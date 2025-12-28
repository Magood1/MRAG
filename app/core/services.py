# app/core/services.py
from app.services.search_service import MockSearchService
from app.services.llm_service import GeminiLLMService

# ✨ إنشاء نسخ واحدة (Singletons) ليتم مشاركتها عبر التطبيق بالكامل
search_service_instance = MockSearchService()
llm_service_instance = GeminiLLMService()
