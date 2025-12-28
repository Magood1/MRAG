import os
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
# مكتبات تحديد المعدل
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
# مكتبة مراقبة Azure
from opencensus.ext.azure.log_exporter import AzureLogHandler

from app.core.config import settings
from app.api.router import api_router
from app.core.limiter import limiter

# --- 1. إعدادات التسجيل والمراقبة (Logging & Observability) ---
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("mrag_service")

# ✨ تكامل Azure Application Insights
# إذا وجدنا سلسلة الاتصال (يتم حقنها تلقائيًا في Azure Web App)، نضيف معالج السجلات
APPINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if APPINSIGHTS_CONNECTION_STRING:
    try:
        azure_handler = AzureLogHandler(connection_string=APPINSIGHTS_CONNECTION_STRING)
        logger.addHandler(azure_handler)
        logger.info("✅ Attached Azure Application Insights Logger")
    except Exception as e:
        logger.error(f"❌ Failed to attach Azure Insights: {e}")

# --- 2. تهيئة تطبيق FastAPI ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.3.0", # ترقية الإصدار لـ Sprint 3
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None, # إخفاء التوثيق في الإنتاج للأمان
    redoc_url=None
)

# --- 3. تسجيل البرمجيات الوسيطة والأدوات (Middleware & Tools) ---

# تسجيل Limiter لحماية API
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware لإضافة Request ID لكل طلب (للتتبع)
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

# ✨ Global Exception Handler (شبكة الأمان الأخيرة)
# يضمن أن أي خطأ غير متوقع يعود كـ JSON نظيف ولا يكشف تفاصيل الخادم
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"🔥 Unhandled Exception (ID: {request_id}): {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error", 
            "request_id": request_id
        }
    )

# --- 4. نقاط النهاية (Endpoints) ---

@app.get("/health", tags=["Monitoring"])
def health_check():
    """
    نقطة فحص الصحة: تعرض حالة النظام، البيئة، والعدادات الحية.
    تستخدمها Azure للتحقق من أن التطبيق يعمل.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "version": "0.3.0",
        "metrics": settings.METRICS # ✨ عرض العدادات الحية (بما في ذلك التوكنات)
    }

# تضمين الموجهات (Routers)
app.include_router(api_router, prefix="/api/v1")

