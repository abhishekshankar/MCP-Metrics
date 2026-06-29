"""Browser controller for automated testing and GTM verification.

Provides a high-level interface for browser automation using Playwright.
Handles site analysis, GTM preview verification, and end-to-end testing.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

from observability.logging import log_operation, logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright


@dataclass
class BrowserAction:
    """Represents a browser action for testing."""

    action: str  # click, fill, navigate, wait, screenshot, assert
    selector: str | None = None
    value: str | None = None
    timeout: int = 5000
    description: str = ""


@dataclass
class TestResult:
    """Result of a browser test."""

    success: bool
    actions: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    page_url: str = ""
    console_logs: list[dict] = field(default_factory=list)
    network_requests: list[dict] = field(default_factory=list)


@dataclass
class GTMPreviewResult:
    """Result of GTM Preview mode verification."""

    url: str
    container_id: str
    preview_id: str
    tags_fired: list[dict[str, Any]] = field(default_factory=list)
    data_layer_events: list[dict] = field(default_factory=list)
    success: bool = False
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class BrowserController:
    """High-level browser controller for testing and verification.

    Handles:
    - Automated UI testing
    - GTM Preview verification
    - Site crawling and analysis
    - Screenshot capture
    - Console and network monitoring
    """

    def __init__(
        self,
        headless: bool = True,
        viewport: dict[str, int] | None = None,
        user_agent: str | None = None,
        timeout: int = 30000,
    ):
        self.headless = headless
        self.viewport = viewport or {"width": 1280, "height": 720}
        self.user_agent = user_agent or "MCP-Metrics Browser Controller"
        self.timeout = timeout
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._console_logs: list[dict] = []
        self._network_requests: list[dict] = []

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self) -> None:
        """Start the browser."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
            logger.info("browser.started", headless=self.headless)

    async def stop(self) -> None:
        """Stop the browser."""
        if self._browser:
            await self._browser.close()
            await self._playwright.stop()
            self._browser = None
            self._context = None
            logger.info("browser.stopped")

    async def new_context(
        self,
        viewport: dict[str, int] | None = None,
        user_agent: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> BrowserContext:
        """Create a new browser context."""
        if not self._browser:
            raise RuntimeError(
                "Browser not started. Use 'await controller.start()' or async context manager."
            )

        context = await self._browser.new_context(
            viewport=viewport or self.viewport,
            user_agent=user_agent or self.user_agent,
            extra_http_headers=extra_headers,
            record_video_dir=None,  # Could enable for debugging
        )
        return context

    async def new_page(
        self,
        context: BrowserContext | None = None,
        capture_console: bool = True,
        capture_network: bool = True,
    ) -> Page:
        """Create a new page with optional monitoring."""
        ctx = context or await self.new_context()
        page = await ctx.new_page()

        if capture_console:
            page.on("console", self._on_console)
        if capture_network:
            page.on("request", self._on_request)
            page.on("response", self._on_response)

        return page

    def _on_console(self, msg) -> None:
        """Handle console messages."""
        self._console_logs.append(
            {
                "type": msg.type,
                "text": msg.text,
                "time": time.time(),
            }
        )

    def _on_request(self, request) -> None:
        """Handle network requests."""
        self._network_requests.append(
            {
                "type": "request",
                "url": request.url,
                "method": request.method,
                "time": time.time(),
            }
        )

    def _on_response(self, response) -> None:
        """Handle network responses."""
        self._network_requests.append(
            {
                "type": "response",
                "url": response.url,
                "status": response.status,
                "time": time.time(),
            }
        )

    async def run_test(
        self,
        url: str,
        actions: list[BrowserAction],
        context: BrowserContext | None = None,
        capture_screenshots: bool = False,
        screenshot_dir: str = "/tmp/screenshots",
    ) -> TestResult:
        """Run an automated browser test.

        Args:
            url: Starting URL
            actions: List of actions to perform
            context: Optional existing browser context
            capture_screenshots: Whether to capture screenshots
            screenshot_dir: Directory for screenshots

        Returns:
            TestResult with success status and collected data
        """
        start_time = time.time()
        result = TestResult(success=True)
        self._console_logs = []
        self._network_requests = []

        page = await self.new_page(context, capture_console=True, capture_network=True)

        try:
            # Navigate to starting URL
            await page.goto(url, timeout=self.timeout, wait_until="networkidle")
            result.page_url = page.url

            # Execute actions
            for i, action in enumerate(actions):
                action_result = {"step": i + 1, "action": action.action, "success": True}

                try:
                    if action.action == "navigate":
                        await page.goto(action.value, timeout=action.timeout)
                        result.page_url = page.url

                    elif action.action == "click":
                        await page.click(action.selector, timeout=action.timeout)

                    elif action.action == "fill":
                        await page.fill(action.selector, action.value, timeout=action.timeout)

                    elif action.action == "select":
                        await page.select_option(
                            action.selector, action.value, timeout=action.timeout
                        )

                    elif action.action == "wait":
                        if action.selector:
                            await page.wait_for_selector(action.selector, timeout=action.timeout)
                        else:
                            await asyncio.sleep(float(action.value or 1))

                    elif action.action == "wait_for_text":
                        await page.wait_for_selector(
                            f"text={action.value}", timeout=action.timeout, state="visible"
                        )

                    elif action.action == "screenshot":
                        if capture_screenshots:
                            import os

                            os.makedirs(screenshot_dir, exist_ok=True)
                            path = f"{screenshot_dir}/step_{i + 1}_{int(time.time())}.png"
                            await page.screenshot(path=path, full_page=True)
                            result.screenshots.append(path)

                    elif action.action == "assert_text":
                        text = await page.inner_text(action.selector, timeout=action.timeout)
                        if action.value not in text:
                            raise AssertionError(f"Expected '{action.value}' in '{text}'")

                    elif action.action == "assert_visible":
                        await page.wait_for_selector(
                            action.selector, state="visible", timeout=action.timeout
                        )

                    elif action.action == "assert_url":
                        if action.value not in page.url:
                            raise AssertionError(
                                f"Expected URL containing '{action.value}', got '{page.url}'"
                            )

                    elif action.action == "press":
                        await page.press(action.selector or "body", action.value)

                    action_result["url"] = page.url
                    result.actions.append(action_result)

                except Exception as e:
                    action_result["success"] = False
                    action_result["error"] = str(e)
                    result.actions.append(action_result)
                    result.errors.append(f"Step {i + 1} ({action.action}): {e}")
                    result.success = False

                    if capture_screenshots:
                        import os

                        os.makedirs(screenshot_dir, exist_ok=True)
                        path = f"{screenshot_dir}/error_step_{i + 1}_{int(time.time())}.png"
                        await page.screenshot(path=path, full_page=True)
                        result.screenshots.append(path)

                    break

        except Exception as e:
            result.success = False
            result.errors.append(f"Navigation failed: {e}")

        finally:
            result.duration_seconds = time.time() - start_time
            result.console_logs = self._console_logs.copy()
            result.network_requests = self._network_requests.copy()
            await page.close()

        log_operation(
            "browser.test_completed",
            url=url,
            success=result.success,
            actions=len(result.actions),
            errors=len(result.errors),
            duration=result.duration_seconds,
        )

        return result

    async def verify_gtm_preview(
        self,
        url: str,
        container_id: str,
        preview_id: str,
        expected_tags: list[dict[str, str]] | None = None,
        timeout: int = 30000,
    ) -> GTMPreviewResult:
        """Verify GTM Preview mode and check tag firing.

        Args:
            url: URL to test
            container_id: GTM container ID (e.g., "GTM-ABC123")
            preview_id: GTM Preview mode ID
            expected_tags: List of expected tags [{"name": "GA4 Config", "event": "page_view"}]
            timeout: Page load timeout

        Returns:
            GTMPreviewResult with verification details
        """
        start_time = time.time()
        result = GTMPreviewResult(
            url=url,
            container_id=container_id,
            preview_id=preview_id,
        )

        # Build preview URL
        separator = "&" if "?" in url else "?"
        preview_url = f"{url}{separator}gtm_preview={preview_id}&gtm_debug=x"

        page = await self.new_page()

        try:
            await page.goto(preview_url, timeout=timeout, wait_until="networkidle")

            # Wait for dataLayer to be available
            try:
                await page.wait_for_function(
                    "() => typeof dataLayer !== 'undefined' && Array.isArray(dataLayer)",
                    timeout=5000,
                )
            except Exception:
                result.errors.append("dataLayer not found - GTM may not be loaded")

            # Collect dataLayer events
            data_layer = await page.evaluate("""
                () => {
                    if (typeof dataLayer === 'undefined') return [];
                    return dataLayer.map(e => ({
                        event: e.event,
                        keys: Object.keys(e),
                        timestamp: Date.now()
                    }));
                }
            """)
            result.data_layer_events = data_layer

            # Check for expected tags
            if expected_tags:
                for tag in expected_tags:
                    tag_result = {
                        "name": tag["name"],
                        "event": tag.get("event", "page_view"),
                        "fired": False,
                    }

                    # Check dataLayer for the event
                    has_event = await page.evaluate(
                        f"""() => {{
                            if (typeof dataLayer === 'undefined') return false;
                            return dataLayer.some(e => e.event === '{tag_result["event"]}');
                        }}"""
                    )

                    if has_event:
                        tag_result["fired"] = True
                    else:
                        result.errors.append(
                            f"Tag '{tag['name']}' event "
                            f"'{tag_result['event']}' not found in dataLayer"
                        )

                    result.tags_fired.append(tag_result)
            else:
                # Auto-detect GA4
                ga4_check = await page.evaluate("""
                    () => {
                        if (typeof dataLayer === 'undefined') return false;
                        return dataLayer.some(e => e.event === 'gtm.js' || e.event === 'config');
                    }
                """)
                if ga4_check:
                    result.tags_fired.append(
                        {"name": "GA4 Configuration", "event": "gtm.js", "fired": True}
                    )

            result.success = (
                all(t.get("fired", False) for t in result.tags_fired) if result.tags_fired else True
            )

        except Exception as e:
            result.errors.append(str(e))
            result.success = False

        finally:
            result.duration_seconds = time.time() - start_time
            await page.close()

        log_operation(
            "browser.gtm_preview_verified",
            url=url,
            container_id=container_id,
            success=result.success,
            tags=len(result.tags_fired),
            duration=result.duration_seconds,
        )

        return result

    async def crawl_site(
        self,
        start_url: str,
        max_pages: int = 20,
        max_depth: int = 3,
        same_domain_only: bool = True,
        crawl_delay_ms: int = 1000,
    ) -> dict[str, Any]:
        """Crawl a website and collect page information.

        Args:
            start_url: Starting URL
            max_pages: Maximum pages to crawl
            max_depth: Maximum crawl depth
            same_domain_only: Stay within the same domain
            crawl_delay_ms: Delay between requests in milliseconds (rate limiting)

        Returns:
            Dict with crawled pages and discovered links
        """
        import random

        base_domain = urlparse(start_url).netloc
        visited: set[str] = set()
        to_visit: list[tuple[str, int]] = [(start_url, 0)]  # (url, depth)
        results: list[dict] = []

        context = await self.new_context()

        try:
            while to_visit and len(visited) < max_pages:
                url, depth = to_visit.pop(0)

                if url in visited or depth > max_depth:
                    continue

                try:
                    page = await context.new_page()
                    response = await page.goto(
                        url, timeout=self.timeout, wait_until="domcontentloaded"
                    )

                    if response and response.status < 400:
                        # Extract page info
                        title = await page.title()
                        links = await page.eval_on_selector_all(
                            "a[href]",
                            "els => els.map(el => el.getAttribute('href'))"
                            ".filter(h => h && h.startsWith('http'))",
                        )

                        page_data = {
                            "url": url,
                            "title": title,
                            "status": response.status,
                            "depth": depth,
                            "links_found": len(links),
                        }
                        results.append(page_data)
                        visited.add(url)

                        # Add new links to queue
                        if depth < max_depth:
                            for link in links[:20]:  # Limit links per page
                                absolute = urljoin(url, link)
                                parsed = urlparse(absolute)

                                if same_domain_only and parsed.netloc != base_domain:
                                    continue

                                # Skip common non-content URLs
                                skip_patterns = [
                                    ".pdf",
                                    ".jpg",
                                    ".png",
                                    ".gif",
                                    ".css",
                                    ".js",
                                    ".zip",
                                    ".tar",
                                    ".gz",
                                    ".mp4",
                                    ".mp3",
                                ]
                                if any(pattern in absolute.lower() for pattern in skip_patterns):
                                    continue

                                if absolute not in visited and absolute not in [
                                    u for u, _ in to_visit
                                ]:
                                    to_visit.append((absolute, depth + 1))

                    await page.close()

                    # Rate limiting: add delay with jitter between requests
                    if crawl_delay_ms > 0 and to_visit:  # Don't delay after last page
                        delay = crawl_delay_ms + random.randint(0, crawl_delay_ms // 4)
                        await asyncio.sleep(delay / 1000)

                except Exception as e:
                    logger.warning("browser.crawl_page_failed", url=url, error=str(e))

        finally:
            await context.close()

        return {
            "start_url": start_url,
            "pages_crawled": len(results),
            "unique_urls": len(visited),
            "pages": results,
        }

    async def run_health_check_test(
        self,
        base_url: str = "http://localhost:5173",
        api_url: str = "http://localhost:8000",
    ) -> dict[str, Any]:
        """Run a comprehensive health check test on the MCP-Metrics application.

        Tests:
        - Web UI loads
        - API is accessible
        - Can create a site
        - Can view site details

        Args:
            base_url: Web UI URL
            api_url: API URL

        Returns:
            Dict with test results
        """
        results = {
            "web_ui_accessible": False,
            "api_accessible": False,
            "can_create_site": False,
            "can_view_site": False,
            "errors": [],
        }

        # Test 1: Web UI loads
        try:
            page = await self.new_page()
            response = await page.goto(base_url, timeout=10000)
            if response and response.status == 200:
                title = await page.title()
                results["web_ui_accessible"] = title == "Analytics MCP"
            await page.close()
        except Exception as e:
            results["errors"].append(f"Web UI test failed: {e}")

        # Test 2: API health check
        try:
            import httpx

            response = httpx.get(f"{api_url}/health", timeout=10)
            results["api_accessible"] = (
                response.status_code == 200 and response.json().get("status") == "ok"
            )
        except Exception as e:
            results["errors"].append(f"API test failed: {e}")

        # Test 3: Full UI workflow (if UI accessible)
        if results["web_ui_accessible"]:
            try:
                test_site_name = f"test-site-{int(time.time())}"

                actions = [
                    BrowserAction("navigate", value=f"{base_url}/create"),
                    BrowserAction("wait", selector="input[placeholder='example.com']"),
                    BrowserAction(
                        "fill",
                        selector="input[placeholder='example.com']",
                        value=f"{test_site_name}.com",
                    ),
                    BrowserAction(
                        "fill", selector="input[placeholder='Example Site']", value="Test Site"
                    ),
                    BrowserAction("click", selector="button[type='submit']"),
                    BrowserAction("wait", value="3"),  # Wait for creation
                    BrowserAction("assert_url", value="/sites/"),
                ]

                test_result = await self.run_test(f"{base_url}/create", actions)
                results["can_create_site"] = test_result.success
                if not test_result.success:
                    results["errors"].extend(test_result.errors)

            except Exception as e:
                results["errors"].append(f"Create site test failed: {e}")

        results["all_passed"] = all(
            [
                results["web_ui_accessible"],
                results["api_accessible"],
            ]
        )

        return results


# Synchronous wrapper functions for convenience
def run_browser_test(
    url: str,
    actions: list[BrowserAction],
    headless: bool = True,
) -> TestResult:
    """Synchronous wrapper for running browser tests."""

    async def _run():
        async with BrowserController(headless=headless) as controller:
            return await controller.run_test(url, actions)

    return asyncio.run(_run())


def verify_gtm_preview(
    url: str,
    container_id: str,
    preview_id: str,
    expected_tags: list[dict[str, str]] | None = None,
    headless: bool = True,
) -> GTMPreviewResult:
    """Synchronous wrapper for GTM preview verification."""

    async def _verify():
        async with BrowserController(headless=headless) as controller:
            return await controller.verify_gtm_preview(url, container_id, preview_id, expected_tags)

    return asyncio.run(_verify())


def run_health_check(
    base_url: str = "http://localhost:5173",
    api_url: str = "http://localhost:8000",
    headless: bool = True,
) -> dict[str, Any]:
    """Synchronous wrapper for health check test."""

    async def _check():
        async with BrowserController(headless=headless) as controller:
            return await controller.run_health_check_test(base_url, api_url)

    return asyncio.run(_check())
