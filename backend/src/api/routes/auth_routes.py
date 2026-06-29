"""Auth management API routes."""

from api.auth import require_admin
from fastapi import APIRouter, Depends

from config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/info")
def auth_info(role: str = Depends(require_admin)):
    settings = get_settings()
    return {
        "roles": ["admin", "readonly"],
        "admin_key_configured": bool(settings.admin_api_key),
        "readonly_key_configured": bool(settings.readonly_api_key),
        "current_role": role,
        "docs": "Pass X-API-Key header with admin or readonly key",
    }
