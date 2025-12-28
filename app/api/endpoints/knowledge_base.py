from fastapi import APIRouter, UploadFile, File, HTTPException, status
# ⭐️ التغيير الرئيسي: استيراد النسخة المشتركة من SearchService
# تم إزالة الاستيراد المباشر لـ MockSearchService
from app.core.services import search_service_instance as search_service
from app.services.ingestion_service import IngestionService

# تعريف المتغيرات العامة والثوابت (يفضل أن تكون في ملف config.py)
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB

# تعريف الـ Router
router = APIRouter()
ingestion_service = IngestionService()

# ⚠️ تم إزالة الـ Mock Store المؤقت (knowledge_base_store) من الـ Router،
# الآن يتم الاعتماد على search_service فقط للتخزين والفهرسة.

@router.post("/{kb_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(kb_id: str, file: UploadFile = File(...)):
    """
    يقوم برفع ومعالجة مستند نصي وفهرسته في قاعدة المعرفة المحددة.
    """
    
    # 1. Validation (File Type)
    if file.content_type != "text/plain":
        raise HTTPException(status_code=400, detail="Only .txt files are supported for now.")
    
    
    # 2. Validation (File Size)
    # نستخدم الثابت المعرف في أعلى الملف
    if file.size and file.size > MAX_FILE_SIZE:
         raise HTTPException(status_code=413, detail=f"File too large. Max size is {MAX_FILE_SIZE / (1024*1024):.0f}MB.")
    
    # 3. Processing and Indexing
    try:
        chunks = await ingestion_service.process_file(file)
        
        # استخدام الخدمة المشتركة لفهرسة المستندات
        search_service.add_documents(kb_id, chunks)
        
        # 4. Success Response
        return {
            "status": "success",
            "chunks_processed": len(chunks),
            "message": "Document processed and indexed."
        }
    except Exception as e:
        # معالجة الأخطاء
        # يمكن تحسين هذه المعالجة لتحديد نوع الخطأ بشكل أدق (مثل أخطاء التخزين)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An internal error occurred during processing: {str(e)}"
        )
    

@router.get("/{kb_id}/search")
def search_kb(kb_id: str, query: str, k: int = 3):
    """
    يجري بحثاً في قاعدة المعرفة المحددة ويعيد أفضل النتائج.
    """
    results = search_service.search(query, kb_id, k)
    return {"results": results}