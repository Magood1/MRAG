from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

def get_rate_limit_key(request: Request):
    """
    يحدد هوية العميل لغرض تحديد المعدل.
    الأولوية لمفتاح API، وإذا لم يوجد نعود لعنوان IP.
    """
    return request.headers.get("X-API-Key", get_remote_address(request))

# ✨ استخدام الدالة الجديدة بدلاً من IP فقط
limiter = Limiter(key_func=get_rate_limit_key)
