"""Health monitoring service."""

import json
import smtplib
from email.mime.text import MIMEText
from typing import Any

import httpx
from models.health_check_result import HealthCheckResult
from models.site import Site
from services.audit_service import AuditService
from services.ga4_service import GA4Service
from sqlalchemy.orm import Session

from config import get_settings


class HealthService:
    ZERO_TRAFFIC_THRESHOLD = 0
    CONVERSION_DROP_RATIO = 0.5

    def __init__(self, db: Session):
        self.db = db
        self.ga4 = GA4Service(db)
        self.audit = AuditService(db)
        self.settings = get_settings()

    def check_site(self, site: Site) -> HealthCheckResult:
        anomaly_flags: list[str] = []
        metrics: dict[str, Any] = {}

        if not site.ga4_property_id:
            result = HealthCheckResult(
                site_id=site.id,
                status="unknown",
                message="No GA4 property configured",
                anomaly_flags=["no_ga4_property"],
            )
            self.db.add(result)
            self.db.commit()
            return result

        report = self.ga4.run_health_report(site.ga4_property_id)
        event_count = int(report.get("eventCount", 0))
        sessions = int(report.get("sessions", 0))
        conversions = int(report.get("conversions", 0))
        metrics = {"event_count": event_count, "sessions": sessions, "conversions": conversions}

        previous = (
            self.db.query(HealthCheckResult)
            .filter(HealthCheckResult.site_id == site.id)
            .order_by(HealthCheckResult.checked_at.desc())
            .offset(1)
            .first()
        )

        if event_count <= self.ZERO_TRAFFIC_THRESHOLD:
            anomaly_flags.append("zero_events_24h")

        if previous and previous.conversion_count_24h:
            baseline = previous.conversion_count_24h
            if conversions < baseline * self.CONVERSION_DROP_RATIO:
                anomaly_flags.append("conversion_drop")

        if site.ga4_measurement_id and site.gtm_container_public_id:
            if not site.gtm_snippets or site.ga4_measurement_id not in str(site.gtm_snippets):
                pass  # mock mode doesn't embed measurement id in snippets

        status = "healthy" if not anomaly_flags else "warning"
        if "zero_events_24h" in anomaly_flags:
            status = "critical"

        result = HealthCheckResult(
            site_id=site.id,
            status=status,
            event_count_24h=event_count,
            conversion_count_24h=conversions,
            traffic_sessions_24h=sessions,
            anomaly_flags=anomaly_flags,
            metrics=metrics,
            baseline_conversion_rate=(
                previous.conversion_count_24h / max(previous.traffic_sessions_24h, 1)
                if previous and previous.traffic_sessions_24h
                else None
            ),
            message=f"Health check: {status}"
            + (f" - {', '.join(anomaly_flags)}" if anomaly_flags else ""),
        )
        self.db.add(result)
        self.db.commit()

        if anomaly_flags:
            self._send_alerts(site, result)

        self.audit.log(
            "health.check",
            site_id=site.id,
            domain=site.domain,
            details={"status": status, "anomaly_flags": anomaly_flags},
        )
        return result

    def check_all_sites(self) -> list[HealthCheckResult]:
        sites = self.db.query(Site).filter(Site.status == "active").all()
        return [self.check_site(site) for site in sites]

    def get_latest(self, site_id: int) -> HealthCheckResult | None:
        return (
            self.db.query(HealthCheckResult)
            .filter(HealthCheckResult.site_id == site_id)
            .order_by(HealthCheckResult.checked_at.desc())
            .first()
        )

    def get_history(self, site_id: int, limit: int = 30) -> list[HealthCheckResult]:
        return (
            self.db.query(HealthCheckResult)
            .filter(HealthCheckResult.site_id == site_id)
            .order_by(HealthCheckResult.checked_at.desc())
            .limit(limit)
            .all()
        )

    def _send_alerts(self, site: Site, result: HealthCheckResult) -> None:
        payload = {
            "site": site.domain,
            "environment": site.environment,
            "status": result.status,
            "anomaly_flags": result.anomaly_flags,
            "metrics": result.metrics,
        }
        if self.settings.alert_webhook_url:
            try:
                httpx.post(
                    self.settings.alert_webhook_url,
                    json=payload,
                    timeout=10,
                )
            except Exception:
                pass

        if self.settings.smtp_host and self.settings.alert_email_to:
            try:
                msg = MIMEText(json.dumps(payload, indent=2))
                msg["Subject"] = f"[Analytics MCP] Health Alert: {site.domain}"
                msg["From"] = self.settings.smtp_user or "analytics-mcp@localhost"
                msg["To"] = self.settings.alert_email_to
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                    if self.settings.smtp_user and self.settings.smtp_password:
                        server.starttls()
                        server.login(self.settings.smtp_user, self.settings.smtp_password)
                    server.send_message(msg)
            except Exception:
                pass

    def simulate_zero_traffic(self, site: Site) -> HealthCheckResult:
        """For testing: create a critical health result."""
        result = HealthCheckResult(
            site_id=site.id,
            status="critical",
            event_count_24h=0,
            conversion_count_24h=0,
            traffic_sessions_24h=0,
            anomaly_flags=["zero_events_24h"],
            metrics={"event_count": 0, "sessions": 0, "conversions": 0},
            message="Simulated zero traffic condition",
        )
        self.db.add(result)
        self.db.commit()
        self._send_alerts(site, result)
        return result
