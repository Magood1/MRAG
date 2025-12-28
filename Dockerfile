# Stage 1: Builder (تجميع الاعتماديات)
FROM python:3.10-slim as builder

WORKDIR /app

# منع بايثون من كتابة ملفات pyc وتفعيل التخزين المؤقت
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تثبيت أدوات النظام اللازمة للبناء (إن وجدت)
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# إنشاء بيئة افتراضية
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# تثبيت الاعتماديات
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime (الصورة النهائية الخفيفة)
FROM python:3.10-slim

WORKDIR /app

# إنشاء مستخدم غير جذري (Security Best Practice)
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

# نسخ البيئة الافتراضية من المرحلة السابقة
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# نسخ كود التطبيق
COPY ./app /app/app

# تغيير الملكية للمستخدم الآمن
RUN chown -R appuser:appgroup /app

# التبديل للمستخدم الآمن
USER appuser

# المنفذ الذي سيعمل عليه التطبيق
EXPOSE 8000

# أمر التشغيل
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

