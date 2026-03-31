# استخدام نسخة بايثون خفيفة ومستقرة
FROM python:3.11-slim

# منع بايثون من كتابة ملفات pyc وتفعيل الطباعة الفورية للسجلات (Logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# تثبيت التبعيات الضرورية للنظام (إذا لزم الأمر)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات أولاً لتسريع عملية البناء (Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# تشغيل البوت
CMD ["python", "main.py"]