from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# مفتاح صالح (يجب أن يطابق أحد المفاتيح في app/services/security_service.py)
VALID_HEADERS = {"X-API-Key": "secret-key-123"}

def test_health_check():
    """Ensure the health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data

def test_upload_document():
    """Test uploading a text file."""
    file_content = b"This is a test document."
    response = client.post(
        "/api/v1/kb/test-kb/upload",
        files={"file": ("test.txt", file_content, "text/plain")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"

def test_search_functionality():
    """Upload and verify search."""
    kb_id = "search-test-kb"
    content = b"The secret code is 998877."
    
    # Upload
    client.post(
        f"/api/v1/kb/{kb_id}/upload",
        files={"file": ("secret.txt", content, "text/plain")}
    )
    
    # Search (قد لا يتطلب مفتاحًا حسب تنفيذنا الحالي لنقطة البحث، لكن الدردشة تتطلب)
    response = client.get(f"/api/v1/kb/{kb_id}/search?query=secret")
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) > 0
    assert "998877" in results[0]["text"]

def test_guardrail_rejection():
    """Ensure system rejects questions with no relevant context."""
    kb_id = "guardrail-test"
    
    # 1. Upload irrelevant content
    client.post(
        f"/api/v1/kb/{kb_id}/upload", 
        files={"file": ("doc.txt", b"Apples are red.", "text/plain")}
    )
    
    # 2. Ask unrelated question WITH AUTH HEADERS
    response = client.post(
        "/api/v1/assistant/chat", 
        json={"kb_id": kb_id, "query": "What is the capital of Mars?"},
        headers=VALID_HEADERS  # ✨ التعديل الحاسم: إرسال المفتاح
    )
    
    # الآن نتوقع 200 لأننا مصرح لنا بالدخول، ولكن حالة الرد ستكون rejected
    assert response.status_code == 200
    data = response.json()
    
    # التحقق من منطق الرفض
    assert data["status"] == "rejected"
    assert data["reason"] == "low_confidence"
    assert "I don't have enough information" in data["answer"]

def test_chat_success_flow():
    """Test a successful chat flow."""
    kb_id = "success-chat-test"
    content = b"The policy for remote work allows 2 days per week."
    
    # Upload
    client.post(
        f"/api/v1/kb/{kb_id}/upload",
        files={"file": ("policy.txt", content, "text/plain")}
    )
    
    # Chat WITH AUTH HEADERS
    response = client.post(
        "/api/v1/assistant/chat",
        json={"kb_id": kb_id, "query": "remote work policy"},
        headers=VALID_HEADERS # ✨ إرسال المفتاح
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # التحقق من النجاح والمقاييس
    assert data["status"] == "success"
    assert data["answer"] is not None
    # التأكد من وجود بيانات التوقيت (المراقبة)
    assert "timings" in data
    assert data["timings"]["total_ms"] > 0

    