import os
import psycopg2
from psycopg2 import extras
import pandas as pd
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# بيانات الاتصال بـ PostgreSQL (من السيرفر الجديد سواء كان Hetzner أو Oracle)
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
        """تهيئة الجدول بنظام PostgreSQL (Serial بدلاً من Autoincrement)"""
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

# دالة التقرير اليومي (تعديل بسيط لقراءة PostgreSQL)
async def send_daily_report(application):
    conn = FinalySignService.get_db_connection()
    df = pd.read_sql_query("SELECT * FROM potential_clients WHERE date = CURRENT_DATE", conn)
    conn.close()
    
    if df.empty: return

    file_path = f"FinalySign_Leads_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    df.to_excel(file_path, index=False)
    # ... كود الإرسال عبر البوت (كما هو سابقاً) ...