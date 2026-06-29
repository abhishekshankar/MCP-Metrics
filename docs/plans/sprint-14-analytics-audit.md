# Sprint 14: Analytics Implementation Audit & Wrong Setup Detection

**Status:** Planned  
**Duration:** 2 weeks  
**Goal:** Automatically detect existing wrong, broken, or suboptimal analytics implementations on any website.

---

## Overview

When given a site URL, the platform crawls it and detects **implementation problems** with existing analytics — wrong configurations, missing tags, common anti-patterns, and compliance issues.

### What It Detects

```bash
# Run comprehensive audit
analytics-mcp audit --domain example.com --deep

# MCP tool equivalent
audit_analytics_implementation(domain="example.com")
```

**Output Example:**
```json
{
  "score": 62,
  "grade": "D+",
  "critical_issues": 3,
  "warnings": 8,
  "recommendations": 12,
  "findings": [
    {
      "severity": "critical",
      "category": "duplication",
      "issue": "Double GA4 tracking detected",
      "details": "Found 2 GA4 tags firing on same page (G-XXXX and G-YYYY)",
      "affected_pages": ["/", "/pricing", "/about"],
      "fix": "Remove duplicate gtag.js or consolidate to single property"
    },
    {
      "severity": "critical", 
      "category": "consent",
      "issue": "Analytics firing before consent",
      "details": "GA4 page_view fires immediately, ignoring consent state",
      "affected_pages": ["all"],
      "fix": "Implement consent mode v2 with default denied state"
    },
    {
      "severity": "warning",
      "category": "data_quality",
      "issue": "Missing page titles in 40% of pages",
      "details": "23 pages have empty or generic <title> tags",
      "affected_pages": ["/blog/*", "/products/item-123"],
      "fix": "Add descriptive <title> tags for better reporting"
    }
  ]
}
```

---

## Detection Categories

### 1. Tag Presence & Configuration

| Check | Severity | Description |
|-------|----------|-------------|
| **No GA4 detected** | Critical | No GA4 tag found (gtag.js, GTM, or Measurement Protocol) |
| **Multiple GA4 properties** | Critical | Same page sends to 2+ properties (double counting) |
| **GTM present but no GA4** | Warning | GTM loaded but no GA4 config tag configured |
| **Hardcoded GA4 ID** | Warning | ID hardcoded instead of GTM variable (harder to maintain) |
| **Wrong GA4 ID format** | Critical | Invalid measurement ID format |
| **Legacy UA still active** | Warning | Universal Analytics tag detected (sunset) |
| **GA4 + UA hybrid** | Info | Both present (migration in progress?) |

### 2. Consent & Privacy (GDPR/CCPA)

| Check | Severity | Description |
|-------|----------|-------------|
| **No consent mechanism** | Critical | No CMP or custom consent solution detected |
| **Analytics fires before consent** | Critical | Events sent before user grants permission |
| **Consent mode not implemented** | Warning | GA4 loaded without consent mode v2 |
| **Missing consent default** | Warning | No default consent state (assumes granted) |
| **Storage denied but analytics fires** | Critical | analytics_storage=denied but events still send |
| **No privacy policy link** | Warning | Required for GDPR compliance |
| **Cookie banner non-compliant** | Warning | Banner blocks content (intrusive) or has pre-ticked boxes |

### 3. DataLayer & Event Implementation

| Check | Severity | Description |
|-------|----------|-------------|
| **No dataLayer** | Warning | Events pushed directly without dataLayer structure |
| **dataLayer defined after GTM** | Critical | `window.dataLayer = []` resets queued events |
| **Inconsistent event naming** | Warning | Mix of snake_case, camelCase, PascalCase |
| **Missing required events** | Warning | No purchase/lead/submit on conversion pages |
| **Custom events without parameters** | Info | Events fire but carry no useful data |
| **ecommerce data missing** | Warning | Purchase events without transaction_id, value, currency |
| **Event parameters inconsistent** | Warning | Same event has different parameters across pages |
| **dataLayer variables not in GTM** | Info | Pushed to DL but no GTM variables created |

### 4. GTM Specific Issues

| Check | Severity | Description |
|-------|----------|-------------|
| **GTM not published** | Critical | Container in preview mode only (no live version) |
| **Multiple GTM containers** | Warning | 2+ GTM IDs on same page (conflict risk) |
| **GTM snippet in wrong location** | Warning | Not in `<head>` (can miss early pageviews) |
| **GTM preview mode on production** | Warning | Debug panel visible to all users |
| **Triggers firing on all events** | Warning | "All Pages" triggers with no filtering |
| **Tags without triggers** | Info | Configured but never fire (orphaned) |
| **Blocking triggers not used** | Warning | No consent-based blocking on analytics tags |
| **Workspaces with unpublished changes** | Info | Staged changes not live |

