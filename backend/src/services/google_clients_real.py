"""Real Google API clients for production use.

These clients call the actual Google Analytics Admin API, GTM API, and GA4 Data API.
They are used when MOCK_GOOGLE_APIS=false and credentials are configured.
"""

import os
from typing import Any

from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account
from googleapiclient.discovery import build
from observability.logging import log_failure, logger

from config import get_settings


class RealGA4AdminClient:
    """Real Google Analytics 4 Admin API client."""

    def __init__(self, credentials_path: str | None = None):
        self.settings = get_settings()
        self.credentials_path = credentials_path or self.settings.google_application_credentials
        self._client: AnalyticsAdminServiceClient | None = None

    def _get_client(self) -> AnalyticsAdminServiceClient:
        if self._client is None:
            if not self.credentials_path or not os.path.isfile(self.credentials_path):
                raise ValueError(f"Credentials file not found: {self.credentials_path}")

            self._client = AnalyticsAdminServiceClient.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/analytics.edit"],
            )
            logger.info("ga4_admin.client_initialized")
        return self._client

    def create_property(
        self, name: str, timezone: str = "America/New_York", currency: str = "USD"
    ) -> dict[str, Any]:
        """Create a GA4 property."""
        from google.analytics.admin_v1alpha.types import Property

        client = self._get_client()
        property_obj = Property(
            display_name=name,
            time_zone=timezone,
            currency_code=currency,
        )

        try:
            result = client.create_property(property=property_obj)
            logger.info("ga4.property_created", property_id=result.name, name=name)
            return {
                "name": result.name,
                "displayName": result.display_name,
                "timeZone": result.time_zone,
                "currencyCode": result.currency_code,
                "propertyId": result.name.split("/")[-1],
            }
        except Exception as e:
            log_failure("ga4.create_property_failed", error=str(e), name=name)
            raise

    def create_web_data_stream(self, property_id: str, domain: str) -> dict[str, Any]:
        """Create a web data stream for a property."""
        from google.analytics.admin_v1alpha.types import DataStream

        client = self._get_client()
        stream = DataStream(
            type_="WEB_DATA_STREAM",
            display_name=f"{domain} Web Stream",
            web_stream_data={
                "default_uri": f"https://{domain}",
            },
        )

        try:
            result = client.create_data_stream(parent=property_id, data_stream=stream)
            logger.info(
                "ga4.web_stream_created",
                property_id=property_id,
                stream_id=result.name,
                measurement_id=result.web_stream_data.measurement_id,
            )
            return {
                "name": result.name,
                "type": "WEB_DATA_STREAM",
                "measurementId": result.web_stream_data.measurement_id,
                "defaultUri": result.web_stream_data.default_uri,
                "streamId": result.name.split("/")[-1],
            }
        except Exception as e:
            log_failure("ga4.create_web_stream_failed", error=str(e), property_id=property_id)
            raise

    def get_property(self, property_id: str) -> dict[str, Any] | None:
        """Get a property by ID."""
        client = self._get_client()
        try:
            result = client.get_property(name=property_id)
            return {
                "name": result.name,
                "displayName": result.display_name,
                "timeZone": result.time_zone,
                "currencyCode": result.currency_code,
            }
        except Exception as e:
            if "not found" in str(e).lower():
                return None
            raise

    def enable_bigquery_link(self, property_id: str, project: str, dataset: str) -> dict[str, Any]:
        """Enable BigQuery export for a property."""
        from google.analytics.admin_v1alpha.types import BigQueryLink

        client = self._get_client()
        link = BigQueryLink(
            project=project,
            dataset=dataset,
            daily_export_enabled=True,
            streaming_export_enabled=True,
        )

        try:
            result = client.create_big_query_link(parent=property_id, big_query_link=link)
            logger.info(
                "ga4.bigquery_link_created",
                property_id=property_id,
                project=project,
                dataset=dataset,
            )
            return {
                "name": result.name,
                "project": result.project,
                "dataset": result.dataset,
                "dailyExportEnabled": result.daily_export_enabled,
                "streamingExportEnabled": result.streaming_export_enabled,
            }
        except Exception as e:
            log_failure("ga4.bigquery_link_failed", error=str(e), property_id=property_id)
            raise


