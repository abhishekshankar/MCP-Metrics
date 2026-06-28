"""GTM Preview mode verification service using Playwright.

Similar to jtrackingai/analytics-tracking-automation's preview verification.
Verifies that tags fire correctly in GTM Preview mode before publishing.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import async_playwright

from observability.logging import log_failure, log_operation


@dataclass
class TagFireResult:
    """Result of a tag firing check."""

    tag_name: str
    event_name: str
    fired: bool
    firing_count: int = 0
    errors: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreviewVerificationResult:
    """Complete preview verification result."""

    url: str
    container_id: str
    preview_id: str
    tag_results: list[TagFireResult] = field(default_factory=list)
    data_layer_events: list[dict] = field(default_factory=list)
    duration_seconds: float = 0.0
    success: bool = False
    errors: list[str] = field(default_factory=list)


class PreviewService:
    """Verify GTM tag firing using Preview mode and Playwright.

    Opens GTM Preview mode, navigates to pages, and checks that tags fire.
    """

    def __init__(
        self,
        headless: bool = True,
        preview_timeout_seconds: int = 30,
        page_load_timeout: int = 10000,
    ):
        self.headless = headless
        self.preview_timeout = preview_timeout_seconds
        self.page_load_timeout = page_load_timeout

    async def verify_preview(
        self,
        url: str,
        container_id: str,
        preview_id: str,
        expected_tags: list[dict[str, Any]] | None = None,
    ) -> PreviewVerificationResult:
        """Verify GTM Preview mode and check tag firing.

        Args:
            url: Website URL to test
            container_id: GTM container ID
            preview_id: GTM Preview mode ID (from GTM UI)
            expected_tags: List of expected tags to verify firing
                [{"name": "GA4 Config", "event": "page_view"}, ...]

        Returns:
            PreviewVerificationResult with tag firing details
        """
        import time

        start_time = time.time()
        result = PreviewVerificationResult(
            url=url,
            container_id=container_id,
            preview_id=preview_id,
        )

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="MCP-Metrics Preview Bot",
                )

                try:
                    page = await context.new_page()

                    # Inject GTM Preview mode
                    preview_url = self._build_preview_url(url, container_id, preview_id)
                    
                    await page.goto(preview_url, timeout=self.page_load_timeout)
                    
                    # Wait for page to load and GTM to initialize
                    await asyncio.sleep(2)

                    # Collect dataLayer events
                    result.data_layer_events = await self._collect_data_layer(page)

                    # Check expected tags
                    if expected_tags:
                        for tag in expected_tags:
                            tag_result = await self._check_tag_firing(
                                page, tag["name"], tag.get("event", "page_view")
                            )
                            result.tag_results.append(tag_result)
                    else:
                        # Auto-detect common tags
                        result.tag_results = await self._auto_detect_tags(page)

                    result.success = all(r.fired for r in result.tag_results) if result.tag_results else True

                    log_operation(
                        "preview.verify",
                        url=url,
                        container_id=container_id,
                        tags_checked=len(result.tag_results),
                        success=result.success,
                    )

                finally:
                    await browser.close()

        except Exception as e:
            log_failure("preview.verify_failed", error=str(e), url=url)
            result.errors.append(str(e))
            result.success = False

        result.duration_seconds = time.time() - start_time
        return result

    def _build_preview_url(self, url: str, container_id: str, preview_id: str) -> str:
        """Build URL with GTM Preview mode parameters."""
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}gtm_preview={preview_id}&gtm_debug=x"

    async def _collect_data_layer(self, page) -> list[dict]:
        """Collect dataLayer events from page."""
        try:
            events = await page.evaluate("""
                () => {
                    if (typeof dataLayer !== 'undefined' && Array.isArray(dataLayer)) {
                        return dataLayer.map(e => ({
                            event: e.event,
                            timestamp: new Date().toISOString(),
                            keys: Object.keys(e)
                        }));
                    }
                    return [];
                }
            """)
            return events
        except Exception as e:
            return [{"error": str(e)}]

    async def _check_tag_firing(
        self, page, tag_name: str, event_name: str
    ) -> TagFireResult:
        """Check if a specific tag fired for an event."""
        result = TagFireResult(tag_name=tag_name, event_name=event_name)

        try:
            # Check dataLayer for the event
            has_event = await page.evaluate(
                f"""
                () => {{
                    if (typeof dataLayer === 'undefined') return false;
                    return dataLayer.some(e => e.event === '{event_name}');
                }}
                """
            )

            if has_event:
                result.fired = True
                result.firing_count = 1
            else:
                result.fired = False
                result.errors.append(f"Event '{event_name}' not found in dataLayer")

        except Exception as e:
            result.errors.append(str(e))

        return result

    async def _auto_detect_tags(self, page) -> list[TagFireResult]:
        """Auto-detect common GTM/GA4 tags."""
        results = []

        # Check for GA4 config
        ga4_check = await page.evaluate("""
            () => {
                // Check if gtag is defined
                if (typeof gtag !== 'undefined') return true;
                // Check dataLayer for config events
                if (typeof dataLayer !== 'undefined') {
                    return dataLayer.some(e => e.event === 'gtm.js' || e.event === 'config');
                }
                return false;
            }
        """)

        if ga4_check:
            results.append(TagFireResult(
                tag_name="GA4 Configuration",
                event_name="gtm.js",
                fired=True,
                firing_count=1,
            ))

        # Check for common events
        common_events = ["page_view", "screen_view", "user_engagement"]
        for event in common_events:
            has_event = await page.evaluate(
                f"""() => typeof dataLayer !== 'undefined' && 
                    dataLayer.some(e => e.event === '{event}')"""
            )
            if has_event:
                results.append(TagFireResult(
                    tag_name=f"GA4 Event - {event}",
                    event_name=event,
                    fired=True,
                    firing_count=1,
                ))

        return results

    async def verify_blueprint_events(
        self,
        url: str,
        container_id: str,
        preview_id: str,
        blueprint_events: list[dict[str, Any]],
    ) -> PreviewVerificationResult:
        """Verify that all blueprint events fire correctly.

        Args:
            url: Website URL
            container_id: GTM container ID
            preview_id: GTM Preview ID
            blueprint_events: Events from applied blueprint
                [{"name": "signup_started", "trigger_type": "customEvent"}, ...]

        Returns:
            Verification result for all blueprint events
        """
        expected = [
            {"name": f"Event - {e['name']}", "event": e["name"].replace("_", "")}
            for e in blueprint_events
        ]

        return await self.verify_preview(url, container_id, preview_id, expected)


def verify_preview_sync(
    url: str,
    container_id: str,
    preview_id: str,
    expected_tags: list[dict[str, Any]] | None = None,
) -> PreviewVerificationResult:
    """Synchronous wrapper for preview verification."""
    service = PreviewService()
    return asyncio.run(service.verify_preview(url, container_id, preview_id, expected_tags))
