"""FastMCP server with analytics tools."""

from typing import Any

from fastmcp import FastMCP
from sqlalchemy.orm import Session

from database import SessionLocal
from observability.logging import increment_metric
from services.audit_service import AuditService
from services.blueprint_service import BlueprintService
from services.ga4_data_service import GA4DataService
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


# GA4 Schema Discovery Tools (like surendranb/google-analytics-mcp)

@mcp.tool()
def search_ga4_schema(keyword: str) -> dict[str, Any]:
    """Search for GA4 dimensions and metrics matching a keyword.

    Similar to surendranb/google-analytics-mcp's search_schema tool.
    Finds dimensions and metrics by name or description.

    Args:
        keyword: Search term (e.g., "user", "conversion", "session")

    Returns:
        Matching dimensions and metrics with categories
    """
    service = GA4DataService()
    result = service.search_schema(keyword)
    _log_mcp("search_ga4_schema", None, {"keyword": keyword, "results": len(result["dimensions"]) + len(result["metrics"])})
    return result


@mcp.tool()
def list_dimension_categories() -> dict[str, Any]:
    """List all available GA4 dimension categories."""
    service = GA4DataService()
    categories = service.list_dimension_categories()
    return {"categories": categories}


@mcp.tool()
def list_metric_categories() -> dict[str, Any]:
    """List all available GA4 metric categories."""
    service = GA4DataService()
    categories = service.list_metric_categories()
    return {"categories": categories}


@mcp.tool()
def get_dimensions_by_category(category: str | None = None) -> dict[str, Any]:
    """Get dimensions organized by category.

    Args:
        category: Optional category to filter (e.g., "Time", "Geography", "Event")

    Returns:
        Dimensions grouped by category
    """
    service = GA4DataService()
    return service.get_dimensions_by_category(category)


@mcp.tool()
def get_metrics_by_category(category: str | None = None) -> dict[str, Any]:
    """Get metrics organized by category.

    Args:
        category: Optional category to filter (e.g., "User", "Session", "Conversions")

    Returns:
        Metrics grouped by category
    """
    service = GA4DataService()
    return service.get_metrics_by_category(category)


@mcp.tool()
def query_ga4_data(
    property_id: str,
    dimensions: list[str],
    metrics: list[str],
    start_date: str,
    end_date: str,
    limit: int = 1000,
    estimate_only: bool = False,
) -> dict[str, Any]:
    """Query GA4 data with intelligent defaults and safety features.

    Similar to surendranb/google-analytics-mcp's get_ga4_data tool.
    Includes row estimation and safe defaults to prevent context window overflow.

    Args:
        property_id: GA4 property ID (e.g., "properties/123456789")
        dimensions: List of dimension names (use search_ga4_schema to find valid names)
        metrics: List of metric names
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Maximum rows (default 1000, max 10000)
        estimate_only: If True, only returns row count estimate

    Returns:
        Query results with metadata, or row estimate if estimate_only=True

    Example:
        query_ga4_data(
            property_id="properties/123456789",
            dimensions=["date", "country"],
            metrics=["activeUsers", "sessions"],
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
    """
    service = GA4DataService()
    result = service.query_data(
        property_id=property_id,
        dimensions=dimensions,
        metrics=metrics,
        date_range={"start": start_date, "end": end_date},
        limit=min(limit, 10000),
        estimate_only=estimate_only,
    )
    _log_mcp(
        "query_ga4_data",
        None,
        {
            "property_id": property_id,
            "dimensions": dimensions,
            "metrics": metrics,
            "estimate_only": estimate_only,
        },
    )
    return result


if __name__ == "__main__":
    mcp.run()
