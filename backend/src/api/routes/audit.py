"""Audit API routes - includes audit log and analytics implementation audit."""

from typing import Any, Literal

from api.auth import require_read
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from services.audit_service import AuditService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/audit", tags=["audit"])


# ============================================================================
# Audit Log Endpoints (Existing)
# ============================================================================


@router.get("")
def list_audit_logs(
    domain: str | None = None,
    operation: str | None = None,
    actor: str | None = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    role: str = Depends(require_read),
):
    """List audit logs with optional filtering."""
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


# ============================================================================
# Analytics Implementation Audit Endpoints (New)
# ============================================================================


class AnalyticsAuditRequest(BaseModel):
    """Request to run an analytics implementation audit."""

    url: str = Field(..., description="URL to audit")
    crawl_depth: int = Field(2, ge=0, le=5, description="How deep to crawl")
    max_pages: int = Field(20, ge=1, le=100, description="Maximum pages to check")
    check_consent: bool = Field(True, description="Check consent implementation")
    check_ecommerce: bool = Field(
        False, description="Check e-commerce tracking"
    )
    expected_blueprint: str | None = Field(
        None, description="Compare against blueprint"
    )


class AuditFindingResponse(BaseModel):
    """Single audit finding response."""

    severity: Literal["critical", "warning", "info"]
    category: str
    issue: str
    description: str
    affected_pages: list[str]
    fix_recommendation: str
    fix_complexity: Literal["simple", "moderate", "complex"]
    evidence: dict[str, Any] | None = None


class AuditActionItem(BaseModel):
    """Prioritized action plan item."""

    priority: int
    fix: str
    effort: str
    impact: str
    category: str


class AnalyticsAuditReportResponse(BaseModel):
    """Complete analytics audit report response."""

    url: str
    audit_timestamp: str
    crawl_pages: int
    score: int
    grade: str
    critical_count: int
    warning_count: int
    info_count: int
    category_scores: dict[str, int]
    findings: list[AuditFindingResponse]
    working_well: list[str]
    action_plan: list[AuditActionItem]


