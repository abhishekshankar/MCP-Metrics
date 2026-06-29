"""FastMCP server with analytics tools."""

from typing import Any

from database import SessionLocal
from fastmcp import FastMCP
from observability.logging import increment_metric
from pydantic import BaseModel, Field, field_validator
from services.audit_service import AuditService
from services.blueprint_service import BlueprintService
from services.ga4_data_service import GA4DataService
from services.health_service import HealthService
from services.site_service import SiteService
from sqlalchemy.orm import Session

mcp = FastMCP("Analytics MCP")


# Validation Models
class DomainRequest(BaseModel):
    """Base model for domain-based requests."""

    domain: str = Field(
        ...,
        min_length=1,
        max_length=253,
        pattern=r"^[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9](\.[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9])*$",
    )
    environment: str = Field(default="prod", pattern=r"^(dev|stage|prod)$")

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        if "." not in v:
            raise ValueError("Domain must contain at least one dot (e.g., example.com)")
        return v.lower()


class CreateSiteRequest(BaseModel):
    """Validation model for create_analytics_setup."""

    domain: str = Field(
        ...,
        min_length=1,
        max_length=253,
        pattern=r"^[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9](\.[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9])*$",
    )
    name: str = Field(..., min_length=1, max_length=100)
    environment: str = Field(default="prod", pattern=r"^(dev|stage|prod)$")
    blueprint: str = Field(default="saas", pattern=r"^(saas|ecommerce|content|none)$")
    consent: str = Field(default="none", pattern=r"^(none|basic|advanced)$")
    enable_bigquery: bool = False
    bigquery_project: str | None = Field(default=None, max_length=100)
    bigquery_dataset: str | None = Field(default=None, max_length=100)
    primary_domain: str | None = None
    linked_domains: list[str] = Field(default_factory=list)

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        if "." not in v:
            raise ValueError("Domain must contain at least one dot")
        return v.lower()

    @field_validator("linked_domains")
    @classmethod
    def validate_linked_domains(cls, v: list[str]) -> list[str]:
        return [d.strip().lower() for d in v if d.strip()]


class GA4QueryRequest(BaseModel):
    """Validation model for query_ga4_data."""

    property_id: str = Field(..., pattern=r"^properties/\d+$")
    dimensions: list[str] = Field(..., min_length=1)
    metrics: list[str] = Field(..., min_length=1)
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    limit: int = Field(default=1000, ge=1, le=10000)
    estimate_only: bool = False

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: str, info) -> str:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be after start_date")
        return v


class BrowserActionRequest(BaseModel):
    """Validation model for browser action."""

    action: str = Field(
        ...,
        pattern=r"^(navigate|click|fill|select|wait|assert_text|assert_visible|assert_url|screenshot|press)$",
    )
    selector: str | None = None
    value: str | None = None
    timeout: int = Field(default=5000, ge=100, le=60000)
    description: str = ""


class BrowserTestRequest(BaseModel):
    """Validation model for run_browser_test."""

    url: str = Field(..., pattern=r"^https?://.+")
    actions: list[dict[str, Any]]
    headless: bool = True
    capture_screenshots: bool = False
    timeout_seconds: int = Field(default=60, ge=10, le=300)


class GTMPreviewRequest(BaseModel):
    """Validation model for browser_gtm_preview_test."""

    url: str = Field(..., pattern=r"^https?://.+")
    container_id: str = Field(..., pattern=r"^GTM-[A-Z0-9]{4,}$")
    preview_id: str = Field(..., min_length=1)
    expected_tags: list[dict[str, str]] | None = None
    headless: bool = True
    timeout_seconds: int = Field(default=60, ge=10, le=300)


class CrawlRequest(BaseModel):
    """Validation model for crawl_website."""

    start_url: str = Field(..., pattern=r"^https?://.+")
    max_pages: int = Field(default=20, ge=1, le=100)
    max_depth: int = Field(default=3, ge=1, le=5)
    headless: bool = True
    crawl_delay_ms: int = Field(default=1000, ge=0, le=5000)