class RealGTMClient:
    """Real Google Tag Manager API client."""

    API_VERSION = "v2"
    SCOPES = ["https://www.googleapis.com/auth/tagmanager.edit.containers"]

    def __init__(self, credentials_path: str | None = None):
        self.settings = get_settings()
        self.credentials_path = credentials_path or self.settings.google_application_credentials
        self._service: Any | None = None

    def _get_service(self) -> Any:
        if self._service is None:
            if not self.credentials_path or not os.path.isfile(self.credentials_path):
                raise ValueError(f"Credentials file not found: {self.credentials_path}")

            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES,
            )
            self._service = build("tagmanager", self.API_VERSION, credentials=credentials)
            logger.info("gtm.service_initialized")
        return self._service

    def create_container(self, account_id: str, name: str, domain: str) -> dict[str, Any]:
        """Create a GTM container."""
        service = self._get_service()

        body = {
            "name": name,
            "usageContext": ["web"],
            "domainName": [domain],
        }

        try:
            result = (
                service.accounts()
                .containers()
                .create(parent=f"accounts/{account_id}", body=body)
                .execute()
            )
            logger.info(
                "gtm.container_created",
                account_id=account_id,
                container_id=result["containerId"],
                name=name,
            )
            return {
                "containerId": result["containerId"],
                "publicId": result["publicId"],
                "name": result["name"],
                "domainName": result.get("domainName", []),
                "accountId": account_id,
            }
        except Exception as e:
            log_failure("gtm.create_container_failed", error=str(e), account_id=account_id)
            raise

    def create_workspace(
        self, account_id: str, container_id: str, name: str = "Default Workspace"
    ) -> dict[str, Any]:
        """Create a workspace in a container."""
        service = self._get_service()

        body = {"name": name, "description": "Created by Analytics MCP"}

        try:
            result = (
                service.accounts()
                .containers()
                .workspaces()
                .create(
                    parent=f"accounts/{account_id}/containers/{container_id}",
                    body=body,
                )
                .execute()
            )
            logger.info(
                "gtm.workspace_created",
                account_id=account_id,
                container_id=container_id,
                workspace_id=result["workspaceId"],
            )
            return {
                "workspaceId": result["workspaceId"],
                "name": result["name"],
                "containerId": container_id,
            }
        except Exception as e:
            log_failure("gtm.create_workspace_failed", error=str(e), container_id=container_id)
            raise

    def create_tag(
        self,
        account_id: str,
        container_id: str,
        workspace_id: str,
        tag_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a tag in a workspace."""
        service = self._get_service()

        try:
            result = (
                service.accounts()
                .containers()
                .workspaces()
                .tags()
                .create(
                    parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}",
                    body=tag_config,
                )
                .execute()
            )
            logger.info(
                "gtm.tag_created",
                account_id=account_id,
                container_id=container_id,
                tag_id=result["tagId"],
                name=tag_config.get("name"),
            )
            return {
                "tagId": result["tagId"],
                "name": result["name"],
                "type": result["type"],
                "firingTriggerId": result.get("firingTriggerId", []),
            }
        except Exception as e:
            log_failure("gtm.create_tag_failed", error=str(e), tag_name=tag_config.get("name"))
            raise

    def create_trigger(
        self,
        account_id: str,
        container_id: str,
        workspace_id: str,
        trigger_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a trigger in a workspace."""
        service = self._get_service()

        try:
            result = (
                service.accounts()
                .containers()
                .workspaces()
                .triggers()
                .create(
                    parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}",
                    body=trigger_config,
                )
                .execute()
            )
            logger.info(
                "gtm.trigger_created",
                account_id=account_id,
                trigger_id=result["triggerId"],
                name=trigger_config.get("name"),
            )
            return {
                "triggerId": result["triggerId"],
                "name": result["name"],
                "type": result["type"],
            }
        except Exception as e:
            log_failure(
                "gtm.create_trigger_failed", error=str(e), trigger_name=trigger_config.get("name")
            )
            raise

    def create_variable(
        self,
        account_id: str,
        container_id: str,
        workspace_id: str,
        variable_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a variable in a workspace."""
        service = self._get_service()

        try:
            result = (
                service.accounts()
                .containers()
                .workspaces()
                .variables()
                .create(
                    parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}",
                    body=variable_config,
                )
                .execute()
            )
            return {
                "variableId": result["variableId"],
                "name": result["name"],
                "type": result["type"],
            }
        except Exception as e:
            log_failure("gtm.create_variable_failed", error=str(e))
            raise

    def create_version(
        self,
        account_id: str,
        container_id: str,
        workspace_id: str,
        name: str = "Published by Analytics MCP",
    ) -> dict[str, Any]:
        """Create a container version."""
        service = self._get_service()

        body = {"name": name}

        try:
            result = (
                service.accounts()
                .containers()
                .workspaces()
                .create_version(
                    path=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}",
                    body=body,
                )
                .execute()
            )
            logger.info(
                "gtm.version_created",
                account_id=account_id,
                container_id=container_id,
                version_id=result["containerVersion"]["containerVersionId"],
            )
            return {
                "containerVersionId": result["containerVersion"]["containerVersionId"],
                "name": result["containerVersion"]["name"],
            }
        except Exception as e:
            log_failure("gtm.create_version_failed", error=str(e))
            raise

    def publish_version(
        self, account_id: str, container_id: str, version_id: str
    ) -> dict[str, Any]:
        """Publish a container version."""
        service = self._get_service()

        try:
            result = (
                service.accounts()
                .containers()
                .versions()
                .publish(
                    path=f"accounts/{account_id}/containers/{container_id}/versions/{version_id}",
                )
                .execute()
            )
            logger.info(
                "gtm.version_published",
                account_id=account_id,
                container_id=container_id,
                version_id=version_id,
            )
            return {
                "published": True,
                "versionId": version_id,
                "containerVersionId": result["containerVersion"]["containerVersionId"],
            }
        except Exception as e:
            log_failure("gtm.publish_version_failed", error=str(e), version_id=version_id)
            raise

    def get_container(self, account_id: str, container_id: str) -> dict[str, Any] | None:
        """Get a container by ID."""
        service = self._get_service()
        try:
            result = (
                service.accounts()
                .containers()
                .get(path=f"accounts/{account_id}/containers/{container_id}")
                .execute()
            )
            return {
                "containerId": result["containerId"],
                "publicId": result["publicId"],
                "name": result["name"],
            }
        except Exception as e:
            if "not found" in str(e).lower():
                return None
            raise


class RealGA4DataClient:
    """Real GA4 Data API client for querying analytics data."""

    def __init__(self, credentials_path: str | None = None):
        self.settings = get_settings()
        self.credentials_path = credentials_path or self.settings.google_application_credentials
        self._client: BetaAnalyticsDataClient | None = None

    def _get_client(self) -> BetaAnalyticsDataClient:
        if self._client is None:
            if not self.credentials_path or not os.path.isfile(self.credentials_path):
                raise ValueError(f"Credentials file not found: {self.credentials_path}")

            self._client = BetaAnalyticsDataClient.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
            logger.info("ga4_data.client_initialized")
        return self._client

    def run_report(
        self,
        property_id: str,
        dimensions: list[str],
        metrics: list[str],
        date_range: dict[str, str],
    ) -> dict[str, Any]:
        """Run a GA4 report."""
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            Metric,
            RunReportRequest,
        )

        client = self._get_client()

        request = RunReportRequest(
            property=property_id,
            dimensions=[Dimension(name=d) for d in dimensions],
            metrics=[Metric(name=m) for m in metrics],
            date_ranges=[DateRange(start_date=date_range["start"], end_date=date_range["end"])],
        )

        try:
            response = client.run_report(request)

            rows = []
            for row in response.rows:
                row_data = {}
                for i, dim in enumerate(dimensions):
                    row_data[dim] = row.dimension_values[i].value
                for i, metric in enumerate(metrics):
                    row_data[metric] = row.metric_values[i].value
                rows.append(row_data)

            return {
                "rows": rows,
                "rowCount": len(rows),
                "dimensions": dimensions,
                "metrics": metrics,
            }
        except Exception as e:
            log_failure("ga4_data.run_report_failed", error=str(e), property_id=property_id)
            raise