# Mock data for demo - replace with real audit in production
MOCK_ANALYTICS_AUDIT_REPORT: AnalyticsAuditReportResponse = (
    AnalyticsAuditReportResponse(
        url="https://example.com",
        audit_timestamp="2024-06-29T20:16:00Z",
        crawl_pages=23,
        score=62,
        grade="D+",
        critical_count=3,
        warning_count=8,
        info_count=5,
        category_scores={
            "tag_presence": 30,
            "duplication": 45,
            "consent": 25,
            "data_quality": 60,
            "ecommerce": 75,
            "spa_tracking": 90,
            "gtm_specific": 70,
            "performance": 85,
        },
        findings=[
            AuditFindingResponse(
                severity="critical",
                category="duplication",
                issue="Double GA4 tracking detected",
                description=(
                    "Found 2 GA4 properties firing on same page: "
                    "G-ABC123DEF (Production) and G-XYZ789ABC (Test). "
                    "All metrics inflated 2x."
                ),
                affected_pages=["/", "/pricing", "/about", "/contact"],
                fix_recommendation=(
                    "Remove test property from production "
                    "or use separate data streams"
                ),
                fix_complexity="simple",
                evidence={
                    "measurement_ids": ["G-ABC123DEF", "G-XYZ789ABC"],
                    "html_location": "<head>",
                },
            ),
            AuditFindingResponse(
                severity="critical",
                category="consent",
                issue="Analytics fires before consent",
                description=(
                    "GA4 page_view fires at 0.2s, consent granted at 1.5s. "
                    "Violates GDPR consent requirements."
                ),
                affected_pages=["all"],
                fix_recommendation=(
                    "Set default consent to denied, update after user choice"
                ),
                fix_complexity="moderate",
                evidence={
                    "ga4_time": 0.2,
                    "consent_time": 1.5,
                    "consent_mechanism": "none detected",
                },
            ),
            AuditFindingResponse(
                severity="critical",
                category="consent",
                issue="No consent mechanism detected",
                description=(
                    "No CMP (Cookiebot, OneTrust, etc.) or custom consent "
                    "solution found. May violate GDPR/CCPA."
                ),
                affected_pages=["all"],
                fix_recommendation=(
                    "Implement consent mode v2 with CMP or custom solution"
                ),
                fix_complexity="moderate",
                evidence={
                    "cookies_found": ["_ga", "_gid", "session_id"],
                    "cmp_signatures": [],
                },
            ),
            AuditFindingResponse(
                severity="warning",
                category="data_quality",
                issue="Missing page titles in 40% of pages",
                description=(
                    "23 pages have empty or generic <title> tags. "
                    "Impacts reporting and SEO."
                ),
                affected_pages=[
                    "/blog/*",
                    "/products/item-123",
                    "/category/old",
                ],
                fix_recommendation=(
                    "Add descriptive <title> tags for better reporting"
                ),
                fix_complexity="simple",
                evidence={
                    "empty_titles": 9,
                    "generic_titles": 14,
                },
            ),
            AuditFindingResponse(
                severity="warning",
                category="gtm_specific",
                issue="GTM preview mode on production",
                description=(
                    "GTM debug panel visible to all users. "
                    "Performance impact and security risk."
                ),
                affected_pages=["all"],
                fix_recommendation=(
                    "Publish container and disable preview mode"
                ),
                fix_complexity="simple",
                evidence={
                    "gtm_debug_param": "gtm_debug=x",
                    "preview_mode": True,
                },
            ),
            AuditFindingResponse(
                severity="warning",
                category="tag_presence",
                issue="Hardcoded GA4 measurement ID",
                description=(
                    "Measurement ID hardcoded in gtag.js instead of "
                    "GTM variable. Harder to maintain."
                ),
                affected_pages=["/", "/pricing"],
                fix_recommendation=(
                    "Move to GTM variable for easier updates"
                ),
                fix_complexity="simple",
                evidence={
                    "location": "inline script",
                    "ids_found": ["G-ABC123DEF"],
                },
            ),
            AuditFindingResponse(
                severity="info",
                category="performance",
                issue="GA4 not loaded async",
                description="gtag.js blocking render - could be deferred",
                affected_pages=["all"],
                fix_recommendation=(
                    "Add async or defer attribute to script tag"
                ),
                fix_complexity="simple",
                evidence={
                    "script_attributes": [],
                    "load_time_ms": 120,
                },
            ),
            AuditFindingResponse(
                severity="info",
                category="data_quality",
                issue="Internal search not tracked",
                description="?q= and ?search= parameters ignored by GA4",
                affected_pages=["/search"],
                fix_recommendation=(
                    "Enable site search tracking in GA4 settings"
                ),
                fix_complexity="simple",
                evidence={
                    "search_params_found": ["?q=test", "?search=hello"],
                    "ga4_search_events": 0,
                },
            ),
        ],
        working_well=[
            "✅ GTM container properly configured",
            "✅ SPA navigation tracked via history changes",
            "✅ Enhanced measurement enabled (scroll, outbound clicks)",
            "✅ Cross-domain tracking configured correctly",
            "✅ DataLayer structure consistent across pages",
            "✅ Web Vitals tracked (LCP, CLS, FID)",
        ],
        action_plan=[
            AuditActionItem(
                priority=1,
                fix="Remove duplicate GA4 tag (G-XYZ789ABC)",
                effort="30 minutes",
                impact="High - fixes 100% metric inflation",
                category="duplication",
            ),
            AuditActionItem(
                priority=2,
                fix="Implement consent mode v2",
                effort="2 hours",
                impact="Legal - GDPR compliance",
                category="consent",
            ),
            AuditActionItem(
                priority=3,
                fix="Add CMP or custom consent banner",
                effort="4 hours",
                impact="Legal - consent collection",
                category="consent",
            ),
            AuditActionItem(
                priority=4,
                fix="Fix missing page titles (23 pages)",
                effort="2 hours",
                impact="Medium - reporting quality",
                category="data_quality",
            ),
            AuditActionItem(
                priority=5,
                fix="Disable GTM preview mode on production",
                effort="15 minutes",
                impact="Low - security/performance",
                category="gtm_specific",
            ),
        ],
    )
)


@router.post("/check", response_model=AnalyticsAuditReportResponse)
async def run_analytics_audit(
    request: AnalyticsAuditRequest,
    role: str = Depends(require_read),
):
    """
    Run comprehensive analytics audit on any website.

    Detects: duplicate tracking, consent issues, missing tags,
    GTM misconfigurations, e-commerce problems, SPA issues.

    Returns detailed report with severity scores and fix recommendations.
    """
    try:
        # For demo, return mock data with requested URL
        # In production, use: auditor = AnalyticsAuditor(...)
        report = MOCK_ANALYTICS_AUDIT_REPORT.model_copy()
        report.url = request.url

        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/check/categories")
def get_audit_categories(
    role: str = Depends(require_read),
) -> dict[str, str]:
    """Get list of audit categories and descriptions."""
    return {
        "tag_presence": "GA4/GTM presence and configuration",
        "duplication": "Multiple tags firing (double counting)",
        "consent": "GDPR/CCPA consent implementation",
        "data_quality": "Event naming, parameter consistency",
        "ecommerce": "Purchase/transaction tracking",
        "spa_tracking": "Single Page App virtual pageviews",
        "gtm_specific": "GTM container configuration",
        "performance": "Script loading, impact on page speed",
    }
