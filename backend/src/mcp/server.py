"""FastMCP server with analytics tools."""

from typing import Any

from fastmcp import FastMCP
from sqlalchemy.orm import Session

from database import SessionLocal
from observability.logging import increment_metric
from services.audit_service import AuditService
from services.blueprint_service import BlueprintService
from services.health_service import HealthService
from services.site_service import SiteService

mcp = FastMCP("Analytics MCP")


def _get_db() -> Session:
    return SessionLocal()


def _log_mcp(operation: str, domain: str | None = None, details: dict | None = None) -> None:
    db = _get_db()
    try:
        audit = AuditService(db)
        audit.log(
            f"mcp.{operation}",
            domain=domain,
            actor="mcp",
            actor_type="mcp",
            details=details,
        )
        increment_metric("mcp_invocations")
    finally:
        db.close()


@mcp.tool()
def create_analytics_setup(
    domain: str,
    name: str,
    environment: str = "prod",
    blueprint: str = "saas",
    consent: str = "none",
    enable_bigquery: bool = False,
    bigquery_project: str | None = None,
    bigquery_dataset: str | None = None,
    primary_domain: str | None = None,
    linked_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Create a full GA4 + GTM analytics setup for a domain."""
    db = _get_db()
    try:
        service = SiteService(db)
        result = service.create_site(
            domain=domain,
            name=name,
            environment=environment,
            blueprint=blueprint,
            consent_preset=consent,
            enable_bigquery=enable_bigquery,
            bigquery_project=bigquery_project,
            bigquery_dataset=bigquery_dataset,
            primary_domain=primary_domain,
            linked_domains=linked_domains or [],
            actor="mcp",
            actor_type="mcp",
        )
        _log_mcp("create_analytics_setup", domain, {"environment": environment, "blueprint": blueprint})
        return result
    finally:
        db.close()


@mcp.tool()
def get_analytics_status(domain: str, environment: str = "prod") -> dict[str, Any]:
    """Get GA4/GTM status and health for a site."""
    db = _get_db()
    try:
        service = SiteService(db)
        status = service.get_status(domain, environment)
        health = HealthService(db)
        site = service.get_by_domain(domain, environment)
        latest = health.get_latest(site.id) if site else None
        if latest:
            status["health"] = {
                "status": latest.status,
                "anomaly_flags": latest.anomaly_flags,
            }
        _log_mcp("get_analytics_status", domain)
        return status
    finally:
        db.close()


@mcp.tool()
def apply_tracking_blueprint(domain: str, blueprint: str, environment: str = "prod") -> dict[str, Any]:
    """Apply a tracking blueprint to an existing site."""
    db = _get_db()
    try:
        site_service = SiteService(db)
        site = site_service.get_by_domain(domain, environment)
        if not site:
            return {"error": f"Site '{domain}' not found"}
        blueprint_service = BlueprintService(db)
        result = blueprint_service.apply(site, blueprint, actor="mcp", actor_type="mcp")
        _log_mcp("apply_tracking_blueprint", domain, {"blueprint": blueprint})
        return result
    finally:
        db.close()


@mcp.tool()
def describe_analytics_setup(domain: str, environment: str = "prod") -> dict[str, Any]:
    """Get a human-readable description of the analytics setup."""
    db = _get_db()
    try:
        service = SiteService(db)
        result = service.describe_setup(domain, environment)
        _log_mcp("describe_analytics_setup", domain)
        return result
    finally:
        db.close()


@mcp.tool()
def get_health_status(domain: str, environment: str = "prod") -> dict[str, Any]:
    """Get health metrics and anomaly flags for a site."""
    db = _get_db()
    try:
        site_service = SiteService(db)
        site = site_service.get_by_domain(domain, environment)
        if not site:
            return {"error": f"Site '{domain}' not found"}
        health = HealthService(db)
        result = health.check_site(site)
        _log_mcp("get_health_status", domain)
        return {
            "domain": domain,
            "status": result.status,
            "event_count_24h": result.event_count_24h,
            "conversion_count_24h": result.conversion_count_24h,
            "traffic_sessions_24h": result.traffic_sessions_24h,
            "anomaly_flags": result.anomaly_flags,
            "metrics": result.metrics,
        }
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()
