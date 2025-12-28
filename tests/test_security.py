from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_missing_api_key():
    """Test rejection when API key is missing."""
    response = client.post(
        "/api/v1/assistant/chat",
        json={"kb_id": "test", "query": "hello"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid or missing API Key" # أو الرسالة التي حددتها

def test_invalid_api_key():
    """Test rejection when API key is invalid."""
    response = client.post(
        "/api/v1/assistant/chat",
        json={"kb_id": "test", "query": "hello"},
        headers={"X-API-Key": "hacker-key"}
    )
    assert response.status_code == 403
    assert "Invalid" in response.json()["detail"]

def test_health_check_public():
    """Health check should be public (no key required)."""
    response = client.get("/health")
    assert response.status_code == 200

    