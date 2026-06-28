"""Site analyzer for automated page discovery and business intent grouping.

Uses Playwright for browser-based site crawling and analysis.
Similar to jtrackingai's tracking-discover functionality.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright

from observability.logging import log_failure, log_operation


@dataclass
class PageAnalysis:
    """Analysis result for a single page."""

    url: str
    title: str = ""
    meta_description: str = ""
    headings: list[str] = field(default_factory=list)
    buttons: list[dict] = field(default_factory=list)
    forms: list[dict] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    structured_data: list[dict] = field(default_factory=list)
    business_purpose: str = ""  # e.g., "homepage", "product", "checkout", "content"
    tracking_potential: list[str] = field(default_factory=list)  # e.g., ["purchase", "signup", "contact"]


@dataclass
class SiteAnalysis:
    """Complete site analysis result."""

    base_url: str
    pages: list[PageAnalysis] = field(default_factory=list)
    page_groups: dict[str, list[str]] = field(default_factory=dict)  # business_purpose -> urls
    total_pages: int = 0
    crawl_duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)


class SiteAnalyzer:
    """Analyze websites to discover pages and business intent.

    Uses Playwright for headless browser automation.
    """

    def __init__(
        self,
        max_pages: int = 50,
        crawl_depth: int = 3,
        respect_robots_txt: bool = True,
        headless: bool = True,
    ):
        self.max_pages = max_pages
        self.crawl_depth = crawl_depth
        self.respect_robots_txt = respect_robots_txt
        self.headless = headless
        self.visited_urls: set[str] = set()

    async def analyze_site(self, url: str) -> SiteAnalysis:
        """Crawl and analyze an entire website.

        Args:
            url: Starting URL (homepage recommended)

        Returns:
            SiteAnalysis with discovered pages and groupings
        """
        import time

        start_time = time.time()
        base_url = self._normalize_url(url)
        analysis = SiteAnalysis(base_url=base_url)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    user_agent="MCP-Metrics Site Analyzer Bot"
                )

                try:
                    # BFS crawl
                    urls_to_crawl = [(base_url, 0)]  # (url, depth)

                    while urls_to_crawl and len(self.visited_urls) < self.max_pages:
                        current_url, depth = urls_to_crawl.pop(0)

                        if current_url in self.visited_urls or depth > self.crawl_depth:
                            continue

                        page_analysis = await self._analyze_page(context, current_url)
                        if page_analysis:
                            analysis.pages.append(page_analysis)
                            self.visited_urls.add(current_url)

                            # Extract links for further crawling
                            if depth < self.crawl_depth:
                                for link in page_analysis.links[:20]:  # Limit links per page
                                    absolute_url = urljoin(current_url, link)
                                    if self._should_crawl(absolute_url, base_url):
                                        urls_to_crawl.append((absolute_url, depth + 1))

                finally:
                    await browser.close()

        except Exception as e:
            log_failure("site_analyzer.crawl_failed", error=str(e), url=url)
            analysis.errors.append(str(e))

        analysis.total_pages = len(analysis.pages)
        analysis.crawl_duration_seconds = time.time() - start_time

        # Group pages by business purpose
        analysis.page_groups = self._group_pages(analysis.pages)

        log_operation(
            "site_analyzer.complete",
            url=url,
            pages_found=analysis.total_pages,
            duration=analysis.crawl_duration_seconds,
        )

        return analysis

    async def _analyze_page(self, context, url: str) -> PageAnalysis | None:
        """Analyze a single page."""
        page = await context.new_page()

        try:
            response = await page.goto(url, wait_until="networkidle", timeout=30000)

            if not response or response.status >= 400:
                return None

            # Extract page data
            title = await page.title()

            # Meta description
            meta_desc = await page.eval_on_selector(
                'meta[name="description"]',
                "el => el?.content || ''"
            )

            # Headings
            headings = await page.eval_on_selector_all(
                "h1, h2, h3",
                "els => els.map(el => el.textContent.trim()).filter(t => t)"
            )

            # Buttons with tracking potential
            buttons = await page.eval_on_selector_all(
                "button, a.btn, .btn, [role='button']",
                """els => els.map(el => ({
                    text: el.textContent.trim().substring(0, 50),
                    selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ')[0] : ''),
                    type: el.type || 'button',
                    href: el.href || null
                })).filter(b => b.text)"""
            )

            # Forms
            forms = await page.eval_on_selector_all(
                "form",
                """els => els.map(el => ({
                    action: el.action || null,
                    method: el.method || 'get',
                    inputs: Array.from(el.querySelectorAll('input, select, textarea')).map(i => ({
                        name: i.name,
                        type: i.type || i.tagName.toLowerCase(),
                        required: i.required
                    }))
                }))"""
            )

            # Links
            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(el => el.getAttribute('href')).filter(h => h && !h.startsWith('#') && !h.startsWith('javascript:'))"
            )

            # Images
            images = await page.eval_on_selector_all(
                "img",
                """els => els.map(el => ({
                    src: el.src,
                    alt: el.alt,
                    width: el.naturalWidth,
                    height: el.naturalHeight
                })).filter(i => i.src)"""
            )

            # Structured data
            structured_data = await page.eval_on_selector_all(
                'script[type="application/ld+json"]',
                "els => els.map(el => { try { return JSON.parse(el.textContent); } catch { return null; } }).filter(Boolean)"
            )

            analysis = PageAnalysis(
                url=url,
                title=title,
                meta_description=meta_desc,
                headings=headings[:10],  # Limit
                buttons=buttons[:20],
                forms=forms[:5],
                links=list(set(links))[:50],  # Deduplicate and limit
                images=images[:20],
                structured_data=structured_data[:5],
            )

            # Determine business purpose
            analysis.business_purpose = self._classify_page_purpose(analysis)
            analysis.tracking_potential = self._identify_tracking_opportunities(analysis)

            return analysis

        except Exception as e:
            log_failure("site_analyzer.page_failed", error=str(e), url=url)
            return None

        finally:
            await page.close()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"

    def _should_crawl(self, url: str, base_url: str) -> bool:
        """Check if URL should be crawled."""
        parsed = urlparse(url)
        base_parsed = urlparse(base_url)

        # Same domain only
        if parsed.netloc != base_parsed.netloc:
            return False

        # Skip common non-content URLs
        skip_patterns = [
            ".pdf", ".jpg", ".png", ".gif", ".css", ".js",
            "/wp-admin", "/wp-includes", "/admin", "/api/",
            "?", "/tag/", "/author/", "/search",
        ]
        if any(pattern in url.lower() for pattern in skip_patterns):
            return False

        return True

    def _classify_page_purpose(self, page: PageAnalysis) -> str:
        """Classify page by business purpose using heuristics."""
        url_lower = page.url.lower()
        title_lower = page.title.lower()

        # E-commerce patterns
        if any(x in url_lower for x in ["/cart", "/checkout", "/basket"]):
            return "checkout"
        if any(x in url_lower for x in ["/product", "/item", "/p/", "/shop/"]):
            return "product"
        if "/collection" in url_lower or "/category" in url_lower:
            return "category"

        # Content patterns
        if any(x in url_lower for x in ["/blog", "/article", "/post", "/news/"]):
            return "content"

        # Conversion patterns
        if any(x in url_lower for x in ["/contact", "/signup", "/register", "/demo"]):
            return "conversion"
        if any(x in url_lower for x in ["/pricing", "/plans", "/subscribe"]):
            return "pricing"

        # Homepage
        if url_lower.rstrip("/") == urlparse(page.url).netloc or url_lower.endswith("/") and url_lower.count("/") <= 3:
            if "home" in title_lower or len(page.url.split("/")) <= 4:
                return "homepage"

        # About/Support
        if any(x in url_lower for x in ["/about", "/company", "/team"]):
            return "about"
        if any(x in url_lower for x in ["/help", "/support", "/faq", "/docs"]):
            return "support"

        return "other"

    def _identify_tracking_opportunities(self, page: PageAnalysis) -> list[str]:
        """Identify potential tracking events based on page elements."""
        opportunities = []

        # Check for e-commerce
        if page.business_purpose in ["product", "category"]:
            opportunities.extend(["view_item", "add_to_cart"])
        if page.business_purpose == "checkout":
            opportunities.extend(["begin_checkout", "purchase"])

        # Check for forms
        for form in page.forms:
            if any(inp.get("type") == "email" for inp in form.get("inputs", [])):
                opportunities.append("signup" if "signup" in page.url.lower() else "lead_form")
            if any(inp.get("name", "").lower() in ["search", "q", "query"] for inp in form.get("inputs", [])):
                opportunities.append("search")

        # Check for CTAs
        button_texts = " ".join([b.get("text", "").lower() for b in page.buttons])
        if any(x in button_texts for x in ["buy", "purchase", "order", "checkout"]):
            opportunities.append("purchase_intent")
        if any(x in button_texts for x in ["sign up", "register", "create account", "join"]):
            opportunities.append("signup")
        if any(x in button_texts for x in ["demo", "schedule", "book", "request"]):
            opportunities.append("demo_request")
        if any(x in button_texts for x in ["download", "get", "free"]):
            opportunities.append("download")
        if any(x in button_texts for x in ["contact", "message", "email us"]):
            opportunities.append("contact")

        # Check for video
        if any(x in page.url.lower() for x in ["/video", "/watch", "/tutorial"]):
            opportunities.append("video_engagement")

        return list(set(opportunities))

    def _group_pages(self, pages: list[PageAnalysis]) -> dict[str, list[str]]:
        """Group pages by business purpose."""
        groups: dict[str, list[str]] = {}

        for page in pages:
            purpose = page.business_purpose
            if purpose not in groups:
                groups[purpose] = []
            groups[purpose].append(page.url)

        return groups

    async def analyze_single_page(self, url: str) -> PageAnalysis | None:
        """Analyze just a single page (no crawling).

        Useful for quick analysis of a specific URL.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()

            try:
                result = await self._analyze_page(context, url)
                return result
            finally:
                await browser.close()


def analyze_site_sync(url: str, max_pages: int = 50) -> SiteAnalysis:
    """Synchronous wrapper for site analysis."""
    analyzer = SiteAnalyzer(max_pages=max_pages)
    return asyncio.run(analyzer.analyze_site(url))
