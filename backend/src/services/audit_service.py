"""Audit logging service."""

from sqlalchemy.orm import Session

from models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        operation: str,
        *,
        site_id: int | None = None,
        domain: str | None = None,
        actor: str = "system",
        actor_type: str = "system",
        details: dict | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        status: str = "success",
        message: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            site_id=site_id,
            domain=domain,
            operation=operation,
            actor=actor,
            actor_type=actor_type,
            details=details,
            old_value=old_value,
            new_value=new_value,
            status=status,
            message=message,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_logs(
        self,
        *,
        site_id: int | None = None,
        domain: str | None = None,
        operation: str | None = None,
        actor: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        query = self.db.query(AuditLog).order_by(AuditLog.created_at.desc())
        if site_id:
            query = query.filter(AuditLog.site_id == site_id)
        if domain:
            query = query.filter(AuditLog.domain == domain)
        if operation:
            query = query.filter(AuditLog.operation == operation)
        if actor:
            query = query.filter(AuditLog.actor == actor)
        return query.limit(limit).all()
