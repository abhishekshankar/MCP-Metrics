"""Analytics MCP Typer CLI."""

import json
import os
from typing import Optional

import httpx
import typer

app = typer.Typer(name="analytics-mcp", help="Analytics MCP CLI - GA4 + GTM automation")

API_URL = os.environ.get("ANALYTICS_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("ANALYTICS_API_KEY", "")


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


def _output(data: dict | list, pretty: bool = False) -> None:
    if pretty:
        typer.echo(json.dumps(data, indent=2))
    else:
        typer.echo(json.dumps(data))


def _request(method: str, path: str, **kwargs) -> dict | list:
    url = f"{API_URL}{path}"
    with httpx.Client(timeout=120) as client:
        response = client.request(method, url, headers=_headers(), **kwargs)
        if response.status_code >= 400:
            typer.echo(json.dumps({"error": response.text}), err=True)
            raise typer.Exit(1)
        return response.json()


@app.command()
def create(
    domain: str = typer.Option(..., help="Site domain"),
    name: str = typer.Option(..., help="Site name"),
    env: str = typer.Option("prod", "--env", help="Environment (dev/stage/prod)"),
    blueprint: Optional[str] = typer.Option("saas", help="Blueprint preset"),
    consent: str = typer.Option("none", help="Consent preset (none/basic/advanced)"),
    enable_bigquery: bool = typer.Option(False, help="Enable BigQuery export"),
    bigquery_project: Optional[str] = typer.Option(None),
    bigquery_dataset: Optional[str] = typer.Option(None),
    primary_domain: Optional[str] = typer.Option(None),
    linked_domains: Optional[str] = typer.Option(None, help="Comma-separated linked domains"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output"),
):
    """Create a full analytics setup (GA4 + GTM + blueprint)."""
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
        "linked_domains": linked_domains.split(",") if linked_domains else [],
    }
    result = _request("POST", "/sites", json=body)
    _output(result, pretty)


@app.command()
def status(
    domain: str = typer.Option(..., help="Site domain"),
    env: str = typer.Option("prod", "--env"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Get analytics status for a site."""
    result = _request("GET", f"/sites/{domain}", params={"environment": env})
    _output(result, pretty)


@app.command("list")
def list_sites(pretty: bool = typer.Option(False, "--pretty")):
    """List all managed sites."""
    result = _request("GET", "/sites")
    _output(result, pretty)


@app.command("apply-blueprint")
def apply_blueprint(
    domain: str = typer.Option(...),
    blueprint: str = typer.Option(...),
    env: str = typer.Option("prod", "--env"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Apply a tracking blueprint to a site."""
    result = _request(
        "POST",
        f"/sites/{domain}/blueprint",
        params={"environment": env},
        json={"blueprint": blueprint},
    )
    _output(result, pretty)


@app.command()
def health(
    domain: str = typer.Option(...),
    env: str = typer.Option("prod", "--env"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Run health check for a site."""
    result = _request("GET", f"/sites/{domain}/health", params={"environment": env})
    _output(result, pretty)


@app.command()
def rollback(
    domain: str = typer.Option(...),
    version: int = typer.Option(...),
    env: str = typer.Option("prod", "--env"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Rollback GTM configuration to a previous version."""
    result = _request(
        "POST",
        f"/sites/{domain}/rollback",
        params={"environment": env},
        json={"version": version},
    )
    _output(result, pretty)


@app.command()
def describe(
    domain: str = typer.Option(...),
    env: str = typer.Option("prod", "--env"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Describe analytics setup in human-readable format."""
    result = _request("GET", f"/sites/{domain}/describe", params={"environment": env})
    _output(result, pretty)


def main():
    app()


if __name__ == "__main__":
    main()
