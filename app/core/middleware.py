# app/core/middleware.py
import time
import logging
from fastapi import Request

logger = logging.getLogger("mrag_service")

async def monitoring_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    
    response = await call_next(request)
    
    process_time = time.perf_counter() - start_time
    
    # Structured Log
    log_data = {
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "process_time_ms": round(process_time * 1000, 2),
        "request_id": response.headers.get("X-Request-ID", "unknown")
    }
    
    logger.info(f"Request processed: {log_data}")
    
    # إضافة الزمن في الترويسة (مفيد للتصحيح)
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
