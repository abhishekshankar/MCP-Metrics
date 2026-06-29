"""Analytics MCP Typer CLI."""

import json
import os
from pathlib import Path
from typing import Optional

import httpx
import typer
import yaml

app = typer.Typer(name="analytics-mcp", help="Analytics MCP CLI - GA4 + GTM automation")

# Config file paths (in order of precedence)
CONFIG_PATHS = [
    Path(".analytics.yaml"),  # Project-local config
    Path(".analytics.yml"),
    Path(".analytics.json"),
    Path.home() / ".config" / "analytics-mcp" / "config.yaml",  # User config
    Path.home() / ".analytics.yaml",  # Legacy user config
]


def _load_config() -> dict:
    """Load configuration from file if present."""
    config = {}
    for path in CONFIG_PATHS:
        if path.exists():
            try:
                with open(path, "r") as f:
                    if path.suffix == ".json":
                        config = json.load(f)
                    else:
                        config = yaml.safe_load(f) or {}
                break  # Use first found config
            except Exception:
                continue
    return config


def _get_api_url() -> str:
    """Get API URL from environment or config."""
    return os.environ.get("ANALYTICS_API_URL") or _load_config().get(
        "api_url", "http://localhost:8000"
    )


def _get_api_key() -> str:
    """Get API key from environment or config."""
    return os.environ.get("ANALYTICS_API_KEY") or _load_config().get("api_key", "")


def _headers() -> dict[str, str]:
    """Get request headers with API key if configured."""
    headers = {"Content-Type": "application/json"}
    api_key = _get_api_key()
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


def _output(data: dict | list, pretty: bool = False) -> None:
    """Output JSON data to stdout."""
    if pretty:
        typer.echo(json.dumps(data, indent=2))
    else:
        typer.echo(json.dumps(data))


