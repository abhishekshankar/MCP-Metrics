"""Site API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.auth import require_admin, require_read
from database import get_db
from observability.logging import increment_metric
from services.blueprint_service import BlueprintService
from services.governance_service import GovernanceService
from services.health_service import HealthService
from services.site_service import SiteService

router = APIRouter(prefix="/sites", tags=["sites"])


class CreateSiteRequest(BaseModel):
    domain: str
    name: str
    environment: str = "prod"
    blueprint: str | None = None
    consent_preset: str = "none"
    primary_domain: str | None = None
    linked_domains: list[str] = Field(default_factory=list)
    enable_bigquery: bool = False
    bigquery_project: str | None = None
    bigquery_dataset: str | None = None


class ApplyBlueprintRequest(BaseModel):
    blueprint: str


class RollbackRequest(BaseModel):
    version: int


@router.post("")
def create_site(
    body: CreateSiteRequest,
    db: Session = Depends(get_db),
    role: str = Depends(require_admin),
):
    service = SiteService(db)
    try:
        result = service.create_site(
            domain=body.domain,
            name=body.name,
            environment=body.environment,
            blueprint=body.blueprint,
            consent_preset=body.consent_preset,
            primary_domain=body.primary_domain,
            linked_domains=body.linked_domains,
            enable_bigquery=body.enable_bigquery,
            bigquery_project=body.bigquery_project,
            bigquery_dataset=body.bigquery_dataset,
            actor=f"api:{role}",
            actor_type="api",
        )
        increment_metric("sites_created")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("")
def list_sites(db: Session = Depends(get_db), role: str = Depends(require_read)):
    service = SiteService(db)
    return [service._site_response(s) for s in service.list_sites()]


@router.get("/{domain}")
def get_site(
    domain: str,
    environment: str = Query("prod"),
    db: Session = Depends(get_db),
    role: str = Depends(require_read),
):
    service = SiteService(db)
    try:
        return service.get_status(domain, environment)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{domain}/describe")
def describe_site(
    domain: str,
    environment: str = Query("prod"),
    db: Session = Depends(get_db),
    role: str = Depends(require_read),
):
    service = SiteService(db)
    try:
        return service.describe_setup(domain, environment)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{domain}/blueprint")
def apply_blueprint(
    domain: str,
    body: ApplyBlueprintRequest,
    environment: str = Query("prod"),
    db: Session = Depends(get_db),
    role: str = Depends(require_admin),
):
    site_service = SiteService(db)
    site = site_service.get_by_domain(domain, environment)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{domain}' not found")
    blueprint_service = BlueprintService(db)
    try:
        return blueprint_service.apply(site, body.blueprint, actor=f"api:{role}", actor_type="api")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{domain}/health")
def site_health(
    domain: str,
    environment: str = Query("prod"),
    db: Session = Depends(get_db),
    role: str = Depends(require_read),
):
    site_service = SiteService(db)
    site = site_service.get_by_domain(domain, environment)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{domain}' not found")
    health = HealthService(db)
    result = health.check_site(site)
    return {
        "domain": domain,
        "status": result.status,
        "event_count_24h": result.event_count_24h,
        "conversion_count_24h": result.conversion_count_24h,
        "traffic_sessions_24h": result.traffic_sessions_24h,
        "anomaly_flags": result.anomaly_flags,
        "metrics": result.metrics,
        "checked_at": result.checked_at.isoformat(),
    }


@router.post("/{domain}/rollback")
def rollback_site(
    domain: str,
    body: RollbackRequest,
    environment: str = Query("prod"),
    db: Session = Depends(get_db),
    role: str = Depends(require_admin),
):
    site_service = SiteService(db)
    site = site_service.get_by_domain(domain, environment)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{domain}' not found")
    governance = GovernanceService(db)
    try:
        return governance.rollback(site, body.version, actor=f"api:{role}", actor_type="api")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{domain}/audit")
def site_audit(
    domain: str,
    operation: str | None = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    role: str = Depends(require_read),
):
    from services.audit_service import AuditService

    audit = AuditService(db)
    logs = audit.list_logs(domain=domain, operation=operation, limit=limit)
    return [
        {
            "id": log.id,
            "operation": log.operation,
            "actor": log.actor,
            "actor_type": log.actor_type,
            "status": log.status,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/{domain}/diff")
def gtm_diff(
    domain: str,
    before: str = Query(...),
    after: str = Query(...),
    environment: str = Query("prod"),
    db: Session = Depends(get_db),
    role: str = Depends(require_read),
):
    site_service = SiteService(db)
    site = site_service.get_by_domain(domain, environment)
    if not site or not site.gtm_container_id:
        raise HTTPException(status_code=404, detail="Site or GTM container not found")
    governance = GovernanceService(db)
    return governance.diff_gtm(before, after, site.gtm_container_id)


@router.get("/{domain}/versions")
def site_versions(
    domain: str,
    environment: str = Query("prod"),
    db: Session = Depends(get_db),
    role: str = Depends(require_read),
):
    """Get blueprint version history for a site."""
    site_service = SiteService(db)
    site = site_service.get_by_domain(domain, environment)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{domain}' not found")
    governance = GovernanceService(db)
    versions = governance.get_version_history(site.id)
    return {
        "versions": [
            {
                "number": v.version_number,
                "blueprint_name": v.blueprint_name,
                "gtm_version_id": v.gtm_version_id,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ]
    }


@router.get("/{domain}/health/history")
def health_history(
    domain: str,
    limit: int = Query(30, le=100),
    environment: str = Query("prod"),
    db: Session = Depends(get_db),
    role: str = Depends(require_read),
):
    """Get health check history for a site."""
    site_service = SiteService(db)
    site = site_service.get_by_domain(domain, environment)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{domain}' not found")
    health = HealthService(db)
    history = health.get_history(site.id, limit)
    return [
        {
            "timestamp": h.checked_at.isoformat(),
            "event_count": h.event_count_24h,
            "sessions": h.traffic_sessions_24h,
            "conversions": h.conversion_count_24h,
            "status": h.status,
            "anomaly_flags": h.anomaly_flags,
        }
        for h in history
    ]


class SiteAnalysisRequest(BaseModel):
    max_pages: int = Query(50, ge=1, le=100)
    crawl_depth: int = Query(3, ge=1, le=5)


@router.post("/{domain}/analyze")
def analyze_site(
    domain: str,
    body: SiteAnalysisRequest,
    environment: str = Query("prod"),
    db: Session = Depends(get_db),
    role: str = Depends(require_admin),
):
    """Analyze site structure with Playwright crawler (like jtrackingai).

    Discovers pages, groups by business purpose, identifies tracking opportunities.
    """
    import asyncio

    from services.site_analyzer import SiteAnalyzer

    site_service = SiteService(db)
    site = site_service.get_by_domain(domain, environment)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{domain}' not found")

    analyzer = SiteAnalyzer(
        max_pages=body.max_pages,
        crawl_depth=body.crawl_depth,
        headless=True,
    )

    try:
        url = f"https://{site.domain}"
        result = asyncio.run(analyzer.analyze_site(url))

        return {
            "domain": domain,
            "base_url": result.base_url,
            "total_pages": result.total_pages,
            "crawl_duration_seconds": result.crawl_duration_seconds,
            "page_groups": result.page_groups,
            "pages": [
                {
                    "url": p.url,
                    "title": p.title,
                    "business_purpose": p.business_purpose,
                    "tracking_potential": p.tracking_potential,
                    "headings": p.headings[:5],
                    "buttons_count": len(p.buttons),
                    "forms_count": len(p.forms),
                }
                for p in result.pages[:20]  # Limit response size
            ],
            "errors": result.errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Site analysis failed: {e}") from e
