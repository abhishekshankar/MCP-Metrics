"""API authentication middleware."""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_role(api_key: str | None = Security(api_key_header)) -> str:
    settings = get_settings()
    if not api_key:
        return "anonymous"
    if api_key == settings.admin_api_key:
        return "admin"
    if api_key == settings.readonly_api_key:
        return "readonly"
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def require_admin(role: str = Depends(get_api_role)) -> str:
    if role not in ("admin", "anonymous"):
        if role == "readonly":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    if role == "anonymous":
        settings = get_settings()
        if settings.mock_google_apis:
            return "admin"  # allow unauthenticated in mock dev mode
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
    return role


def require_read(role: str = Depends(get_api_role)) -> str:
    if role == "anonymous":
        settings = get_settings()
        if settings.mock_google_apis:
            return "admin"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
    return role
