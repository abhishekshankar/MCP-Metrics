"""Audit log API routes."""

from api.auth import require_read
from database import get_db
from fastapi import APIRouter, Depends, Query
from services.audit_service import AuditService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit_logs(
    domain: str | None = None,
    operation: str | None = None,
    actor: str | None = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    role: str = Depends(require_read),
):
    audit = AuditService(db)
    logs = audit.list_logs(domain=domain, operation=operation, actor=actor, limit=limit)
    return [
        {
            "id": log.id,
            "site_id": log.site_id,
            "domain": log.domain,
            "operation": log.operation,
            "actor": log.actor,
            "actor_type": log.actor_type,
            "status": log.status,
            "details": log.details,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "message": log.message,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
