import time
from fastapi import APIRouter, HTTPException, status, Request, Depends
from app.models.schemas import ChatRequest, ChatResponse, Timings

# ⭐️ التغيير الرئيسي: استيراد النسخ المشتركة (Singletons) من مكان تعريفها المركزي
from app.core.services import search_service_instance, llm_service_instance
from app.services.security_service import get_api_key
from app.core.limiter import limiter
from app.core.config import settings

router = APIRouter()

# ⭐️ استخدام الأسماء المشتركة محلياً لسهولة القراءة (كما طلب في الإصلاح)
search_service = search_service_instance
llm_service = llm_service_instance

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("100/minute") # الحد: 5 طلبات في الدقيقة لكل مفتاح
async def chat_with_kb(
    request: Request,
    chat_req: ChatRequest,
    api_key: str = Depends(get_api_key) # فرض الأمان
):
    """
    يعالج طلبات الدردشة RAG (استرجاع-توليد معزز)، ويقوم بالبحث، والتوليد،
    وتطبيق الـ Guardrails، وتسجيل المقاييس، وقياس الأداء.
    """
    
    # 1. زيادة عداد الطلبات
    settings.METRICS["total_requests"] += 1
    
    start_total = time.perf_counter()
    retrieval_ms = 0.0
    llm_ms = 0.0
    
    try:
        # --- Phase 1: Retrieval (البحث) ---
        t0 = time.perf_counter()
        try:
            # استخدام search_service المشترك
            results = search_service.search(chat_req.query, chat_req.kb_id, top_k=3)
        except Exception as e:
            settings.METRICS["search_errors"] += 1
            # رفع خطأ HTTP بدلاً من الفشل الصامت
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search Service Failed: {str(e)}")
        retrieval_ms = (time.perf_counter() - t0) * 1000

        # --- Phase 2: Guardrail (الحماية) ---
        # التحقق من أن النتيجة الأولى ذات جودة كافية
        if not results or results[0].get("score", 0) <= 0:
            settings.METRICS["rejected_responses"] += 1
            total_ms = (time.perf_counter() - start_total) * 1000
            return ChatResponse(
                answer="I don't have enough information in the knowledge base.",
                context_used=[],
                status="rejected",
                reason="low_confidence",
                # استخدام Timings مع تقريب ضمني
                timings=Timings(total_ms=total_ms, retrieval_ms=retrieval_ms, llm_ms=0.0)
            )
        
        # --- Phase 3: Generation (التوليد LLM) ---
        t1 = time.perf_counter()
        # استخدام llm_service المشترك
        answer = await llm_service.generate_answer(chat_req.query, results)
        llm_ms = (time.perf_counter() - t1) * 1000
        
        # --- Phase 4: Fallback Check (تحقق من فشل LLM) ---
        if not answer or "Error" in answer:
             settings.METRICS["llm_errors"] += 1
             raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM Service Unavailable")

        # --- Phase 5: Success Response ---
        settings.METRICS["successful_responses"] += 1
        total_ms = (time.perf_counter() - start_total) * 1000

        return ChatResponse(
            answer=answer,
            context_used=results,
            status="success",
            timings=Timings(
                total_ms=round(total_ms, 2),
                retrieval_ms=round(retrieval_ms, 2),
                llm_ms=round(llm_ms, 2)
            )
        )

    except HTTPException as he:
        # إعادة رفع استثناءات HTTP المرفوعة عمداً
        raise he
    except Exception as e:
        # معالجة أي خطأ عام غير متوقع
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Internal Error: {str(e)}"
        )
    
    