### 5. E-commerce Tracking

| Check | Severity | Description |
|-------|----------|-------------|
| **No e-commerce events** | Warning | Product/add_to_cart/purchase not detected |
| **Missing currency** | Critical | Transactions lack currency code |
| **Missing transaction_id** | Critical | Purchase events without unique ID |
| **Value as string** | Warning | transaction_value: "99.99" instead of 99.99 |
| **Tax/shipping not included** | Warning | Revenue calculations may be wrong |
| **Product array empty** | Critical | purchase fires but items: [] |
| **SKU as product name** | Warning | item_name contains SKU instead of readable name |

### 6. Technical Implementation

| Check | Severity | Description |
|-------|----------|-------------|
| **Pageview on SPA without history** | Critical | Single page app but no virtual pageview tracking |
| **Duplicate pageviews on SPA** | Warning | Multiple pageviews fired for same route |
| **404 page tracked as regular** | Warning | Error pages sending normal page_view |
| **Query params not cleaned** | Warning | UTM parameters in page_location (wrong attribution) |
| **Cross-domain not configured** | Warning | Subdomain/cross-domain traffic split into separate sessions |
| **Referral exclusion missing** | Warning | Payment processor (Stripe/PayPal) appears as referrer |
| **Enhanced measurement off** | Info | Scroll, outbound clicks, site search not auto-tracked |
| **Internal search not tracked** | Info | ?q= or ?search= parameters ignored |

### 7. Performance & Data Quality

| Check | Severity | Description |
|-------|----------|-------------|
| **GA4 blocking render** | Warning | gtag.js not async/deferred |
| **GTM container too large** | Warning | >100KB (slows page load) |
| **Client ID reset on navigation** | Critical | New session every page (cookie issue) |
| **Session timeout too short** | Info | 30 min timeout (default) vs site behavior |
| **Missing user_id for logged-in** | Info | Authenticated users tracked anonymously |
| **Bot traffic not filtered** | Warning | Obvious bot hits in data (speed, patterns) |
| **Internal traffic not excluded** | Warning | Office IPs showing in reports |

---

## Implementation Architecture

### 1. Audit Engine (`backend/src/services/audit_engine.py`)

```python
@dataclass
class AuditFinding:
    """Single audit finding."""
    severity: Literal["critical", "warning", "info"]
    category: str  # duplication, consent, data_quality, etc.
    issue: str  # Human-readable issue name
    description: str  # Detailed explanation
    affected_pages: list[str]  # URLs where issue found
    evidence: dict  # Screenshots, code snippets, dataLayer state
    fix_recommendation: str
    fix_complexity: Literal["simple", "moderate", "complex"]
    doc_link: str | None  # Link to GA4/GTM documentation


@dataclass  
class AuditReport:
    """Complete audit results."""
    url: str
    audit_timestamp: datetime
    crawl_pages: int
    score: int  # 0-100
    grade: str  # A+, A, B, C, D, F
    
    # Summary counts
    critical_count: int
    warning_count: int
    info_count: int
    
    # Category breakdown
    category_scores: dict[str, int]  # consent: 45, duplication: 90, ...
    
    # Findings
    findings: list[AuditFinding]
    
    # Positive findings (what's working)
    working_well: list[str]
    
    # Prioritized action plan
    action_plan: list[dict]  # Ordered list of fixes with effort estimates


class AnalyticsAuditor:
    """Detect wrong analytics implementations."""
    
    def __init__(self, browser_controller: BrowserController):
        self.browser = browser_controller
        self.detectors = [
            TagPresenceDetector(),
            ConsentDetector(),
            DataLayerDetector(),
            GTMSpecificDetector(),
            EcommerceDetector(),
            SPADetector(),
            PerformanceDetector(),
        ]
    
    async def audit_site(
        self, 
        url: str,
        crawl_depth: int = 2,
        max_pages: int = 20,
        check_consent: bool = True,
        check_ecommerce: bool = True,
    ) -> AuditReport:
        """Run complete analytics audit on a website."""
        # Crawl site
        pages = await self._crawl_site(url, max_pages, crawl_depth)
        
        # Run detectors on each page
        all_findings = []
        for page in pages:
            page_findings = await self._audit_page(page)
            all_findings.extend(page_findings)
        
        # Aggregate and deduplicate
        aggregated = self._aggregate_findings(all_findings)
        
        # Calculate scores
        scores = self._calculate_scores(aggregated, pages)
        
        # Generate action plan
        action_plan = self._prioritize_fixes(aggregated)
        
        return AuditReport(
            url=url,
            crawl_pages=len(pages),
            score=scores["overall"],
            grade=self._score_to_grade(scores["overall"]),
            findings=aggregated,
            action_plan=action_plan,
            ...
        )
```