class SiteUIRequest(BaseModel):
    """Validation model for create_site_via_ui."""

    domain: str = Field(
        ...,
        min_length=1,
        max_length=253,
        pattern=r"^[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9](\.[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9])*$",
    )
    name: str = Field(..., min_length=1, max_length=100)
    web_ui_url: str = Field(default="http://localhost:5173", pattern=r"^https?://.+")
    environment: str = Field(default="prod", pattern=r"^(dev|stage|prod)$")
    blueprint: str = Field(default="saas", pattern=r"^(saas|ecommerce|content|none)$")
    headless: bool = True
    timeout_seconds: int = Field(default=120, ge=10, le=300)


class TestAppRequest(BaseModel):
    """Validation model for test_mcp_metrics_app."""

    web_ui_url: str = Field(default="http://localhost:5173", pattern=r"^https?://.+")
    api_url: str = Field(default="http://localhost:8000", pattern=r"^https?://.+")
    headless: bool = True
    timeout_seconds: int = Field(default=60, ge=10, le=300)


class ApplyBlueprintRequest(BaseModel):
    """Validation model for apply_tracking_blueprint."""

    domain: str = Field(..., min_length=1, max_length=253)
    blueprint: str = Field(..., pattern=r"^(saas|ecommerce|content|none)$")
    environment: str = Field(default="prod", pattern=r"^(dev|stage|prod)$")


class SchemaCategoryRequest(BaseModel):
    """Validation model for schema category requests."""

    category: str | None = Field(default=None, min_length=1, max_length=50)


def _get_db() -> Session:
    """Get database session."""
    return SessionLocal()


def _log_mcp(operation: str, domain: str | None = None, details: dict | None = None) -> None:
    """Log MCP operation to audit log."""
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


# Core Site Management Tools (async)


