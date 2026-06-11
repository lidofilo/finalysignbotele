import os
import psycopg2
from psycopg2 import extras
import pandas as pd
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 🛠️ تفعيل وإعداد الـ logger ليتم استيراده في main.py بدون مشاكل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# بيانات الاتصال بـ PostgreSQL 
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "password")
DB_PORT = os.getenv("DB_PORT", "5432")

class FinalySignService:
    @staticmethod
    def get_db_connection():
        """دالة مركزية لإنشاء الاتصال بسيرفر PostgreSQL"""
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )

    @staticmethod
    def init_db():
        """تهيئة الجدول بنظام PostgreSQL"""
        conn = FinalySignService.get_db_connection()
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS potential_clients (
                    id SERIAL PRIMARY KEY, 
                    name TEXT, 
                    company_name TEXT, 
                    industry TEXT, 
                    phone TEXT, 
                    date DATE DEFAULT CURRENT_DATE
                )
            ''')
        conn.commit()
        conn.close()

    @staticmethod
    def save_lead(data: dict):
        """حفظ العميل في PostgreSQL"""
        conn = FinalySignService.get_db_connection()
        with conn.cursor() as cur:
            query = "INSERT INTO potential_clients (name, company_name, industry, phone, date) VALUES (%s, %s, %s, %s, %s)"
            values = (data['name'], data['company_name'], data['industry'], data['phone'], datetime.now().date())
            cur.execute(query, values)
        conn.commit()
        conn.close()

    @staticmethod
    def get_ai_reply(text: str):
        """دالة مؤقتة للرد الذكي - يمكنك ربط مكتبة Groq هنا لاحقاً"""
        return f"مرحباً بك، تم استلام رسالتك: *{text}*.\n جارٍ ربط نظام Groq AI الذكي..."

# دالة التقرير اليومي
async def send_daily_report(application):
    conn = FinalySignService.get_db_connection()
    df = pd.read_sql_query("SELECT * FROM potential_clients WHERE date = CURRENT_DATE", conn)
    conn.close()
    
    if df.empty: return

    file_path = f"FinalySign_Leads_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    df.to_excel(file_path, index=False)