### 2. Individual Detectors

```python
class TagPresenceDetector:
    """Detect GA4/GTM presence and configuration issues."""
    
    async def detect(self, page: PageSnapshot) -> list[AuditFinding]:
        findings = []
        
        # Check for GA4
        ga4_tags = await self._find_ga4_tags(page)
        
        if len(ga4_tags) == 0:
            findings.append(AuditFinding(
                severity="critical",
                category="tag_presence",
                issue="No GA4 detected",
                description="No GA4 tag (gtag.js, GTM, or Measurement Protocol) found on page",
                affected_pages=[page.url],
                evidence={"html_snippet": page.head_html[:1000]},
                fix_recommendation="Install GA4 via gtag.js or GTM",
                fix_complexity="simple",
            ))
        elif len(ga4_tags) > 1:
            findings.append(AuditFinding(
                severity="critical",
                category="duplication",
                issue="Multiple GA4 properties detected",
                description=f"Found {len(ga4_tags)} GA4 tags firing: {', '.join(ga4_tags)}",
                affected_pages=[page.url],
                evidence={"measurement_ids": ga4_tags},
                fix_recommendation="Consolidate to single GA4 property or use separate data streams",
                fix_complexity="moderate",
            ))
        
        # Check for GTM
        gtm_tags = await self._find_gtm_tags(page)
        if gtm_tags and not any(t.get("has_ga4_config") for t in gtm_tags):
            findings.append(AuditFinding(
                severity="warning",
                category="tag_presence",
                issue="GTM present but no GA4 configured",
                description="GTM container loaded but no GA4 Configuration tag found",
                affected_pages=[page.url],
                fix_recommendation="Add GA4 Configuration tag in GTM",
                fix_complexity="simple",
            ))
        
        return findings


class ConsentDetector:
    """Detect consent and privacy implementation issues."""
    
    async def detect(self, page: PageSnapshot) -> list[AuditFinding]:
        findings = []
        
        # Check if consent mechanism exists
        consent_cookies = ["cookiebot", "onetrust", "trustarc", "complianz"]
        has_cmp = any(c in page.cookies for c in consent_cookies)
        has_custom_consent = "consent" in str(page.dataLayer).lower()
        
        if not has_cmp and not has_custom_consent:
            findings.append(AuditFinding(
                severity="critical",
                category="consent",
                issue="No consent mechanism detected",
                description="No CMP or custom consent solution found. May violate GDPR/CCPA.",
                affected_pages=[page.url],
                evidence={"cookies": list(page.cookies.keys())[:20]},
                fix_recommendation="Implement consent mode v2 with CMP or custom solution",
                fix_complexity="moderate",
            ))
        
        # Check if analytics fires before consent
        dataLayer = page.dataLayer
        ga4_events = [e for e in dataLayer if e.get("event") in ["page_view", "screen_view"]]
        consent_events = [e for e in dataLayer if "consent" in str(e).lower()]
        
        if ga4_events and consent_events:
            ga4_time = min(e.get("_timestamp", 999) for e in ga4_events)
            consent_time = min(e.get("_timestamp", 0) for e in consent_events)
            
            if ga4_time < consent_time:
                findings.append(AuditFinding(
                    severity="critical",
                    category="consent",
                    issue="Analytics fires before consent",
                    description=f"GA4 page_view fired at {ga4_time}s, consent at {consent_time}s",
                    affected_pages=[page.url],
                    evidence={"timeline": [ga4_events[0], consent_events[0]]},
                    fix_recommendation="Set default consent to denied, update after user choice",
                    fix_complexity="moderate",
                ))
        
        return findings


class SPADetector:
    """Detect Single Page App tracking issues."""
    
    async def detect(self, page: PageSnapshot, navigation_log: list[dict]) -> list[AuditFinding]:
        findings = []
        
        # Detect if SPA
        is_spa = self._is_likely_spa(page, navigation_log)
        
        if is_spa:
            # Check for virtual pageviews
            virtual_pageviews = [e for e in page.dataLayer 
                                if e.get("event") in ["page_view", "virtual_pageview", "history_change"]]
            
            if len(virtual_pageviews) == 1:
                findings.append(AuditFinding(
                    severity="critical",
                    category="spa_tracking",
                    issue="SPA detected but no virtual pageviews",
                    description="Single Page App architecture detected, but only initial page_view found",
                    affected_pages=[page.url],
                    evidence={"navigation": navigation_log[:5]},
                    fix_recommendation="Implement history change listener and fire virtual pageviews",
                    fix_complexity="complex",
                ))
            
            # Check for duplicate pageviews
            if len(virtual_pageviews) > len(set(p.get("page_location") for p in virtual_pageviews)):
                findings.append(AuditFinding(
                    severity="warning",
                    category="spa_tracking",
                    issue="Duplicate pageviews on SPA",
                    description="Multiple page_view events for same route detected",
                    affected_pages=[page.url],
                    fix_recommendation="Debounce route change events or check trigger conditions",
                    fix_complexity="moderate",
                ))
        
        return findings


class EcommerceDetector:
    """Detect e-commerce tracking issues."""
    
    async def detect(self, page: PageSnapshot) -> list[AuditFinding]:
        findings = []
        
        # Find purchase events
        purchase_events = [e for e in page.dataLayer if e.get("event") == "purchase"]
        
        for event in purchase_events:
            ecommerce = event.get("ecommerce", {})
            
            # Check required fields
            if not ecommerce.get("transaction_id"):
                findings.append(AuditFinding(
                    severity="critical",
                    category="ecommerce",
                    issue="Purchase event missing transaction_id",
                    description="Purchase event fired without unique transaction identifier",
                    affected_pages=[page.url],
                    evidence={"event": event},
                    fix_recommendation="Include transaction_id in purchase dataLayer push",
                    fix_complexity="simple",
                ))
            
            if not ecommerce.get("currency"):
                findings.append(AuditFinding(
                    severity="critical",
                    category="ecommerce",
                    issue="Purchase event missing currency",
                    description="GA4 requires currency code for all monetary values",
                    affected_pages=[page.url],
                    fix_recommendation="Add currency: 'USD' (or appropriate code) to purchase event",
                    fix_complexity="simple",
                ))
            
            # Check items array
            items = ecommerce.get("items", [])
            if not items:
                findings.append(AuditFinding(
                    severity="warning",
                    category="ecommerce",
                    issue="Purchase event has no items",
                    description="Purchase recorded but product details not included",
                    affected_pages=[page.url],
                    fix_recommendation="Populate items array with product details",
                    fix_complexity="moderate",
                ))
        
        return findings
```

