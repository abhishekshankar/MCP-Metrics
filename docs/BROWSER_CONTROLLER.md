# Browser Controller

A comprehensive Playwright-based browser automation system for MCP-Metrics. Handles automated testing, GTM preview verification, site crawling, and end-to-end UI testing.

## Features

- **Automated UI Testing**: Define test scenarios with actions (click, fill, assert, etc.)
- **GTM Preview Verification**: Verify tags fire correctly in GTM Preview mode
- **Site Crawling**: Discover and map website structure
- **Console & Network Monitoring**: Capture browser events during testing
- **Screenshot Capture**: Document test results visually
- **MCP Tool Integration**: Use via Claude Code MCP tools

## Quick Start

### Python API

```python
from services.browser_controller import (
    BrowserController,
    BrowserAction,
    run_browser_test,
)

# Async API
async with BrowserController(headless=True) as controller:
    actions = [
        BrowserAction("navigate", value="https://example.com"),
        BrowserAction("click", selector="#login-btn"),
        BrowserAction("fill", selector="#email", value="user@example.com"),
        BrowserAction("fill", selector="#password", value="secret"),
        BrowserAction("click", selector="#submit"),
        BrowserAction("assert_visible", selector=".dashboard"),
    ]

    result = await controller.run_test("https://example.com", actions)
    print(f"Test passed: {result.success}")

# Sync API
result = run_browser_test(
    "https://example.com",
    [
        BrowserAction("navigate", value="https://example.com"),
        BrowserAction("assert_text", selector="h1", value="Welcome"),
    ],
)
```

### MCP Tools

When using MCP-Metrics as an MCP server, these browser tools are available:

#### `run_browser_test`

Run automated browser tests with a sequence of actions.

```json
{
  "url": "https://example.com/login",
  "actions": [
    {"action": "fill", "selector": "#email", "value": "user@example.com"},
    {"action": "fill", "selector": "#password", "value": "secret"},
    {"action": "click", "selector": "#login-btn"},
    {"action": "assert_visible", "selector": ".dashboard"}
  ],
  "headless": true,
  "capture_screenshots": false
}
```

**Actions:**
- `navigate` - Go to a URL (set `value` to URL)
- `click` - Click an element (set `selector`)
- `fill` - Fill an input (set `selector` and `value`)
- `select` - Select from dropdown (set `selector` and `value`)
- `wait` - Wait (set `selector` for element, or `value` for seconds)
- `assert_text` - Check element contains text (set `selector` and `value`)
- `assert_visible` - Check element is visible (set `selector`)
- `assert_url` - Check URL contains text (set `value`)
- `screenshot` - Capture screenshot (requires `capture_screenshots=true`)
- `press` - Press a key (set `value` to key name)

#### `test_mcp_metrics_app`

Test the MCP-Metrics application automatically.

```json
{
  "web_ui_url": "http://localhost:5173",
  "api_url": "http://localhost:8000",
  "headless": true
}
```

**Returns:**
- `web_ui_accessible`: Whether Web UI loads
- `api_accessible`: Whether API responds
- `can_create_site`: Whether site creation works
- `can_view_site`: Whether site viewing works
- `errors`: List of any errors

#### `create_site_via_ui`

Create a site using the Web UI via browser automation.

```json
{
  "domain": "test.example.com",
  "name": "Test Site",
  "web_ui_url": "http://localhost:5173",
  "environment": "prod",
  "blueprint": "saas",
  "headless": true
}
```

#### `browser_gtm_preview_test`

Test GTM Preview mode in a real browser.

```json
{
  "url": "https://example.com",
  "container_id": "GTM-ABC123",
  "preview_id": "PREVIEW-1",
  "expected_tags": [
    {"name": "GA4 Config", "event": "page_view"},
    {"name": "Purchase Tag", "event": "purchase"}
  ],
  "headless": true
}
```

**Returns:**
- `success`: Whether all expected tags fired
- `tags_fired`: List of tags with firing status
- `data_layer_events`: All dataLayer events captured
- `errors`: Any errors during verification

#### `crawl_website`

Crawl a website and discover pages.

```json
{
  "start_url": "https://example.com",
  "max_pages": 20,
  "max_depth": 3,
  "headless": true
}
```

**Returns:**
- `pages_crawled`: Number of pages discovered
- `unique_urls`: Number of unique URLs
- `pages`: List of page info (URL, title, status)

## Examples

### End-to-End Site Creation Test