@mcp.tool()
async def create_analytics_setup(
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
    """Create a full GA4 + GTM analytics setup for a domain.

    Args:
        domain: Site domain (e.g., "example.com")
        name: Site name
        environment: Environment (dev/stage/prod)
        blueprint: Blueprint preset (saas/ecommerce/content/none)
        consent: Consent preset (none/basic/advanced)
        enable_bigquery: Enable BigQuery export
        bigquery_project: BigQuery project ID (if enable_bigquery)
        bigquery_dataset: BigQuery dataset (if enable_bigquery)
        primary_domain: Primary domain for cross-domain tracking
        linked_domains: List of linked domains for cross-domain

    Returns:
        Site configuration including GA4 property and GTM container IDs

    Example:
        create_analytics_setup(domain="example.com", name="Example Site", blueprint="ecommerce")
    """
    # Validate inputs
    request = CreateSiteRequest(
        domain=domain,
        name=name,
        environment=environment,
        blueprint=blueprint,
        consent=consent,
        enable_bigquery=enable_bigquery,
        bigquery_project=bigquery_project,
        bigquery_dataset=bigquery_dataset,
        primary_domain=primary_domain,
        linked_domains=linked_domains or [],
    )

    db = _get_db()
    try:
        service = SiteService(db)
        result = service.create_site(
            domain=request.domain,
            name=request.name,
            environment=request.environment,
            blueprint=request.blueprint,
            consent_preset=request.consent,
            enable_bigquery=request.enable_bigquery,
            bigquery_project=request.bigquery_project,
            bigquery_dataset=request.bigquery_dataset,
            primary_domain=request.primary_domain,
            linked_domains=request.linked_domains,
            actor="mcp",
            actor_type="mcp",
        )
        _log_mcp(
            "create_analytics_setup",
            request.domain,
            {
                "environment": request.environment,
                "blueprint": request.blueprint,
            },
        )
        return result
    finally:
        db.close()


@mcp.tool()
async def get_analytics_status(domain: str, environment: str = "prod") -> dict[str, Any]:
    """Get GA4/GTM status and health for a site.

    Args:
        domain: Site domain
        environment: Environment (dev/stage/prod)

    Returns:
        Site status including GA4 property, GTM container, and health metrics
    """
    # Validate inputs
    request = DomainRequest(domain=domain, environment=environment)

    db = _get_db()
    try:
        service = SiteService(db)
        site = service.get_by_domain(request.domain, request.environment)
        if not site:
            raise ValueError(f"Site '{request.domain}' ({request.environment}) not found")

        status = service.get_status(request.domain, request.environment)
        health = HealthService(db)
        latest = health.get_latest(site.id)
        if latest:
            status["health"] = {
                "status": latest.status,
                "anomaly_flags": latest.anomaly_flags,
            }
        _log_mcp("get_analytics_status", request.domain)
        return status
    finally:
        db.close()


@mcp.tool()
async def apply_tracking_blueprint(
    domain: str,
    blueprint: str,
    environment: str = "prod",
) -> dict[str, Any]:
    """Apply a tracking blueprint to an existing site.

    Args:
        domain: Site domain
        blueprint: Blueprint to apply (saas/ecommerce/content/none)
        environment: Environment (dev/stage/prod)

    Returns:
        Blueprint application result
    """
    # Validate inputs
    request = ApplyBlueprintRequest(
        domain=domain,
        blueprint=blueprint,
        environment=environment,
    )

    db = _get_db()
    try:
        site_service = SiteService(db)
        site = site_service.get_by_domain(request.domain, request.environment)
        if not site:
            raise ValueError(f"Site '{request.domain}' ({request.environment}) not found")

        blueprint_service = BlueprintService(db)
        result = blueprint_service.apply(
            site,
            request.blueprint,
            actor="mcp",
            actor_type="mcp",
        )
        _log_mcp("apply_tracking_blueprint", request.domain, {"blueprint": request.blueprint})
        return result
    finally:
        db.close()


@mcp.tool()
async def describe_analytics_setup(domain: str, environment: str = "prod") -> dict[str, Any]:
    """Get a human-readable description of the analytics setup.

    Args:
        domain: Site domain
        environment: Environment (dev/stage/prod)

    Returns:
        Human-readable description of the analytics configuration
    """
    # Validate inputs
    request = DomainRequest(domain=domain, environment=environment)

    db = _get_db()
    try:
        service = SiteService(db)
        result = service.describe_setup(request.domain, request.environment)
        _log_mcp("describe_analytics_setup", request.domain)
        return result
    finally:
        db.close()


@mcp.tool()
async def get_health_status(domain: str, environment: str = "prod") -> dict[str, Any]:
    """Get health metrics and anomaly flags for a site.

    Args:
        domain: Site domain
        environment: Environment (dev/stage/prod)

    Returns:
        Health check results with metrics and anomaly detection
    """
    # Validate inputs
    request = DomainRequest(domain=domain, environment=environment)

    db = _get_db()
    try:
        site_service = SiteService(db)
        site = site_service.get_by_domain(request.domain, request.environment)
        if not site:
            raise ValueError(f"Site '{request.domain}' ({request.environment}) not found")

        health = HealthService(db)
        result = health.check_site(site)
        _log_mcp("get_health_status", request.domain)
        return {
            "domain": request.domain,
            "status": result.status,
            "event_count_24h": result.event_count_24h,
            "conversion_count_24h": result.conversion_count_24h,
            "traffic_sessions_24h": result.traffic_sessions_24h,
            "anomaly_flags": result.anomaly_flags,
            "metrics": result.metrics,
        }
    finally:
        db.close()


# GA4 Schema Discovery Tools (async)


@mcp.tool()
async def search_ga4_schema(keyword: str) -> dict[str, Any]:
    """Search for GA4 dimensions and metrics matching a keyword.

    Similar to surendranb/google-analytics-mcp's search_schema tool.
    Finds dimensions and metrics by name or description.

    Args:
        keyword: Search term (e.g., "user", "conversion", "session")

    Returns:
        Matching dimensions and metrics with categories
    """
    if not keyword or len(keyword) < 2:
        raise ValueError("Keyword must be at least 2 characters")

    service = GA4DataService()
    result = service.search_schema(keyword)
    _log_mcp(
        "search_ga4_schema",
        None,
        {
            "keyword": keyword,
            "results": len(result["dimensions"]) + len(result["metrics"]),
        },
    )
    return result


@mcp.tool()
async def list_dimension_categories() -> dict[str, Any]:
    """List all available GA4 dimension categories."""
    service = GA4DataService()
    categories = service.list_dimension_categories()
    return {"categories": categories}


@mcp.tool()
async def list_metric_categories() -> dict[str, Any]:
    """List all available GA4 metric categories."""
    service = GA4DataService()
    categories = service.list_metric_categories()
    return {"categories": categories}


@mcp.tool()
async def get_dimensions_by_category(category: str | None = None) -> dict[str, Any]:
    """Get dimensions organized by category.

    Args:
        category: Optional category to filter (e.g., "Time", "Geography", "Event")

    Returns:
        Dimensions grouped by category
    """
    request = SchemaCategoryRequest(category=category)
    service = GA4DataService()
    return service.get_dimensions_by_category(request.category)


@mcp.tool()
async def get_metrics_by_category(category: str | None = None) -> dict[str, Any]:
    """Get metrics organized by category.

    Args:
        category: Optional category to filter (e.g., "User", "Session", "Conversions")

    Returns:
        Metrics grouped by category
    """
    request = SchemaCategoryRequest(category=category)
    service = GA4DataService()
    return service.get_metrics_by_category(request.category)


@mcp.tool()
async def query_ga4_data(
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
        dimensions: List of dimension names
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
    # Validate inputs
    request = GA4QueryRequest(
        property_id=property_id,
        dimensions=dimensions,
        metrics=metrics,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        estimate_only=estimate_only,
    )

    service = GA4DataService()
    result = service.query_data(
        property_id=request.property_id,
        dimensions=request.dimensions,
        metrics=request.metrics,
        date_range={"start": request.start_date, "end": request.end_date},
        limit=request.limit,
        estimate_only=request.estimate_only,
    )
    _log_mcp(
        "query_ga4_data",
        None,
        {
            "property_id": request.property_id,
            "dimensions": request.dimensions,
            "metrics": request.metrics,
            "estimate_only": request.estimate_only,
        },
    )
    return result


# Browser Controller Tools (async with timeout)


@mcp.tool()
async def verify_gtm_preview(
    domain: str,
    container_id: str,
    preview_id: str,
    environment: str = "prod",
    test_pages: list[str] | None = None,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Verify GTM Preview mode — check that tags fire correctly before publishing.

    Similar to jtrackingai/analytics-tracking-automation's preview verification.
    Opens GTM Preview mode in a headless browser and verifies tag firing.

    Args:
        domain: Site domain to test
        container_id: GTM container ID (e.g., "GTM-XXXXXX")
        preview_id: GTM Preview mode ID (from GTM UI "Preview" button)
        environment: Site environment (default "prod")
        test_pages: List of paths to test (default ["/"])
        timeout_seconds: Maximum time to wait for verification (10-300 seconds)

    Returns:
        Verification results with tag firing status and recommendations

    Example:
        verify_gtm_preview(
            domain="example.com",
            container_id="GTM-ABC123",
            preview_id="ENV-1",
            test_pages=["/", "/pricing"]
        )
    """
    from services.preview_service import PreviewService
    from services.site_service import SiteService

    # Validate inputs
    request = DomainRequest(domain=domain, environment=environment)
    if not container_id.startswith("GTM-"):
        raise ValueError("container_id must be a valid GTM container ID (e.g., GTM-ABC123)")
    if not preview_id:
        raise ValueError("preview_id is required")
    if not 10 <= timeout_seconds <= 300:
        raise ValueError("timeout_seconds must be between 10 and 300")

    db = _get_db()
    try:
        site_service = SiteService(db)
        site = site_service.get_by_domain(request.domain, request.environment)
        if not site:
            raise ValueError(f"Site '{request.domain}' ({request.environment}) not found")

        service = PreviewService(headless=True, preview_timeout_seconds=timeout_seconds)
        pages = test_pages or ["/"]
        results = []

        for path in pages:
            url = f"https://{request.domain}{path}"
            result = await service.verify_preview(
                url=url,
                container_id=container_id,
                preview_id=preview_id,
            )
            results.append(
                {
                    "url": result.url,
                    "success": result.success,
                    "tags_fired": len([r for r in result.tag_results if r.fired]),
                    "tags_total": len(result.tag_results),
                    "duration_seconds": result.duration_seconds,
                }
            )

        all_success = all(r["success"] for r in results)

        _log_mcp(
            "verify_gtm_preview",
            request.domain,
            {
                "container_id": container_id,
                "pages": len(results),
            },
        )

        return {
            "domain": request.domain,
            "container_id": container_id,
            "overall_success": all_success,
            "pages_tested": len(results),
            "results": results,
            "recommendation": (
                "Proceed with publishing" if all_success else "Review failed tags before publishing"
            ),
        }
    finally:
        db.close()


@mcp.tool()
async def analyze_site_structure(
    domain: str,
    environment: str = "prod",
    max_pages: int = 50,
) -> dict[str, Any]:
    """Analyze website structure with Playwright crawler.

    Similar to jtrackingai/analytics-tracking-automation's site analysis.
    Discovers pages, groups by business purpose, identifies tracking opportunities.

    Args:
        domain: Site domain to analyze
        environment: Site environment (default "prod")
        max_pages: Maximum pages to crawl (default 50, max 100)

    Returns:
        Site analysis with page groups and tracking recommendations

    Example:
        analyze_site_structure(domain="example.com", max_pages=30)
    """
    from services.site_analyzer import SiteAnalyzer
    from services.site_service import SiteService

    # Validate inputs
    request = DomainRequest(domain=domain, environment=environment)
    if not 1 <= max_pages <= 100:
        raise ValueError("max_pages must be between 1 and 100")

    db = _get_db()
    try:
        site_service = SiteService(db)
        site = site_service.get_by_domain(request.domain, request.environment)
        if not site:
            raise ValueError(f"Site '{request.domain}' ({request.environment}) not found")

        analyzer = SiteAnalyzer(max_pages=max_pages, headless=True)
        url = f"https://{request.domain}"
        result = await analyzer.analyze_site(url)

        _log_mcp("analyze_site_structure", request.domain, {"pages": result.total_pages})

        return {
            "domain": request.domain,
            "base_url": result.base_url,
            "total_pages": result.total_pages,
            "crawl_duration_seconds": result.crawl_duration_seconds,
            "page_groups": result.page_groups,
            "tracking_recommendations": {
                purpose: f"Apply '{purpose}' tracking blueprint"
                for purpose in result.page_groups.keys()
            },
        }
    finally:
        db.close()


@mcp.tool()
async def run_browser_test(
    url: str,
    actions: list[dict[str, Any]],
    headless: bool = True,
    capture_screenshots: bool = False,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Run an automated browser test with a sequence of actions.

    Uses Playwright to control a browser and execute actions like clicking,
    filling forms, navigating, and asserting content.

    Args:
        url: Starting URL (must be http:// or https://)
        actions: List of action objects. Each action has:
            - action: str - "navigate", "click", "fill", "select", "wait",
                           "assert_text", "assert_visible", "assert_url", "screenshot"
            - selector: str (optional) - CSS selector for target element
            - value: str (optional) - Value for fill, select, or navigate
            - timeout: int (optional) - Timeout in milliseconds (default 5000)
            - description: str (optional) - Description of the action
        headless: Whether to run browser headless (default True)
        capture_screenshots: Whether to capture screenshots (default False)
        timeout_seconds: Maximum test duration (10-300 seconds, default 60)

    Returns:
        Test result with success status, action results, errors, and metadata

    Example:
        run_browser_test(
            url="https://example.com/login",
            actions=[
                {"action": "fill", "selector": "#email", "value": "user@example.com"},
                {"action": "fill", "selector": "#password", "value": "secret"},
                {"action": "click", "selector": "#login-btn"},
                {"action": "assert_visible", "selector": ".dashboard"}
            ]
        )
    """
    from services.browser_controller import BrowserAction, BrowserController

    # Validate inputs
    request = BrowserTestRequest(
        url=url,
        actions=actions,
        headless=headless,
        capture_screenshots=capture_screenshots,
        timeout_seconds=timeout_seconds,
    )

    # Validate and convert actions
    browser_actions = []
    for i, a in enumerate(request.actions):
        try:
            action_req = BrowserActionRequest(**a)
            browser_actions.append(
                BrowserAction(
                    action=action_req.action,
                    selector=action_req.selector,
                    value=action_req.value,
                    timeout=action_req.timeout,
                    description=action_req.description,
                )
            )
        except Exception as e:
            raise ValueError(f"Invalid action at index {i}: {e}")

    async with BrowserController(
        headless=request.headless,
        timeout=request.timeout_seconds * 1000,  # Convert to milliseconds
    ) as controller:
        result = await controller.run_test(
            request.url,
            browser_actions,
            capture_screenshots=request.capture_screenshots,
        )

    _log_mcp(
        "browser_test",
        None,
        {
            "url": request.url,
            "success": result.success,
            "actions_count": len(result.actions),
        },
    )

    return {
        "success": result.success,
        "url": result.page_url,
        "duration_seconds": result.duration_seconds,
        "actions": result.actions,
        "errors": result.errors,
        "screenshots": result.screenshots,
        "console_logs_count": len(result.console_logs),
        "network_requests_count": len(result.network_requests),
    }


@mcp.tool()
async def test_mcp_metrics_app(
    web_ui_url: str = "http://localhost:5173",
    api_url: str = "http://localhost:8000",
    headless: bool = True,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Test the MCP-Metrics application automatically.

    Performs comprehensive testing of the Web UI and API to verify
    the application is working correctly.

    Args:
        web_ui_url: URL of the Web UI (default http://localhost:5173)
        api_url: URL of the API (default http://localhost:8000)
        headless: Whether to run browser headless (default True)
        timeout_seconds: Maximum test duration (10-300 seconds, default 60)

    Returns:
        Test results with accessibility checks and any errors

    Example:
        test_mcp_metrics_app()
        test_mcp_metrics_app(web_ui_url="http://localhost:3000")
    """
    from services.browser_controller import BrowserController

    # Validate inputs
    request = TestAppRequest(
        web_ui_url=web_ui_url,
        api_url=api_url,
        headless=headless,
        timeout_seconds=timeout_seconds,
    )

    async with BrowserController(
        headless=request.headless,
        timeout=request.timeout_seconds * 1000,
    ) as controller:
        result = await controller.run_health_check_test(
            request.web_ui_url,
            request.api_url,
        )

    _log_mcp(
        "test_mcp_metrics_app",
        None,
        {
            "web_ui_accessible": result.get("web_ui_accessible"),
            "api_accessible": result.get("api_accessible"),
            "all_passed": result.get("all_passed"),
        },
    )

    return result


@mcp.tool()
async def create_site_via_ui(
    domain: str,
    name: str,
    web_ui_url: str = "http://localhost:5173",
    environment: str = "prod",
    blueprint: str = "saas",
    headless: bool = True,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Create a site using the Web UI via browser automation.

    Useful for end-to-end testing of the creation flow.

    Args:
        domain: Site domain (e.g., "example.com")
        name: Site name
        web_ui_url: URL of the Web UI
        environment: Environment (dev/stage/prod)
        blueprint: Blueprint to apply (saas/ecommerce/content/none)
        headless: Whether to run headless
        timeout_seconds: Maximum test duration (10-300 seconds, default 120)

    Returns:
        Result of the UI automation

    Example:
        create_site_via_ui(domain="test.com", name="Test Site")
    """
    from services.browser_controller import BrowserAction, BrowserController

    # Validate inputs
    request = SiteUIRequest(
        domain=domain,
        name=name,
        web_ui_url=web_ui_url,
        environment=environment,
        blueprint=blueprint,
        headless=headless,
        timeout_seconds=timeout_seconds,
    )

    actions = [
        BrowserAction("navigate", value=f"{request.web_ui_url}/create"),
        BrowserAction("wait", selector="input[placeholder='example.com']"),
        BrowserAction(
            "fill",
            selector="input[placeholder='example.com']",
            value=request.domain,
            description="Fill domain",
        ),
        BrowserAction(
            "fill",
            selector="input[placeholder='Example Site']",
            value=request.name,
            description="Fill name",
        ),
        BrowserAction("select", selector="select", value=request.environment),
        BrowserAction("select", selector="select:nth-of-type(2)", value=request.blueprint),
        BrowserAction("click", selector="button[type='submit']", description="Submit form"),
        BrowserAction("wait", value="5", description="Wait for creation"),
        BrowserAction(
            "assert_url",
            value=f"/sites/{request.domain}",
            description="Verify redirect to site detail",
        ),
    ]

    async with BrowserController(
        headless=request.headless,
        timeout=request.timeout_seconds * 1000,
    ) as controller:
        result = await controller.run_test(
            f"{request.web_ui_url}/create",
            actions,
        )

    _log_mcp(
        "create_site_via_ui",
        request.domain,
        {
            "success": result.success,
            "web_ui_url": request.web_ui_url,
        },
    )

    return {
        "success": result.success,
        "domain": request.domain,
        "name": request.name,
        "actions_completed": len(result.actions),
        "errors": result.errors,
        "final_url": result.page_url,
    }


@mcp.tool()
async def browser_gtm_preview_test(
    url: str,
    container_id: str,
    preview_id: str,
    expected_tags: list[dict[str, str]] | None = None,
    headless: bool = True,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Test GTM Preview mode in a browser.

    Opens the page with GTM Preview mode and verifies tags fire correctly.
    This is more thorough than API-only verification.

    Args:
        url: URL to test (must be http:// or https://)
        container_id: GTM container ID (e.g., "GTM-ABC123")
        preview_id: GTM Preview mode ID
        expected_tags: List of expected tags with name and event
        headless: Whether to run headless (default True)
        timeout_seconds: Maximum test duration (10-300 seconds, default 60)

    Returns:
        Verification results with tag firing status

    Example:
        browser_gtm_preview_test(
            url="https://example.com",
            container_id="GTM-ABC123",
            preview_id="PREVIEW-1",
            expected_tags=[
                {"name": "GA4 Config", "event": "page_view"}
            ]
        )
    """
    from services.browser_controller import BrowserController

    # Validate inputs
    request = GTMPreviewRequest(
        url=url,
        container_id=container_id,
        preview_id=preview_id,
        expected_tags=expected_tags,
        headless=headless,
        timeout_seconds=timeout_seconds,
    )

    async with BrowserController(
        headless=request.headless,
        timeout=request.timeout_seconds * 1000,
    ) as controller:
        result = await controller.verify_gtm_preview(
            url=request.url,
            container_id=request.container_id,
            preview_id=request.preview_id,
            expected_tags=request.expected_tags,
        )

    _log_mcp(
        "browser_gtm_preview_test",
        None,
        {
            "url": request.url,
            "container_id": request.container_id,
            "success": result.success,
            "tags_fired": len(result.tags_fired),
        },
    )

    return {
        "success": result.success,
        "url": result.url,
        "container_id": result.container_id,
        "preview_id": result.preview_id,
        "tags_fired": result.tags_fired,
        "data_layer_events": result.data_layer_events,
        "errors": result.errors,
        "duration_seconds": result.duration_seconds,
    }


@mcp.tool()
async def crawl_website(
    start_url: str,
    max_pages: int = 20,
    max_depth: int = 3,
    headless: bool = True,
    crawl_delay_ms: int = 1000,
) -> dict[str, Any]:
    """Crawl a website and collect page information.

    Discovers pages, collects titles, and maps site structure.

    Args:
        start_url: Starting URL (must be http:// or https://)
        max_pages: Maximum pages to crawl (default 20, max 100)
        max_depth: Maximum crawl depth (default 3, max 5)
        headless: Whether to run headless (default True)
        crawl_delay_ms: Delay between requests in milliseconds (default 1000, max 5000)

    Returns:
        Crawl results with discovered pages

    Example:
        crawl_website(start_url="https://example.com", max_pages=10)
    """
    from services.browser_controller import BrowserController

    # Validate inputs
    request = CrawlRequest(
        start_url=start_url,
        max_pages=max_pages,
        max_depth=max_depth,
        headless=headless,
        crawl_delay_ms=crawl_delay_ms,
    )

    async with BrowserController(
        headless=request.headless,
        crawl_delay_ms=request.crawl_delay_ms,
    ) as controller:
        result = await controller.crawl_site(
            start_url=request.start_url,
            max_pages=request.max_pages,
            max_depth=request.max_depth,
            same_domain_only=True,
        )

    _log_mcp(
        "crawl_website",
        None,
        {
            "start_url": request.start_url,
            "pages_crawled": result["pages_crawled"],
        },
    )

    return result


if __name__ == "__main__":
    mcp.run()
