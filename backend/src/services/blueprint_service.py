"""Blueprint loading and application service."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import get_settings
from models.blueprint_version import BlueprintVersion
from models.site import Site
from services.audit_service import AuditService
from services.gtm_service import GTMService


class BlueprintEvent(BaseModel):
    name: str
    trigger_type: str
    trigger_config: dict | None = None
    parameters: list[str] = Field(default_factory=list)


class BlueprintDataLayer(BaseModel):
    helper_snippet: str = ""
    spec: dict[str, dict] = Field(default_factory=dict)


class Blueprint(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0"
    events: list[BlueprintEvent] = Field(default_factory=list)
    dataLayer: BlueprintDataLayer = Field(default_factory=BlueprintDataLayer)


class BlueprintService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.audit = AuditService(db)
        self.gtm = GTMService(db)
        self._cache: dict[str, Blueprint] = {}

    def _blueprint_dirs(self) -> list[Path]:
        dirs = [self.settings.blueprints_path]
        plugin_dir = Path(__file__).resolve().parent.parent / "plugins" / "blueprints"
        if plugin_dir.exists():
            dirs.append(plugin_dir)
        return dirs

    def load(self, name: str) -> Blueprint:
        if name in self._cache:
            return self._cache[name]
        for directory in self._blueprint_dirs():
            path = directory / f"{name}.yaml"
            if path.exists():
                with open(path) as f:
                    data = yaml.safe_load(f)
                blueprint = Blueprint.model_validate(data)
                self._cache[name] = blueprint
                return blueprint
        raise ValueError(f"Blueprint '{name}' not found")

    def list_available(self) -> list[dict[str, str]]:
        blueprints = {}
        for directory in self._blueprint_dirs():
            if not directory.exists():
                continue
            for path in directory.glob("*.yaml"):
                with open(path) as f:
                    data = yaml.safe_load(f)
                blueprints[data["name"]] = {
                    "name": data["name"],
                    "description": data.get("description", ""),
                    "version": data.get("version", "1.0"),
                }
        return list(blueprints.values())

    def validate(self, blueprint: Blueprint) -> bool:
        if not blueprint.name or not blueprint.events:
            raise ValueError("Blueprint must have name and at least one event")
        return True

    def apply(
        self,
        site: Site,
        blueprint_name: str,
        *,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        blueprint = self.load(blueprint_name)
        self.validate(blueprint)

        if not site.gtm_container_id or not site.gtm_workspace_id:
            raise RuntimeError("Site must have GTM container before applying blueprint")

        created_tags = []
        for event in blueprint.events:
            if event.name == "page_view" and event.trigger_type == "pageview":
                continue  # covered by GA4 config tag
            result = self.gtm.create_event_tag(
                site.gtm_container_id,
                site.gtm_workspace_id,
                event.name,
                event.trigger_type,
                trigger_config=event.trigger_config,
                parameters=event.parameters,
                consent_preset=site.consent_preset,
                site=site,
            )
            created_tags.append({"event": event.name, "tag_id": result["tag"]["tagId"]})

        publish_result = self.gtm.save_and_publish(
            site.gtm_container_id,
            site.gtm_workspace_id,
            site=site,
            actor=actor,
            actor_type=actor_type,
        )

        gtm_config = self.gtm.get_config(site.gtm_container_id)
        version_count = (
            self.db.query(BlueprintVersion)
            .filter(BlueprintVersion.site_id == site.id)
            .count()
        )
        bp_version = BlueprintVersion(
            site_id=site.id,
            blueprint_name=blueprint_name,
            version_number=version_count + 1,
            gtm_version_id=publish_result["version"]["containerVersionId"],
            config_snapshot=blueprint.model_dump(),
            gtm_config_snapshot=gtm_config,
        )
        self.db.add(bp_version)
        site.blueprint = blueprint_name
        site.config_snapshot = blueprint.model_dump()
        self.db.commit()

        self.audit.log(
            "blueprint.apply",
            site_id=site.id,
            domain=site.domain,
            actor=actor,
            actor_type=actor_type,
            new_value={
                "blueprint": blueprint_name,
                "tags_created": len(created_tags),
                "version": bp_version.version_number,
            },
        )

        return {
            "blueprint": blueprint_name,
            "tags_created": created_tags,
            "dataLayer": blueprint.dataLayer.model_dump(),
            "helper_snippet": blueprint.dataLayer.helper_snippet,
            "version": bp_version.version_number,
            "gtm_version_id": publish_result["version"]["containerVersionId"],
        }

    def save_custom(self, name: str, content: dict[str, Any]) -> Path:
        """Save a custom blueprint to the blueprints directory.

        Creates the blueprints directory if it doesn't exist.
        Validates the content before saving.
        """
        # Validate the blueprint content
        blueprint = Blueprint.model_validate(content)
        self.validate(blueprint)

        # Ensure the blueprints directory exists
        blueprints_dir = self.settings.blueprints_path
        blueprints_dir.mkdir(parents=True, exist_ok=True)

        # Save the blueprint
        path = blueprints_dir / f"{name}.yaml"
        with open(path, "w") as f:
            yaml.dump(content, f, default_flow_style=False, sort_keys=False)

        # Clear cache to ensure the new blueprint is loaded
        self._cache.pop(name, None)

        return path
