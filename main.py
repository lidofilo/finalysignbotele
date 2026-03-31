import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# استيراد الإعدادات والخدمات من الملف المنفصل
from services import (
    FinalySignService, 
    send_daily_report, 
    TELEGRAM_TOKEN, 
    logger
)

# --- 1. إعدادات الثوابت للمحادثة ---
NAME, COMPANY, INDUSTRY, PHONE = range(4)
service = FinalySignService()

# --- 2. إعدادات البداية والجدولة (POST_INIT) ---
async def post_init_setup(application):
    """تهيئة أزرار القائمة الرسمية والمجدول الزمني"""
    # ضبط أزرار القائمة (Menu Buttons) كما في الصورة التي أرفقتها
    commands = [
        BotCommand("start", "العودة للقائمة الرئيسية"),
        BotCommand("consult", "طلب استشارة فنية"),
        BotCommand("about", "تعرف على FinalySign"),
        BotCommand("help", "الدعم الفني وتحدث لموظف")
    ]
    await application.bot.set_my_commands(commands)

    # تشغيل المجدول للتقرير اليومي (الساعة 9 صباحاً)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_report, 'cron', hour=9, minute=0, args=[application])
    scheduler.start()
    
    logger.info("✅ تم ضبط القائمة والمجدول بنجاح.")

# --- 3. دوال المعالجة (Handlers Logic) ---

def get_main_keyboard():
    """لوحة الأزرار الرئيسية أسفل الكيبورد"""
    return ReplyKeyboardMarkup([
        ['🌐 خدماتنا التقنية', '📞 طلب استشارة'],
        ['💬 التحدث لموظف', '📝 عن FinalySign']
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    await update.message.reply_text(
        "أهلاً بك في FinalySign! ✨ شريكك التقني للتحول الرقمي.\n"
        "يمكنك استخدام القائمة بالأسفل أو كتابة استفسارك مباشرة.",
        reply_markup=get_main_keyboard()
    )

# --- 4. منطق جمع بيانات العميل (Conversation Flow) ---

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "يسعدنا خدمتك في FinalySign! 🤝\nلنبدأ بتسجيل طلبك، ما هو اسمك الكريم؟", 
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text(f"أهلاً بك أستاذ {update.message.text}. ما هو اسم شركتك؟")
    return COMPANY

async def get_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['company_name'] = update.message.text
    await update.message.reply_text("في أي مجال تخصص الشركة؟")
    return INDUSTRY

async def get_industry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['industry'] = update.message.text
    await update.message.reply_text("أخيراً، يرجى إرسال رقم الهاتف للتواصل معك:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    # حفظ البيانات في قاعدة البيانات عبر الخدمة المنفصلة
    service.save_lead(context.user_data)
    
    await update.message.reply_text(
        "✅ تم تسجيل بياناتك بنجاح! سيتم التواصل معك خلال 24 ساعة.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء الطلب.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

# --- 5. الرد الذكي بالذكاء الاصطناعي ---

async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # خيارات سريعة للأزرار العادية
    text = update.message.text
    if text == '📝 عن FinalySign':
        await update.message.reply_text("FinalySign: مؤسسة متخصصة في البرمجة والتصميم والتحول الرقمي.")
        return
    elif text == '💬 التحدث لموظف':
        await update.message.reply_text("سيتم تحويل رسالتك للمختص، يرجى توضيح استفسارك.")
        return

    # الرد عبر Groq
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = service.get_ai_reply(text)
    await update.message.reply_text(reply, parse_mode='Markdown')

# --- 6. تشغيل المحرك (Main Engine) ---

if __name__ == '__main__':
    # تهيئة قاعدة البيانات عند الانطلاق
    service.init_db()

    # بناء التطبيق وربط دالة الـ post_init
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init_setup).build()

    # تعريف نظام المحادثة (Conversation Handler)
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^📞 طلب استشارة$'), ask_name),
            CommandHandler("consult", ask_name) # ربط زر المنيو أيضاً
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_company)],
            INDUSTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_industry)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # إضافة كافة الـ Handlers بالترتيب الصحيح
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", lambda u, c: u.message.reply_text("FinalySign: خبراء البرمجيات والتصميم.")))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ai_chat))

    # انطلاق البوت
    print("🚀 FinalySign Bot is LIVE & Organized...")
    app.run_polling()