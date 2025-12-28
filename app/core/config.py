import os
import logging
from typing import Dict
from pydantic_settings import BaseSettings
# مكتبات Azure للأمان
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# إعداد المسجل المحلي
logger = logging.getLogger("mrag_service")

class Settings(BaseSettings):
    # معلومات المشروع
    PROJECT_NAME: str = "MRAG Service"
    ENVIRONMENT: str = "development"
    
    # الأسرار والمتغيرات البيئية
    # في التطوير: تأتي من ملف .env
    # في الإنتاج: تأتي من Key Vault (باستثناء KEY_VAULT_NAME الذي يُحقن كمتغير بيئة)
    GEMINI_API_KEY: str = "" 
    KEY_VAULT_NAME: str = "" 
    
    # عدادات المراقبة الحية (In-Memory Metrics)
    # يتم تحديثها من قبل الخدمات وعرضها في /health
    METRICS: Dict[str, int] = {
        "total_requests": 0,
        "search_errors": 0,
        "llm_errors": 0,
        "successful_responses": 0,
        "rejected_responses": 0,
        "total_input_tokens": 0,  
        "total_output_tokens": 0,
        "estimated_cost_usd": 0 # (يمكنك إضافة منطق حساب لاحقاً: Tokens * Price)
    }

    def load_secrets_from_keyvault(self):
        """
        محاولة جلب الأسرار الحساسة من Azure Key Vault.
        يعمل هذا فقط إذا كنا في بيئة الإنتاج وتم تحديد اسم الخزنة.
        """
        if self.ENVIRONMENT == "production" and self.KEY_VAULT_NAME:
            try:
                logger.info(f"🔐 Attempting to connect to Key Vault: {self.KEY_VAULT_NAME}...")
                
                # DefaultAzureCredential يستخدم Managed Identity تلقائيًا في Azure
                credential = DefaultAzureCredential()
                vault_url = f"https://{self.KEY_VAULT_NAME}.vault.azure.net/"
                client = SecretClient(vault_url=vault_url, credential=credential)
                
                # جلب مفتاح Gemini (تأكد أن الاسم في Key Vault هو 'GeminiApiKey')
                self.GEMINI_API_KEY = client.get_secret("GeminiApiKey").value
                
                logger.info("✅ Successfully retrieved secrets from Key Vault.")
            except Exception as e:
                # نسجل خطأ فادحًا ولكن لا نوقف التطبيق فورًا (قد يكون هناك Fallback)
                logger.critical(f"❌ Failed to load secrets from Key Vault: {e}")
        else:
            logger.info("ℹ️ Running in Development mode or KEY_VAULT_NAME not set. Using local env vars.")

    class Config:
        env_file = ".env"
        extra = "ignore" # تجاهل أي متغيرات إضافية في البيئة

# إنشاء كائن الإعدادات وتشغيل منطق جلب الأسرار
settings = Settings()
settings.load_secrets_from_keyvault()