### 3. Page Snapshot Structure

```python
@dataclass
class PageSnapshot:
    """Captured page state for analysis."""
    url: str
    timestamp: datetime
    
    # DOM/HTML
    head_html: str
    body_html: str
    title: str
    
    # Scripts & Tags
    scripts: list[dict]  # {src, async, defer, inline_content}
    inline_scripts: list[str]
    
    # Analytics-specific
    dataLayer: list[dict]  # Captured dataLayer state with timestamps
    gtm_events: list[dict]  # GTM-specific event log
    ga4_beacons: list[dict]  # Captured GA4 network requests
    
    # Network
    network_requests: list[dict]  # All requests with timing
    cookies: dict[str, str]
    localStorage: dict[str, str]
    
    # Consent
    consent_state: dict  # {analytics_storage, ad_storage, ...}
    
    # Performance
    performance_timing: dict  # Navigation timing API data
    web_vitals: dict  # LCP, CLS, FID if captured
    
    # SPA detection
    navigation_history: list[str]  # URL changes during session


class PageCapture:
    """Capture page state using BrowserController."""
    
    async def capture(self, url: str, interactions: bool = True) -> PageSnapshot:
        """Capture comprehensive page snapshot."""
        async with BrowserController() as browser:
            page = await browser.new_page(
                capture_console=True,
                capture_network=True,
                monitor_dataLayer=True,  # Custom hook to watch dataLayer
            )
            
            # Navigate and wait
            await page.goto(url, wait_until="networkidle")
            
            # Let GTM/GA4 initialize
            await asyncio.sleep(2)
            
            # Capture state
            snapshot = PageSnapshot(
                url=url,
                head_html=await page.content(),
                dataLayer=await self._extract_dataLayer(page),
                ga4_beacons=self._extract_ga4_beacons(page.network_requests),
                ...
            )
            
            # Interact if needed (for SPA detection)
            if interactions:
                await self._interact_and_capture(page, snapshot)
            
            return snapshot
    
    async def _interact_and_capture(self, page, snapshot: PageSnapshot):
        """Click links and capture SPA navigation."""
        # Find internal links
        links = await page.eval_on_selector_all("a[href^='/']", 
            "els => els.slice(0, 5).map(el => el.getAttribute('href'))")
        
        for link in links[:3]:  # Sample 3 pages
            current_url = page.url
            await page.click(f"a[href='{link}']")
            await page.wait_for_load_state("networkidle")
            
            # Capture navigation
            if page.url != current_url:
                snapshot.navigation_history.append(page.url)
                # Capture new dataLayer state
                new_dataLayer = await self._extract_dataLayer(page)
                snapshot.dataLayer.extend(new_dataLayer)
```

