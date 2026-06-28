"""Mock and real Google API clients."""

import hashlib
from typing import Any

from config import get_settings


class MockGA4Client:
    """Mock Google Analytics Admin API client."""

    def __init__(self):
        self._properties: dict[str, dict] = {}
        self._streams: dict[str, dict] = {}

    def create_property(self, name: str, timezone: str, currency: str) -> dict[str, Any]:
        prop_id = f"properties/{hashlib.md5(name.encode()).hexdigest()[:10]}"
        prop = {
            "name": prop_id,
            "displayName": name,
            "timeZone": timezone,
            "currencyCode": currency,
        }
        self._properties[name] = prop
        return prop

    def get_property_by_name(self, name: str) -> dict[str, Any] | None:
        return self._properties.get(name)

    def create_web_data_stream(self, property_id: str, domain: str) -> dict[str, Any]:
        stream_key = f"{property_id}:{domain}"
        if stream_key in self._streams:
            return self._streams[stream_key]
        stream_id = hashlib.md5(stream_key.encode()).hexdigest()[:12]
        measurement_id = f"G-{stream_id[:7].upper()}"
        stream = {
            "name": f"{property_id}/dataStreams/{stream_id}",
            "webStreamData": {"defaultUri": f"https://{domain}"},
            "measurementId": measurement_id,
        }
        self._streams[stream_key] = stream
        return stream

    def get_web_data_stream(self, property_id: str, domain: str) -> dict[str, Any] | None:
        return self._streams.get(f"{property_id}:{domain}")

    def enable_bigquery_export(
        self, property_id: str, project: str, dataset: str
    ) -> dict[str, Any]:
        return {
            "property": property_id,
            "bigqueryProject": project,
            "dataset": dataset,
            "status": "LINKED",
        }

    def run_report(self, property_id: str) -> dict[str, Any]:
        return {
            "eventCount": 1500,
            "sessions": 800,
            "conversions": 45,
            "rows": [{"eventCount": "1500", "sessions": "800", "conversions": "45"}],
        }


class MockGTMClient:
    """Mock Google Tag Manager API client."""

    def __init__(self):
        self._containers: dict[str, dict] = {}
        self._workspaces: dict[str, dict] = {}
        self._tags: dict[str, list] = {}
        self._triggers: dict[str, list] = {}
        self._variables: dict[str, list] = {}
        self._versions: dict[str, list] = {}

    def create_container(self, account_id: str, name: str, domain: str) -> dict[str, Any]:
        key = f"{account_id}:{name}"
        if key in self._containers:
            return self._containers[key]
        container_id = hashlib.md5(key.encode()).hexdigest()[:8]
        container = {
            "containerId": container_id,
            "publicId": f"GTM-{container_id[:4].upper()}",
            "name": name,
            "domainName": [domain],
            "accountId": account_id,
        }
        self._containers[key] = container
        return container

    def create_workspace(self, account_id: str, container_id: str, name: str) -> dict[str, Any]:
        key = f"{container_id}:{name}"
        if key in self._workspaces:
            return self._workspaces[key]
        ws_id = hashlib.md5(key.encode()).hexdigest()[:6]
        workspace = {"workspaceId": ws_id, "name": name, "containerId": container_id}
        self._workspaces[key] = workspace
        self._tags[key] = []
        self._triggers[key] = []
        self._variables[key] = []
        return workspace

    def create_tag(
        self, account_id: str, container_id: str, workspace_id: str, tag_config: dict
    ) -> dict[str, Any]:
        key = f"{container_id}:Default Workspace"
        ws_key = f"{container_id}:Default Workspace"
        tag_id = str(len(self._tags.get(ws_key, [])) + 1)
        tag = {"tagId": tag_id, **tag_config}
        self._tags.setdefault(ws_key, []).append(tag)
        return tag

    def create_trigger(
        self, account_id: str, container_id: str, workspace_id: str, trigger_config: dict
    ) -> dict[str, Any]:
        ws_key = f"{container_id}:Default Workspace"
        trigger_id = str(len(self._triggers.get(ws_key, [])) + 1)
        trigger = {"triggerId": trigger_id, **trigger_config}
        self._triggers.setdefault(ws_key, []).append(trigger)
        return trigger

    def create_variable(
        self, account_id: str, container_id: str, workspace_id: str, variable_config: dict
    ) -> dict[str, Any]:
        ws_key = f"{container_id}:Default Workspace"
        var_id = str(len(self._variables.get(ws_key, [])) + 1)
        variable = {"variableId": var_id, **variable_config}
        self._variables.setdefault(ws_key, []).append(variable)
        return variable

    def create_version(self, account_id: str, container_id: str, workspace_id: str) -> dict:
        key = container_id
        version_id = str(len(self._versions.get(key, [])) + 1)
        version = {
            "containerVersionId": version_id,
            "name": f"Version {version_id}",
            "tag": self._tags.get(f"{container_id}:Default Workspace", []),
            "trigger": self._triggers.get(f"{container_id}:Default Workspace", []),
            "variable": self._variables.get(f"{container_id}:Default Workspace", []),
        }
        self._versions.setdefault(key, []).append(version)
        return version

    def publish_version(self, account_id: str, container_id: str, version_id: str) -> dict:
        return {"containerVersionId": version_id, "published": True}

    def get_version(self, account_id: str, container_id: str, version_id: str) -> dict | None:
        versions = self._versions.get(container_id, [])
        for v in versions:
            if v["containerVersionId"] == version_id:
                return v
        return None

    def get_latest_version(self, account_id: str, container_id: str) -> dict | None:
        versions = self._versions.get(container_id, [])
        return versions[-1] if versions else None

    def get_config(self, account_id: str, container_id: str) -> dict:
        ws_key = f"{container_id}:Default Workspace"
        return {
            "tags": self._tags.get(ws_key, []),
            "triggers": self._triggers.get(ws_key, []),
            "variables": self._variables.get(ws_key, []),
        }


def get_ga4_client():
    settings = get_settings()
    if settings.mock_google_apis:
        return MockGA4Client()
    # Use real client when not in mock mode
    from services.google_clients_real import RealGA4AdminClient
    return RealGA4AdminClient()


def get_gtm_client():
    settings = get_settings()
    if settings.mock_google_apis:
        return MockGTMClient()
    # Use real client when not in mock mode
    from services.google_clients_real import RealGTMClient
    return RealGTMClient()
