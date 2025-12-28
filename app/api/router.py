from fastapi import APIRouter
from app.api.endpoints import knowledge_base, assistant

api_router = APIRouter()

api_router.include_router(knowledge_base.router, prefix="/kb", tags=["Knowledge Base"])

api_router.include_router(assistant.router, prefix="/assistant", tags=["Assistant"])