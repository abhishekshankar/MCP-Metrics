"""GA4 automation service with retry support."""

from typing import Any

from sqlalchemy.orm import Session

from services.google_auth import GoogleAuthProvider
from config import get_settings
from models.site import Site
from services.audit_service import AuditService
from services.google_clients import get_ga4_client
from services.retry_client import retry_with_backoff


class GA4Service:
    def __init__(self, db: Session, auth: GoogleAuthProvider | None = None):
        self.db = db
        self.auth = auth or GoogleAuthProvider()
        self.client = get_ga4_client()
        self.audit = AuditService(db)
        self.settings = get_settings()

    @retry_with_backoff()
    def create_property(
        self,
        name: str,
        timezone: str = "America/New_York",
        currency: str = "USD",
        *,
        site: Site | None = None,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        property_name = f"{name} - {site.environment if site else 'prod'}"
        existing = self.client.get_property_by_name(property_name)
        if existing:
            self.audit.log(
                "ga4.property.reuse",
                site_id=site.id if site else None,
                domain=site.domain if site else None,
                actor=actor,
                actor_type=actor_type,
                details={"property_name": property_name, "property_id": existing["name"]},
            )
            return existing

        try:
            if not self.settings.mock_google_apis:
                self.auth.refresh_if_needed()
            prop = self.client.create_property(property_name, timezone, currency)
            self.audit.log(
                "ga4.property.create",
                site_id=site.id if site else None,
                domain=site.domain if site else None,
                actor=actor,
                actor_type=actor_type,
                new_value={"property_id": prop["name"], "display_name": property_name},
            )
            return prop
        except Exception as e:
            self.audit.log(
                "ga4.property.create",
                site_id=site.id if site else None,
                domain=site.domain if site else None,
                actor=actor,
                actor_type=actor_type,
                status="error",
                message=f"Failed to create GA4 property: {e}",
            )
            raise RuntimeError(f"Failed to create GA4 property '{property_name}': {e}") from e

    @retry_with_backoff()
    def create_web_data_stream(
        self,
        property_id: str,
        domain: str,
        *,
        site: Site | None = None,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        existing = self.client.get_web_data_stream(property_id, domain)
        if existing:
            self.audit.log(
                "ga4.stream.reuse",
                site_id=site.id if site else None,
                domain=domain,
                actor=actor,
                actor_type=actor_type,
                details={
                    "measurement_id": existing["measurementId"],
                    "stream_id": existing["name"],
                },
            )
            return existing

        try:
            stream = self.client.create_web_data_stream(property_id, domain)
            self.audit.log(
                "ga4.stream.create",
                site_id=site.id if site else None,
                domain=domain,
                actor=actor,
                actor_type=actor_type,
                new_value={
                    "measurement_id": stream["measurementId"],
                    "stream_id": stream["name"],
                },
            )
            return stream
        except Exception as e:
            self.audit.log(
                "ga4.stream.create",
                site_id=site.id if site else None,
                domain=domain,
                actor=actor,
                actor_type=actor_type,
                status="error",
                message=str(e),
            )
            raise RuntimeError(f"Failed to create web data stream for {domain}: {e}") from e

    @retry_with_backoff()
    def enable_bigquery_export(
        self,
        property_id: str,
        project: str,
        dataset: str,
        *,
        site: Site | None = None,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        try:
            result = self.client.enable_bigquery_export(property_id, project, dataset)
            if site:
                site.bigquery_enabled = True
                site.bigquery_project = project
                site.bigquery_dataset = dataset
                self.db.commit()
            self.audit.log(
                "ga4.bigquery.enable",
                site_id=site.id if site else None,
                domain=site.domain if site else None,
                actor=actor,
                actor_type=actor_type,
                new_value={"project": project, "dataset": dataset},
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to enable BigQuery export: {e}") from e

    @retry_with_backoff()
    def run_health_report(self, property_id: str) -> dict[str, Any]:
        return self.client.run_report(property_id)

    def provision_for_site(
        self,
        site: Site,
        *,
        actor: str = "system",
        actor_type: str = "system",
    ) -> Site:
        """Idempotent GA4 provisioning for a site."""
        if site.ga4_property_id and site.ga4_measurement_id:
            return site

        prop = self.create_property(site.name, site=site, actor=actor, actor_type=actor_type)
        site.ga4_property_id = prop["name"]

        stream = self.create_web_data_stream(
            prop["name"], site.domain, site=site, actor=actor, actor_type=actor_type
        )
        site.ga4_measurement_id = stream["measurementId"]
        site.ga4_data_stream_id = stream["name"]
        self.db.commit()
        self.db.refresh(site)
        return site
