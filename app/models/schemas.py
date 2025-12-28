from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# --- نماذج الطلب ---
class ChatRequest(BaseModel):
    kb_id: str
    query: str

# --- نماذج المراقبة ---
class Timings(BaseModel):
    total_ms: float
    retrieval_ms: float
    llm_ms: float

# --- نماذج الاستجابة ---
class ChatResponse(BaseModel):
    answer: str
    context_used: List[Dict[str, Any]]
    status: str = "success"
    reason: Optional[str] = None
    timings: Optional[Timings] = None

    