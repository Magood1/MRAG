from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# قائمة المفاتيح المصرح لها (في الواقع تأتي من قاعدة بيانات أو Key Vault)
VALID_API_KEYS = [
    "secret-key-123",
    "admin-key-xyz",
    "client-a-key"
]

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """يتحقق من صحة مفتاح API الوارد في الترويسة."""
    if api_key_header in VALID_API_KEYS:
        return api_key_header
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid or missing API Key"
    )
