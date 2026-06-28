"""Health API routes."""

from database import SessionLocal
from fastapi import APIRouter
from observability.logging import get_metrics
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    db_status = "ok"
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        db_status = "unavailable"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "service": "analytics-mcp",
    }


@router.get("/metrics")
def metrics() -> dict:
    return get_metrics()
