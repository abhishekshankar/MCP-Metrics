"""Plugin loader for custom blueprints and integrations."""

from pathlib import Path

import yaml

from config import get_settings
from observability.logging import logger


class PluginLoader:
    def __init__(self):
        self.settings = get_settings()
        self.blueprints: dict[str, dict] = {}
        self.integrations: dict[str, dict] = {}

    def load_all(self) -> None:
        self._load_blueprints()
        self._load_integrations()
        logger.info(
            "plugins.loaded",
            blueprints=len(self.blueprints),
            integrations=len(self.integrations),
        )

    def _load_blueprints(self) -> None:
        dirs = [
            self.settings.blueprints_path,
            Path(__file__).resolve().parent / "blueprints",
        ]
        for directory in dirs:
            if not directory.exists():
                continue
            for path in directory.glob("*.yaml"):
                try:
                    with open(path) as f:
                        data = yaml.safe_load(f)
                    self.blueprints[data["name"]] = data
                except Exception as e:
                    logger.error("plugin.blueprint.load_failed", path=str(path), error=str(e))

    def _load_integrations(self) -> None:
        integrations_dir = Path(__file__).resolve().parent / "integrations"
        if not integrations_dir.exists():
            return
        for path in integrations_dir.glob("*.yaml"):
            try:
                with open(path) as f:
                    data = yaml.safe_load(f)
                self.integrations[data["name"]] = data
            except Exception as e:
                logger.error("plugin.integration.load_failed", path=str(path), error=str(e))

    def list_blueprints(self) -> list[str]:
        return list(self.blueprints.keys())

    def get_integration_snippet(self, name: str, container_id: str) -> str | None:
        integration = self.integrations.get(name)
        if not integration:
            return None
        return integration.get("snippet_template", "").replace("{{GTM_ID}}", container_id)


plugin_loader = PluginLoader()
