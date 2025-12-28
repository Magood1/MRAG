import pytest
from app.services.ingestion_service import IngestionService

def test_pii_redaction():
    service = IngestionService()
    text = "Contact me at test@example.com or 123-456-7890."
    cleaned = service._clean_pii(text)
    
    assert "test@example.com" not in cleaned
    assert "[EMAIL_REDACTED]" in cleaned
    assert "123-456-7890" not in cleaned
    assert "[PHONE_REDACTED]" in cleaned

def test_chunking():
    service = IngestionService()
    text = "word " * 600 # Text longer than chunk size (500)
    chunks = service._create_chunks(text)
    
    assert len(chunks) > 1
    # Check overlap logic roughly
    assert len(chunks[0].split()) == 500

    