### 4. Scoring Algorithm

```python
def calculate_audit_score(findings: list[AuditFinding], pages: int) -> dict:
    """Calculate overall and category scores."""
    
    # Weight by severity
    weights = {"critical": -15, "warning": -5, "info": -1}
    
    # Category weights (importance to business)
    category_weights = {
        "duplication": 1.5,  # Data quality killer
        "consent": 1.3,      # Legal risk
        "ecommerce": 1.2,    # Revenue tracking
        "tag_presence": 1.0,
        "data_quality": 0.9,
        "spa_tracking": 0.8,
        "gtm_specific": 0.7,
        "performance": 0.5,
    }
    
    # Calculate per-category
    category_scores = {}
    for category in category_weights:
        cat_findings = [f for f in findings if f.category == category]
        deductions = sum(weights[f.severity] for f in cat_findings)
        # Normalize by page count (issues on more pages = worse)
        affected_ratio = len(set(f.affected_pages[0] for f in cat_findings)) / pages
        
        category_scores[category] = max(0, 100 + (deductions * affected_ratio))
    
    # Weighted overall score
    overall = sum(
        category_scores[cat] * weight 
        for cat, weight in category_weights.items()
    ) / sum(category_weights.values())
    
    return {
        "overall": int(overall),
        "categories": {cat: int(score) for cat, score in category_scores.items()}
    }


def score_to_grade(score: int) -> str:
    """Convert score to letter grade."""
    if score >= 95: return "A+"
    if score >= 90: return "A"
    if score >= 85: return "B+"
    if score >= 80: return "B"
    if score >= 75: return "C+"
    if score >= 70: return "C"
    if score >= 65: return "D+"
    if score >= 60: return "D"
    return "F"
```

---

## API & CLI Design

### REST API

```python
# POST /audit
class AuditRequest(BaseModel):
    url: str
    crawl_depth: int = Field(2, ge=0, le=5)
    max_pages: int = Field(20, ge=1, le=100)
    checks: list[str] = Field(default=["all"])  # Or specific categories
    
    # Optional: compare against blueprint
    expected_blueprint: str | None = None  # "saas", "ecommerce", etc.


class AuditResponse(BaseModel):
    audit_id: str
    status: str  # running, completed, failed
    report: AuditReport | None
    
    # Quick summary for dashboard
    summary: dict = {
        "score": 62,
        "grade": "D+",
        "critical_count": 3,
        "warning_count": 8,
        "top_issue": "Double GA4 tracking detected",
    }
```

### CLI Commands

```bash
# Basic audit (quick check)
analytics-mcp audit --domain example.com

# Deep audit (more pages, interactions)
analytics-mcp audit --domain example.com --deep --max-pages 50

# Audit with blueprint comparison
analytics-mcp audit --domain example.com --blueprint ecommerce

# Output formats
analytics-mcp audit --domain example.com --format json > audit.json
analytics-mcp audit --domain example.com --format html > audit-report.html
analytics-mcp audit --domain example.com --format markdown > audit.md

# Continuous monitoring (schedule regular audits)
analytics-mcp audit-schedule --domain example.com --frequency weekly

# Compare audits over time
analytics-mcp audit-history --domain example.com --last 30
```

### MCP Tools

