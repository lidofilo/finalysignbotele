import os
import pandas as pd
import logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# 🛠️ تفعيل وإعداد الـ logger ليتم استيراده في main.py بدون مشاكل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# بيانات الاتصال بـ Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# إنشاء عميل الاتصال بـ Supabase
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("❌ خطأ: لم يتم العثور على SUPABASE_URL أو SUPABASE_KEY في المتغيرات!")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class FinalySignService:
    @staticmethod
    def init_db():
        """في Supabase يتم إنشاء الجداول من لوحة التحكم، هذه الدالة فقط للتأكد من الجاهزية"""
        logger.info("✅ تم تهيئة خدمة Supabase بنجاح.")

    @staticmethod
    def save_lead(data: dict):
        """حفظ العميل في جدول potential_clients داخل Supabase"""
        try:
            data_to_insert = {
                "name": data.get('name'),
                "company_name": data.get('company_name'),
                "industry": data.get('industry'),
                "phone": data.get('phone'),
                "date": datetime.now().date().isoformat()  # حفظ التاريخ بصيغة YYYY-MM-DD
            }
            response = supabase.table("potential_clients").insert(data_to_insert).execute()
            logger.info("✅ تم حفظ بيانات العميل بنجاح في Supabase.")
            return response
        except Exception as e:
            logger.error(f"❌ خطأ أثناء حفظ البيانات في Supabase: {e}")

    @staticmethod
    def get_ai_reply(text: str):
        """دالة مؤقتة للرد الذكي - يمكنك ربط مكتبة Groq هنا لاحقاً"""
        return f"مرحباً بك، تم استلام رسالتك: *{text}*.\n جارٍ ربط نظام Groq AI الذكي..."

# دالة التقرير اليومي (معدلة لجلب البيانات من Supabase)
async def send_daily_report(application):
    try:
        today_str = datetime.now().date().isoformat()
        
        # جلب بيانات اليوم فقط من Supabase
        response = supabase.table("potential_clients").select("*").eq("date", today_str).execute()
        
        # التحقق مما إذا كانت هناك بيانات مسترجعة
        if not response.data:
            logger.info("📅 لا توجد بيانات لعملاء جدد اليوم لتصديرها.")
            return

        # تحويل قائمة القواميس (List of Dicts) القادمة من Supabase إلى DataFrame مباشرة
        df = pd.DataFrame(response.data)
        
        # إعادة ترتيب الأعمدة لشكل جمالي (اختياري)
        columns_order = ['id', 'name', 'company_name', 'industry', 'phone', 'date']
        df = df.reindex(columns=columns_order)

        file_path = f"FinalySign_Leads_{today_str}.xlsx"
        df.to_excel(file_path, index=False)
        logger.info(f"📊 تم إنشاء التقرير اليومي بنجاح وصيغته جاهزة للإرسال: {file_path}")
        
        # ... كود الإرسال عبر البوت (كما هو سابقاً في مشروعك) ...
        
    except Exception as e:
        logger.error(f"❌ خطأ أثناء إعداد أو جلب التقرير اليومي من Supabase: {e}")