def _error(message: str, exit_code: int = 1) -> None:
    """Output error message to stderr and exit."""
    typer.secho(f"Error: {message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(exit_code)


def _request(method: str, path: str, **kwargs) -> dict | list:
    """Make HTTP request to API with error handling."""
    api_url = _get_api_url()
    url = f"{api_url}{path}"

    try:
        with httpx.Client(timeout=120) as client:
            response = client.request(method, url, headers=_headers(), **kwargs)

            if response.status_code == 401:
                _error("Authentication failed - check your API key")
            elif response.status_code == 403:
                _error("Permission denied - your API key may not have access")
            elif response.status_code == 404:
                _error(f"Resource not found: {path}")
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", response.text)
                except Exception:
                    detail = response.text
                _error(f"API error ({response.status_code}): {detail}")

            return response.json()
    except httpx.ConnectError:
        _error(f"Cannot connect to API at {api_url} - is the server running?")
    except httpx.TimeoutException:
        _error("Request timed out - the API may be slow or unresponsive")
    except Exception as e:
        _error(f"Request failed: {e}")


def _validate_env(env: str) -> str:
    """Validate environment value."""
    valid = ["dev", "stage", "prod"]
    if env not in valid:
        _error(f"Invalid environment '{env}' - must be one of: {', '.join(valid)}")
    return env


def _parse_linked_domains(domains_str: Optional[str]) -> list[str]:
    """Parse comma-separated linked domains, stripping whitespace."""
    if not domains_str:
        return []
    return [d.strip().lower() for d in domains_str.split(",") if d.strip()]


# Site Management Commands


@app.command()
def create(
    domain: str = typer.Option(..., help="Site domain (e.g., example.com)"),
    name: str = typer.Option(..., help="Site name"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    blueprint: Optional[str] = typer.Option(
        "saas", help="Blueprint preset (saas/ecommerce/content/none)"
    ),
    consent: str = typer.Option("none", help="Consent preset (none/basic/advanced)"),
    enable_bigquery: bool = typer.Option(False, help="Enable BigQuery export"),
    bigquery_project: Optional[str] = typer.Option(None, help="BigQuery project ID"),
    bigquery_dataset: Optional[str] = typer.Option(None, help="BigQuery dataset name"),
    primary_domain: Optional[str] = typer.Option(
        None, help="Primary domain for cross-domain tracking"
    ),
    linked_domains: Optional[str] = typer.Option(
        None, help="Comma-separated linked domains (e.g., 'shop.example.com, app.example.com')"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
):
    """Create a full analytics setup (GA4 + GTM + blueprint)."""
    _validate_env(env)

    body = {
        "domain": domain,
        "name": name,
        "environment": env,
        "blueprint": blueprint,
        "consent_preset": consent,
        "enable_bigquery": enable_bigquery,
        "bigquery_project": bigquery_project,
        "bigquery_dataset": bigquery_dataset,
        "primary_domain": primary_domain,
        "linked_domains": _parse_linked_domains(linked_domains),
    }
    result = _request("POST", "/sites", json=body)
    _output(result, pretty)


@app.command()
def status(
    domain: str = typer.Option(..., help="Site domain"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """Get analytics status for a site."""
    _validate_env(env)
    result = _request("GET", f"/sites/{domain}", params={"environment": env})
    _output(result, pretty)


@app.command("list")
def list_sites(
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """List all managed sites."""
    result = _request("GET", "/sites")
    _output(result, pretty)


@app.command()
def describe(
    domain: str = typer.Option(..., help="Site domain"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """Describe analytics setup in human-readable format."""
    _validate_env(env)
    result = _request("GET", f"/sites/{domain}/describe", params={"environment": env})
    _output(result, pretty)


# Blueprint Commands


@app.command("apply-blueprint")
def apply_blueprint(
    domain: str = typer.Option(..., help="Site domain"),
    blueprint: str = typer.Option(..., help="Blueprint to apply (saas/ecommerce/content)"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """Apply a tracking blueprint to a site."""
    _validate_env(env)
    result = _request(
        "POST",
        f"/sites/{domain}/blueprint",
        params={"environment": env},
        json={"blueprint": blueprint},
    )
    _output(result, pretty)


@app.command("blueprints")
def list_blueprints(
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """List available tracking blueprints."""
    result = _request("GET", "/blueprints")
    _output(result, pretty)


# Health Commands


@app.command()
def health(
    domain: str = typer.Option(..., help="Site domain"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """Run health check for a site."""
    _validate_env(env)
    result = _request("GET", f"/sites/{domain}/health", params={"environment": env})
    _output(result, pretty)


@app.command("health-history")
def health_history(
    domain: str = typer.Option(..., help="Site domain"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    limit: int = typer.Option(30, help="Number of history entries to retrieve (max 100)"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """Get health check history for a site."""
    _validate_env(env)
    result = _request(
        "GET",
        f"/sites/{domain}/health/history",
        params={"environment": env, "limit": limit},
    )
    _output(result, pretty)


# Governance Commands


@app.command()
def rollback(
    domain: str = typer.Option(..., help="Site domain"),
    version: int = typer.Option(..., help="Version number to rollback to"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """Rollback GTM configuration to a previous version."""
    _validate_env(env)
    result = _request(
        "POST",
        f"/sites/{domain}/rollback",
        params={"environment": env},
        json={"version": version},
    )
    _output(result, pretty)


@app.command("versions")
def list_versions(
    domain: str = typer.Option(..., help="Site domain"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """List blueprint version history for a site."""
    _validate_env(env)
    result = _request("GET", f"/sites/{domain}/versions", params={"environment": env})
    _output(result, pretty)


# Audit Commands


@app.command("audit")
def audit_log(
    domain: Optional[str] = typer.Option(None, help="Filter by domain"),
    operation: Optional[str] = typer.Option(None, help="Filter by operation type"),
    limit: int = typer.Option(100, help="Maximum entries to retrieve (max 500)"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """View audit log."""
    params = {"limit": min(limit, 500)}
    if domain:
        params["domain"] = domain
    if operation:
        params["operation"] = operation

    result = _request("GET", "/audit", params=params)
    _output(result, pretty)


# Advanced Commands


@app.command("analyze")
def analyze_site(
    domain: str = typer.Option(..., help="Site domain to analyze"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    max_pages: int = typer.Option(50, help="Maximum pages to crawl (max 100)"),
    max_depth: int = typer.Option(3, help="Maximum crawl depth (max 5)"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """Analyze site structure by crawling with Playwright.

    Discovers pages, groups by business purpose, and identifies tracking opportunities.
    """
    _validate_env(env)
    body = {
        "max_pages": min(max_pages, 100),
        "crawl_depth": min(max_depth, 5),
    }
    result = _request(
        "POST",
        f"/sites/{domain}/analyze",
        params={"environment": env},
        json=body,
    )
    _output(result, pretty)


@app.command("verify-preview")
def verify_gtm_preview(
    domain: str = typer.Option(..., help="Site domain"),
    container_id: str = typer.Option(..., help="GTM container ID (e.g., GTM-ABC123)"),
    preview_id: str = typer.Option(..., help="GTM Preview mode ID"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    test_pages: Optional[str] = typer.Option(
        None, help="Comma-separated paths to test (default: /)"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """Verify GTM Preview mode in a real browser.

    Opens GTM Preview mode and verifies that tags fire correctly before publishing.
    """
    _validate_env(env)

    pages = [p.strip() for p in test_pages.split(",") if p.strip()] if test_pages else None

    body = {
        "container_id": container_id,
        "preview_id": preview_id,
        "test_pages": pages,
    }
    result = _request(
        "POST",
        f"/sites/{domain}/verify-preview",
        params={"environment": env},
        json=body,
    )
    _output(result, pretty)


# Config Command


@app.command("config")
def show_config(
    pretty: bool = typer.Option(False, "--pretty", "-p"),
):
    """Show current configuration (API URL and config file location)."""
    _load_config()  # Ensure config is loaded
    config_file = None
    for path in CONFIG_PATHS:
        if path.exists():
            config_file = str(path)
            break

    result = {
        "api_url": _get_api_url(),
        "api_key_configured": bool(_get_api_key()),
        "config_file": config_file,
        "config_file_exists": config_file is not None,
    }
    _output(result, pretty)


def main():
    app()


if __name__ == "__main__":
    main()
