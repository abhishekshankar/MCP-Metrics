"""GTM automation service."""

from typing import Any

from sqlalchemy.orm import Session

from services.google_auth import GoogleAuthProvider
from config import get_settings
from models.site import Site
from services.audit_service import AuditService
from services.google_clients import get_gtm_client


class GTMService:
    def __init__(self, db: Session, auth: GoogleAuthProvider | None = None):
        self.db = db
        self.auth = auth or GoogleAuthProvider()
        self.client = get_gtm_client()
        self.audit = AuditService(db)
        self.settings = get_settings()
        self.account_id = self.settings.gtm_account_id

    def create_container(
        self,
        name: str,
        domain: str,
        *,
        site: Site | None = None,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        container_name = f"{name} - {site.environment if site else 'prod'}"
        existing = self.client.create_container(self.account_id, container_name, domain)
        if site and site.gtm_container_id == existing["containerId"]:
            self.audit.log(
                "gtm.container.reuse",
                site_id=site.id,
                domain=domain,
                actor=actor,
                actor_type=actor_type,
                details={"container_id": existing["containerId"]},
            )
            return existing

        self.audit.log(
            "gtm.container.create",
            site_id=site.id if site else None,
            domain=domain,
            actor=actor,
            actor_type=actor_type,
            new_value={
                "container_id": existing["containerId"],
                "public_id": existing["publicId"],
            },
        )
        return existing

    def create_workspace(
        self,
        container_id: str,
        name: str = "Default Workspace",
        *,
        site: Site | None = None,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        workspace = self.client.create_workspace(self.account_id, container_id, name)
        self.audit.log(
            "gtm.workspace.create",
            site_id=site.id if site else None,
            domain=site.domain if site else None,
            actor=actor,
            actor_type=actor_type,
            new_value={"workspace_id": workspace["workspaceId"]},
        )
        return workspace

    def create_ga4_config_tag(
        self,
        container_id: str,
        workspace_id: str,
        measurement_id: str,
        *,
        consent_preset: str = "none",
        linked_domains: list[str] | None = None,
        site: Site | None = None,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        # Create All Pages trigger
        trigger_config: dict[str, Any] = {
            "name": "All Pages",
            "type": "pageview",
        }
        if consent_preset in ("basic", "advanced"):
            trigger_config["name"] = f"All Pages - Consent ({consent_preset})"
            trigger_config["filter"] = [
                {
                    "type": "equals",
                    "parameter": [
                        {"type": "template", "key": "arg0", "value": "{{Consent Analytics}}"},
                        {"type": "template", "key": "arg1", "value": "granted"},
                    ],
                }
            ]
            self.client.create_variable(
                self.account_id,
                container_id,
                workspace_id,
                {
                    "name": "Consent Analytics",
                    "type": "v",
                    "parameter": [{"type": "template", "key": "name", "value": "analytics_storage"}],
                },
            )

        trigger = self.client.create_trigger(
            self.account_id, container_id, workspace_id, trigger_config
        )

        tag_params: list[dict] = [
            {"type": "template", "key": "measurementIdOverride", "value": measurement_id},
        ]
        if linked_domains:
            tag_params.append(
                {
                    "type": "template",
                    "key": "linkDomains",
                    "value": ",".join(linked_domains),
                }
            )

        tag_config = {
            "name": "GA4 Configuration",
            "type": "gaawc",
            "parameter": tag_params,
            "firingTriggerId": [trigger["triggerId"]],
        }
        tag = self.client.create_tag(self.account_id, container_id, workspace_id, tag_config)
        self.audit.log(
            "gtm.tag.ga4_config",
            site_id=site.id if site else None,
            domain=site.domain if site else None,
            actor=actor,
            actor_type=actor_type,
            new_value={"tag_id": tag["tagId"], "measurement_id": measurement_id},
        )
        return tag

    def create_event_tag(
        self,
        container_id: str,
        workspace_id: str,
        event_name: str,
        trigger_type: str,
        trigger_config: dict | None = None,
        parameters: list[str] | None = None,
        *,
        consent_preset: str = "none",
        site: Site | None = None,
    ) -> dict[str, Any]:
        trigger_cfg = trigger_config or {"name": f"Trigger - {event_name}", "type": trigger_type}
        if consent_preset in ("basic", "advanced"):
            trigger_cfg.setdefault("filter", []).append(
                {
                    "type": "equals",
                    "parameter": [
                        {"type": "template", "key": "arg0", "value": "{{Consent Analytics}}"},
                        {"type": "template", "key": "arg1", "value": "granted"},
                    ],
                }
            )
        trigger = self.client.create_trigger(
            self.account_id, container_id, workspace_id, trigger_cfg
        )
        tag_params = [
            {"type": "template", "key": "eventName", "value": event_name},
        ]
        if parameters:
            for param in parameters:
                tag_params.append(
                    {"type": "template", "key": f"eventParameters.{param}", "value": f"{{{{{param}}}}}"}
                )
        tag = self.client.create_tag(
            self.account_id,
            container_id,
            workspace_id,
            {
                "name": f"GA4 Event - {event_name}",
                "type": "gaawe",
                "parameter": tag_params,
                "firingTriggerId": [trigger["triggerId"]],
            },
        )
        return {"tag": tag, "trigger": trigger}

    def save_and_publish(
        self,
        container_id: str,
        workspace_id: str,
        *,
        site: Site | None = None,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        version = self.client.create_version(self.account_id, container_id, workspace_id)
        published = self.client.publish_version(
            self.account_id, container_id, version["containerVersionId"]
        )
        if site:
            site.gtm_latest_version_id = version["containerVersionId"]
            self.db.commit()
        self.audit.log(
            "gtm.publish",
            site_id=site.id if site else None,
            domain=site.domain if site else None,
            actor=actor,
            actor_type=actor_type,
            new_value={"version_id": version["containerVersionId"]},
        )
        return {"version": version, "published": published}

    def generate_snippets(self, container_public_id: str) -> dict[str, str]:
        head = f"""<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{container_public_id}');</script>
<!-- End Google Tag Manager -->"""
        noscript = f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={container_public_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""
        return {"head": head.strip(), "noscript": noscript.strip()}

    def get_config(self, container_id: str) -> dict:
        return self.client.get_config(self.account_id, container_id)

    def get_version(self, container_id: str, version_id: str) -> dict | None:
        return self.client.get_version(self.account_id, container_id, version_id)

    def provision_for_site(
        self,
        site: Site,
        *,
        actor: str = "system",
        actor_type: str = "system",
    ) -> Site:
        if site.gtm_container_id and site.gtm_snippets:
            return site

        container = self.create_container(site.name, site.domain, site=site, actor=actor, actor_type=actor_type)
        site.gtm_container_id = container["containerId"]
        site.gtm_container_public_id = container["publicId"]

        workspace = self.create_workspace(container["containerId"], site=site, actor=actor, actor_type=actor_type)
        site.gtm_workspace_id = workspace["workspaceId"]

        if site.ga4_measurement_id:
            linked = [site.primary_domain or site.domain] + (site.linked_domains or [])
            self.create_ga4_config_tag(
                container["containerId"],
                workspace["workspaceId"],
                site.ga4_measurement_id,
                consent_preset=site.consent_preset,
                linked_domains=linked if site.linked_domains else None,
                site=site,
                actor=actor,
                actor_type=actor_type,
            )

        self.save_and_publish(
            container["containerId"], workspace["workspaceId"], site=site, actor=actor, actor_type=actor_type
        )
        site.gtm_snippets = self.generate_snippets(container["publicId"])
        site.status = "active"
        self.db.commit()
        self.db.refresh(site)
        return site
