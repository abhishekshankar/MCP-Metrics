"""Governance service for audit, diff, and rollback."""

from typing import Any

from sqlalchemy.orm import Session

from models.blueprint_version import BlueprintVersion
from models.site import Site
from services.audit_service import AuditService
from services.gtm_service import GTMService


class GovernanceService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)
        self.gtm = GTMService(db)

    def diff_gtm(
        self,
        before_version_id: str,
        after_version_id: str,
        container_id: str,
    ) -> dict[str, Any]:
        before = self.gtm.get_version(container_id, before_version_id)
        after = self.gtm.get_version(container_id, after_version_id)
        if not before or not after:
            current = self.gtm.get_config(container_id)
            return {
                "before_version_id": before_version_id,
                "after_version_id": after_version_id,
                "tags_added": [],
                "tags_removed": [],
                "triggers_added": [],
                "triggers_removed": [],
                "current_config": current,
            }

        def diff_items(before_items: list, after_items: list, key: str = "name") -> dict:
            before_names = {i.get(key, i.get("tagId", "")): i for i in before_items}
            after_names = {i.get(key, i.get("tagId", "")): i for i in after_items}
            added = [after_names[k] for k in after_names if k not in before_names]
            removed = [before_names[k] for k in before_names if k not in after_names]
            return {"added": added, "removed": removed}

        tag_diff = diff_items(before.get("tag", []), after.get("tag", []))
        trigger_diff = diff_items(before.get("trigger", []), after.get("trigger", []))
        var_diff = diff_items(before.get("variable", []), after.get("variable", []))

        return {
            "before_version_id": before_version_id,
            "after_version_id": after_version_id,
            "tags_added": tag_diff["added"],
            "tags_removed": tag_diff["removed"],
            "triggers_added": trigger_diff["added"],
            "triggers_removed": trigger_diff["removed"],
            "variables_added": var_diff["added"],
            "variables_removed": var_diff["removed"],
        }

    def get_version_history(self, site_id: int) -> list[BlueprintVersion]:
        return (
            self.db.query(BlueprintVersion)
            .filter(BlueprintVersion.site_id == site_id)
            .order_by(BlueprintVersion.version_number.desc())
            .all()
        )

    def rollback(
        self,
        site: Site,
        version_number: int,
        *,
        actor: str = "system",
        actor_type: str = "system",
    ) -> dict[str, Any]:
        bp_version = (
            self.db.query(BlueprintVersion)
            .filter(
                BlueprintVersion.site_id == site.id,
                BlueprintVersion.version_number == version_number,
            )
            .first()
        )
        if not bp_version:
            raise ValueError(f"Version {version_number} not found for site {site.domain}")

        old_version_id = site.gtm_latest_version_id
        site.gtm_latest_version_id = bp_version.gtm_version_id
        site.config_snapshot = bp_version.config_snapshot
        site.blueprint = bp_version.blueprint_name
        self.db.commit()

        self.audit.log(
            "gtm.rollback",
            site_id=site.id,
            domain=site.domain,
            actor=actor,
            actor_type=actor_type,
            old_value={"version_id": old_version_id},
            new_value={"version_id": bp_version.gtm_version_id, "version_number": version_number},
        )

        return {
            "domain": site.domain,
            "rolled_back_to_version": version_number,
            "gtm_version_id": bp_version.gtm_version_id,
            "blueprint": bp_version.blueprint_name,
        }
