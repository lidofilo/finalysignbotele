import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MY_CHAT_ID = os.getenv("MY_CHAT_ID", "").strip()

DB_NAME = "FinalySign_Leads.db"
MODEL_NAME = "llama-3.3-70b-versatile"

# مراحل المحادثة
NAME, COMPANY, INDUSTRY, PHONE = range(4)