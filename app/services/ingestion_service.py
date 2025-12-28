import re
from typing import List
from fastapi import UploadFile

class IngestionService:
    def __init__(self):
        self.chunk_size = 500
        self.chunk_overlap = 50

    async def process_file(self, file: UploadFile) -> List[str]:
        """Reads, cleans, and chunks the uploaded file."""
        content = await file.read()
        text = content.decode("utf-8")
        
        # 1. PII Cleaning (Simple Regex for Emails & Phones)
        text = self._clean_pii(text)
        
        # 2. Chunking
        chunks = self._create_chunks(text)
        return chunks

    def _clean_pii(self, text: str) -> str:
        # Remove Emails
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
        # Remove Phone Numbers (Simple pattern)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', text)
        return text

    def _create_chunks(self, text: str) -> List[str]:
        # Simple split by words for now
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk)
        return chunks
    
    