import os
import logging
import sqlite3
import asyncio
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- إعدادات النظام الثابتة ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MY_CHAT_ID = os.getenv("MY_CHAT_ID", "").strip() # يفضل وضعه في .env أيضاً

# إعدادات قاعدة البيانات واسم الموديل
DB_NAME = "FinalySign_Leads.db"
MODEL_NAME = "llama-3.3-70b-versatile"

# مراحل المحادثة
NAME, COMPANY, INDUSTRY, PHONE = range(4)

# إعداد السجلات (Logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- مديول قاعدة البيانات (Database Module) ---
class DatabaseManager:
    @staticmethod
    def init_db():
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS potential_clients 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             name TEXT, company_name TEXT, industry TEXT, phone TEXT, date TEXT)''')
    
    @staticmethod
    def save_lead(data: dict):
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("INSERT INTO potential_clients (name, company_name, industry, phone, date) VALUES (?, ?, ?, ?, ?)",
                         (data['name'], data['company_name'], data['industry'], data['phone'], datetime.now().strftime("%Y-%m-%d")))

# --- مديول التقارير (Reporting Module) ---
async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    """تصدير البيانات لإكسيل وإرسالها للمدير"""
    if not os.path.exists(DB_NAME) or not MY_CHAT_ID:
        return

    df = pd.read_sql_query("SELECT * FROM potential_clients", sqlite3.connect(DB_NAME))
    if df.empty:
        await context.bot.send_message(chat_id=MY_CHAT_ID, text="📢 تقرير FinalySign: لا يوجد عملاء جدد اليوم.")
        return

    file_path = f"FinalySign_Leads_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    df.to_excel(file_path, index=False)

    with open(file_path, 'rb') as doc:
        await context.bot.send_document(chat_id=MY_CHAT_ID, document=doc, caption="📊 تقرير العملاء اليومي")
    os.remove(file_path)

# --- مديول معالجة الرسائل (Handlers Module) ---
class FinalySignBot:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.system_prompt = (
            "أنت المساعد الذكي لشركة FinalySign. خدماتنا: تصميم مواقع، تطبيقات فلاتر، "
            "سوشيال ميديا، وتحليل بيانات. كن احترافياً وشجع على طلب استشارة."
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [['🌐 خدماتنا', '📞 طلب استشارة'], ['💬 موظف مختص', '📝 عن الشركة']]
        await update.message.reply_text(
            "أهلاً بك في FinalySign! ✨\nكيف يمكننا دعم مشروعك اليوم؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    async def ai_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_text = update.message.text
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            chat_completion = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_text}]
            )
            await update.message.reply_text(chat_completion.choices[0].message.content, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"AI Error: {e}")
            await update.message.reply_text("عذراً، تواصل معنا لاحقاً.")

# --- نظام المحادثة لجمع البيانات (Conversation Logic) ---
async def start_consult(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("يسعدنا خدمتك! ما هو اسمك الكريم؟", reply_markup=ReplyKeyboardRemove())
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("ممتاز، ما هو اسم شركتك؟")
    return COMPANY

async def get_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['company_name'] = update.message.text
    await update.message.reply_text("ما هو مجال عمل الشركة؟")
    return INDUSTRY

async def get_industry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['industry'] = update.message.text
    await update.message.reply_text("رقم الهاتف للتواصل:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    DatabaseManager.save_lead(context.user_data)
    
    await update.message.reply_text("✅ شكراً لك! سيتم التواصل معك خلال 24 ساعة.", 
                                    reply_markup=ReplyKeyboardMarkup([['🌐 خدماتنا', '📞 طلب استشارة']], resize_keyboard=True))
    return ConversationHandler.END

# --- التشغيل الرئيسي (Main Execution) ---
if __name__ == '__main__':
    # 1. تهيئة قاعدة البيانات
    DatabaseManager.init_db()
    
    # 2. بناء التطبيق
    bot_logic = FinalySignBot()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 3. إعداد المجدول للتقرير اليومي (9 صباحاً)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_report, 'cron', hour=9, minute=0, args=[app])
    scheduler.start()

    # 4. تعريف الـ Handlers
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📞 طلب استشارة$'), start_consult)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_company)],
            INDUSTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_industry)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("start", bot_logic.start)],
    )

    app.add_handler(CommandHandler("start", bot_logic.start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot_logic.ai_reply))

    print("🚀 FinalySign Bot is running smoothly...")
    app.run_polling()