```python
@mcp.tool()
async def audit_analytics_implementation(
    url: str,
    crawl_depth: int = 2,
    check_consent: bool = True,
    check_ecommerce: bool = False,
    expected_events: list[str] | None = None,
) -> str:
    """
    Audit a website's analytics implementation for common mistakes.
    
    Detects: duplicate tracking, consent issues, missing events,
    GTM misconfigurations, e-commerce problems, SPA issues.
    
    Returns detailed report with severity scores and fix recommendations.
    """


@mcp.tool()
async def compare_audit_to_blueprint(
    audit_id: str,
    blueprint_name: str,
) -> str:
    """
    Compare audit findings against expected blueprint implementation.
    
    Identifies: missing blueprint events, wrong trigger types,
    incorrect parameter naming.
    """


@mcp.tool()
async def get_audit_action_plan(
    audit_id: str,
    max_effort_hours: float | None = None,  # Filter by fix time
) -> str:
    """
    Get prioritized list of fixes from audit.
n    
    Sorted by: impact (revenue/data quality), effort required,
    dependencies between fixes.
    """
```

---

## Report Output Formats

### Markdown Report Example

```markdown
# Analytics Audit Report: example.com

**Score:** 62/100 (D+)  
**Audit Date:** 2024-01-15  
**Pages Crawled:** 23

---

## Executive Summary

Your analytics implementation has **3 critical issues** that are significantly 
impacting data quality and may pose legal compliance risks.

### Top Priorities

1. 🔴 **Fix Double Tracking** (30 min) — Inflating metrics by 100%
2. 🔴 **Implement Consent Mode** (2 hours) — GDPR compliance risk
3. 🟡 **Add E-commerce Parameters** (1 hour) — Revenue tracking incomplete

---

## Critical Issues (3)

### 1. Double GA4 Tracking

**Severity:** 🔴 Critical  
**Category:** Data Quality  
**Affected Pages:** /, /pricing, /about, /contact

**Problem:** Two GA4 properties firing on same pages:
- G-ABC123DEF (Production)
- G-XYZ789ABC (Test/Staging)

**Impact:** All metrics (users, sessions, conversions) inflated 2x.
Decision-making based on incorrect data.

**Fix:** Remove test property from production or use separate data streams.

**Evidence:**
```html
<!-- In <head> -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123DEF"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-ABC123DEF');
  gtag('config', 'G-XYZ789ABC');  // ← Remove this
</script>
```

---

## Category Breakdown

| Category | Score | Issues |
|----------|-------|--------|
| Consent & Privacy | 45 | No consent mechanism, analytics fires before consent |
| Tag Configuration | 30 | Double GA4, hardcoded IDs |
| Data Quality | 60 | Missing parameters, inconsistent naming |
| E-commerce | 75 | Missing currency on 2 transactions |
| SPA Tracking | 90 | Working well |
| Performance | 85 | Good |

---

## Recommended Action Plan

### Week 1: Critical Fixes (4 hours)

- [ ] Remove duplicate GA4 tag
- [ ] Implement consent mode v2
- [ ] Test in GTM preview mode
- [ ] Verify metrics return to expected levels

### Week 2: Data Quality (6 hours)

- [ ] Standardize event naming to snake_case
- [ ] Add missing e-commerce parameters
- [ ] Create GTM variables for dynamic values
- [ ] Document implementation

### Week 3: Optimization (4 hours)

- [ ] Set up cross-domain tracking
- [ ] Configure referral exclusions
- [ ] Add user_id for logged-in tracking
- [ ] Implement enhanced measurement

---

## Appendix: Full Findings

[Full list of all 23 findings...]
```

---

## Acceptance Criteria

- [ ] Can detect 7+ categories of analytics issues
- [ ] Scoring algorithm produces 0-100 score with letter grade
- [ ] CLI supports audit command with multiple output formats
- [ ] MCP tools for audit, blueprint comparison, action plans
- [ ] REST API with async audit jobs
- [ ] HTML/Markdown report generation with evidence
- [ ] Can crawl SPAs and detect virtual pageview issues
- [ ] E-commerce validation (transaction_id, currency, items)
- [ ] Consent mode v2 detection
- [ ] Action plan prioritized by impact/effort
- [ ] Tests for all detectors
- [ ] Documentation with common issues and fixes

---

## Related Documentation

- [GA4 Implementation Guide](https://support.google.com/analytics/answer/9304153)
- [Consent Mode v2](https://support.google.com/google-ads/answer/13528757)
- [GTM Best Practices](https://developers.google.com/tag-platform/tag-manager/web/best-practices)
- [E-commerce Schema](https://developers.google.com/analytics/devguides/collection/ga4/ecommerce)