```python
from services.browser_controller import run_browser_test, BrowserAction

# Test creating a site through the UI
result = run_browser_test(
    "http://localhost:5173/create",
    [
        BrowserAction("navigate", value="http://localhost:5173/create"),
        BrowserAction("fill", selector="input[placeholder='example.com']", value="test.com"),
        BrowserAction("fill", selector="input[placeholder='Example Site']", value="Test Site"),
        BrowserAction("select", selector="select", value="prod"),
        BrowserAction("click", selector="button[type='submit']"),
        BrowserAction("wait", value="5"),  # Wait for API calls
        BrowserAction("assert_url", value="/sites/test.com"),
    ],
    headless=True,
)

assert result.success, f"Test failed: {result.errors}"
```

### GTM Preview Verification

```python
from services.browser_controller import verify_gtm_preview

# Verify GTM tags fire correctly
result = verify_gtm_preview(
    url="https://example.com/checkout",
    container_id="GTM-ABC123",
    preview_id="PREVIEW-1",
    expected_tags=[
        {"name": "GA4 Config", "event": "page_view"},
        {"name": "Purchase", "event": "purchase"},
    ],
    headless=True,
)

if result.success:
    print("✓ All tags fired correctly")
    for tag in result.tags_fired:
        print(f"  - {tag['name']}: {'✓' if tag['fired'] else '✗'}")
else:
    print("✗ Some tags failed:")
    for error in result.errors:
        print(f"  - {error}")
```

### Site Crawling

```python
from services.browser_controller import BrowserController

async with BrowserController(headless=True) as controller:
    result = await controller.crawl_site(
        start_url="https://example.com",
        max_pages=50,
        max_depth=3,
    )

    print(f"Discovered {result['pages_crawled']} pages")
    for page in result['pages']:
        print(f"  - {page['title']}: {page['url']}")
```

### Health Check with Screenshots

```python
from services.browser_controller import run_browser_test, BrowserAction

# Test with screenshots on failure
result = run_browser_test(
    "http://localhost:5173",
    [
        BrowserAction("navigate", value="http://localhost:5173"),
        BrowserAction("assert_text", selector="h1", value="Sites Dashboard"),
        BrowserAction("screenshot"),
    ],
    headless=True,
    capture_screenshots=True,
)

if result.screenshots:
    print(f"Screenshots saved: {result.screenshots}")
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BrowserController                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   run_test   │  │ verify_gtm   │  │   crawl_site     │  │
│  │              │  │   _preview   │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Playwright                             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Chromium  │  │   Firefox    │  │     WebKit       │  │
│  │  (default) │  │  (optional)  │  │   (optional)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Browser Options

```python
from services.browser_controller import BrowserController

controller = BrowserController(
    headless=True,  # Run without visible window
    viewport={"width": 1280, "height": 720},
    user_agent="Custom Bot 1.0",
    timeout=30000,  # 30 second default timeout
)
```

### Environment Variables

```bash
# Playwright configuration
PLAYWRIGHT_BROWSERS_PATH=0  # Use system browsers
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1  # Skip download in CI

# Proxy configuration (if needed)
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

## Testing

Run browser controller tests:

```bash
cd backend
pytest tests/test_browser_controller.py -v
```

Tests include:
- Browser lifecycle (start/stop)
- Navigation and interactions
- Form filling and submission
- Error handling
- Screenshot capture
- GTM preview verification
- Site crawling
- Complex workflows

## Troubleshooting

### Browser Won't Start

```bash
# Install Playwright browsers
playwright install chromium

# Or install all browsers
playwright install
```

### Headless Mode Issues

```python
# Run headed (visible) for debugging
controller = BrowserController(headless=False)
```

### Timeout Errors

```python
# Increase timeout
controller = BrowserController(timeout=60000)  # 60 seconds

# Or per-action timeout
action = BrowserAction("click", selector="#slow-btn", timeout=10000)
```

### Screenshots Not Saving

```python
# Ensure directory exists and is writable
result = await controller.run_test(
    url,
    actions,
    capture_screenshots=True,
    screenshot_dir="/absolute/path/to/screenshots",
)
```

## Security Considerations

- **Headless mode**: Runs without GUI, faster but harder to debug
- **User Agent**: Can be customized to match real browsers
- **Isolation**: Each test gets a fresh browser context
- **Data URLs**: Tests use `data:` URLs to avoid external dependencies

## Integration with MCP

The browser controller integrates with the MCP server providing these tools:

| Tool | Purpose |
|------|---------|
| `run_browser_test` | Generic browser automation |
| `test_mcp_metrics_app` | Test MCP-Metrics itself |
| `create_site_via_ui` | End-to-end site creation |
| `browser_gtm_preview_test` | GTM verification |
| `crawl_website` | Site discovery |

All tools are available in Claude Code when MCP-Metrics is configured as an MCP server.
