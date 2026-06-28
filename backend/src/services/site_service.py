"""Site orchestration service."""

from typing import Any

from sqlalchemy.orm import Session

from models.site import Site
from services.audit_service import AuditService
from services.blueprint_service import BlueprintService
from services.ga4_service import GA4Service
from services.gtm_service import GTMService


class SiteService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)
        self.ga4 = GA4Service(db)
        self.gtm = GTMService(db)
        self.blueprint = BlueprintService(db)

    def get_by_domain(self, domain: str, environment: str = "prod") -> Site | None:
        return (
            self.db.query(Site)
            .filter(Site.domain == domain, Site.environment == environment)
            .first()
        )

    def list_sites(self) -> list[Site]:
        return self.db.query(Site).order_by(Site.created_at.desc()).all()

    def create_site(
        self,
        domain: str,
        name: str,
        environment: str = "prod",
        blueprint: str | None = None,
        consent_preset: str = "none",
        primary_domain: str | None = None,
        linked_domains: list[str] | None = None,
        enable_bigquery: bool = False,
        bigquery_project: str | None = None,
        bigquery_dataset: str | None = None,
        *,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        existing = self.get_by_domain(domain, environment)
        if existing and existing.status == "active":
            self.audit.log(
                "site.create.reuse",
                site_id=existing.id,
                domain=domain,
                actor=actor,
                actor_type=actor_type,
                details={"environment": environment},
            )
            return self._site_response(existing, reused=True)

        site = existing or Site(
            domain=domain,
            name=name,
            environment=environment,
            consent_preset=consent_preset,
            primary_domain=primary_domain or domain,
            linked_domains=linked_domains or [],
            status="provisioning",
        )
        if not existing:
            self.db.add(site)
            self.db.commit()
            self.db.refresh(site)

        site.name = name
        site.consent_preset = consent_preset
        site.primary_domain = primary_domain or domain
        site.linked_domains = linked_domains or []
        self.db.commit()

        site = self.ga4.provision_for_site(site, actor=actor, actor_type=actor_type)
        site = self.gtm.provision_for_site(site, actor=actor, actor_type=actor_type)

        blueprint_result = None
        if blueprint:
            blueprint_result = self.blueprint.apply(
                site, blueprint, actor=actor, actor_type=actor_type
            )

        if enable_bigquery and bigquery_project and bigquery_dataset and site.ga4_property_id:
            self.ga4.enable_bigquery_export(
                site.ga4_property_id,
                bigquery_project,
                bigquery_dataset,
                site=site,
                actor=actor,
                actor_type=actor_type,
            )

        site.status = "active"
        self.db.commit()
        self.db.refresh(site)

        self.audit.log(
            "site.create",
            site_id=site.id,
            domain=domain,
            actor=actor,
            actor_type=actor_type,
            new_value={"environment": environment, "blueprint": blueprint},
        )

        response = self._site_response(site)
        if blueprint_result:
            response["blueprint_result"] = blueprint_result
        return response

    def get_status(self, domain: str, environment: str = "prod") -> dict[str, Any]:
        site = self.get_by_domain(domain, environment)
        if not site:
            raise ValueError(f"Site '{domain}' ({environment}) not found")
        return self._site_response(site)

    def describe_setup(self, domain: str, environment: str = "prod") -> dict[str, Any]:
        site = self.get_by_domain(domain, environment)
        if not site:
            raise ValueError(f"Site '{domain}' not found")

        consent_docs = {
            "none": "No consent gating. All tags fire on all pages. Use only for dev/lab.",
            "basic": "Tags fire when analytics_storage consent is granted via dataLayer.",
            "advanced": "Full CMP integration via dataLayer consent events (analytics_storage, ad_storage).",
        }

        events = []
        if site.config_snapshot and "events" in site.config_snapshot:
            events = [e["name"] for e in site.config_snapshot["events"]]

        return {
            "domain": site.domain,
            "environment": site.environment,
            "name": site.name,
            "blueprint": site.blueprint,
            "consent_preset": site.consent_preset,
            "consent_explanation": consent_docs.get(site.consent_preset, ""),
            "ga4": {
                "property_id": site.ga4_property_id,
                "measurement_id": site.ga4_measurement_id,
            },
            "gtm": {
                "container_id": site.gtm_container_id,
                "public_id": site.gtm_container_public_id,
                "latest_version": site.gtm_latest_version_id,
            },
            "cross_domain": {
                "primary_domain": site.primary_domain,
                "linked_domains": site.linked_domains,
            },
            "bigquery": {
                "enabled": site.bigquery_enabled,
                "project": site.bigquery_project,
                "dataset": site.bigquery_dataset,
            },
            "tracked_events": events,
            "snippets": site.gtm_snippets,
            "summary": (
                f"Site '{site.name}' ({site.domain}, {site.environment}) uses "
                f"blueprint '{site.blueprint or 'none'}' with {site.consent_preset} consent. "
                f"GA4 Measurement ID: {site.ga4_measurement_id}. "
                f"GTM Container: {site.gtm_container_public_id}."
            ),
        }

    def _site_response(self, site: Site, reused: bool = False) -> dict[str, Any]:
        return {
            "id": site.id,
            "domain": site.domain,
            "name": site.name,
            "environment": site.environment,
            "status": site.status,
            "blueprint": site.blueprint,
            "consent_preset": site.consent_preset,
            "ga4_property_id": site.ga4_property_id,
            "ga4_measurement_id": site.ga4_measurement_id,
            "gtm_container_id": site.gtm_container_id,
            "gtm_container_public_id": site.gtm_container_public_id,
            "gtm_latest_version_id": site.gtm_latest_version_id,
            "snippets": site.gtm_snippets,
            "bigquery_enabled": site.bigquery_enabled,
            "primary_domain": site.primary_domain,
            "linked_domains": site.linked_domains,
            "reused": reused,
        }
