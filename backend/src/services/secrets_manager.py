"""KMS and Secrets Manager integration for secure credential storage."""

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from config import get_settings
from observability.logging import log_failure, logger


class SecretsProvider(ABC):
    """Abstract base class for secrets providers."""

    @abstractmethod
    def get_secret(self, secret_name: str) -> dict[str, Any] | None:
        """Retrieve and parse a secret as JSON."""
        pass

    @abstractmethod
    def get_secret_string(self, secret_name: str) -> str | None:
        """Retrieve a secret as a plain string."""
        pass


class AWSSecretsProvider(SecretsProvider):
    """AWS Secrets Manager provider."""

    def __init__(self, region: str):
        self.region = region
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client("secretsmanager", region_name=self.region)
            except ImportError:
                raise ImportError("boto3 is required for AWS Secrets Manager support")
        return self._client

    def get_secret(self, secret_name: str) -> dict[str, Any] | None:
        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_name)
            secret_string = response.get("SecretString")
            if secret_string:
                return json.loads(secret_string)
            return None
        except Exception as e:
            log_failure("aws.secrets.get_failed", error=str(e), secret=secret_name)
            return None

    def get_secret_string(self, secret_name: str) -> str | None:
        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_name)
            return response.get("SecretString")
        except Exception as e:
            log_failure("aws.secrets.get_failed", error=str(e), secret=secret_name)
            return None


class GCPSecretsProvider(SecretsProvider):
    """Google Cloud Secret Manager provider."""

    def __init__(self, project_id: str | None = None):
        self.project_id = project_id
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google.cloud import secretmanager
                self._client = secretmanager.SecretManagerServiceClient()
            except ImportError:
                raise ImportError("google-cloud-secret-manager is required for GCP Secret Manager support")
        return self._client

    def get_secret(self, secret_name: str) -> dict[str, Any] | None:
        try:
            client = self._get_client()
            project = self.project_id or get_settings().google_cloud_project
            if not project:
                raise ValueError("Google Cloud project ID is required")
            name = f"projects/{project}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")
            return json.loads(payload)
        except Exception as e:
            log_failure("gcp.secrets.get_failed", error=str(e), secret=secret_name)
            return None

    def get_secret_string(self, secret_name: str) -> str | None:
        try:
            client = self._get_client()
            project = self.project_id or get_settings().google_cloud_project
            if not project:
                raise ValueError("Google Cloud project ID is required")
            name = f"projects/{project}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            log_failure("gcp.secrets.get_failed", error=str(e), secret=secret_name)
            return None


class AzureKeyVaultProvider(SecretsProvider):
    """Azure Key Vault provider."""

    def __init__(self, vault_url: str):
        self.vault_url = vault_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient
                credential = DefaultAzureCredential()
                self._client = SecretClient(vault_url=self.vault_url, credential=credential)
            except ImportError:
                raise ImportError("azure-identity and azure-keyvault-secrets are required for Azure Key Vault support")
        return self._client

    def get_secret(self, secret_name: str) -> dict[str, Any] | None:
        try:
            client = self._get_client()
            secret = client.get_secret(secret_name)
            return json.loads(secret.value) if secret.value else None
        except Exception as e:
            log_failure("azure.keyvault.get_failed", error=str(e), secret=secret_name)
            return None

    def get_secret_string(self, secret_name: str) -> str | None:
        try:
            client = self._get_client()
            secret = client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            log_failure("azure.keyvault.get_failed", error=str(e), secret=secret_name)
            return None


class EnvironmentSecretsProvider(SecretsProvider):
    """Fallback provider that reads from environment variables."""

    def get_secret(self, secret_name: str) -> dict[str, Any] | None:
        """Read from env var as JSON."""
        value = os.getenv(secret_name)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def get_secret_string(self, secret_name: str) -> str | None:
        return os.getenv(secret_name)


class CredentialsManager:
    """Manager for retrieving Google service account credentials from various sources."""

    _provider: SecretsProvider | None = None

    @classmethod
    def get_provider(cls) -> SecretsProvider:
        if cls._provider is None:
            settings = get_settings()
            provider_type = settings.kms_provider

            if provider_type == "aws":
                cls._provider = AWSSecretsProvider(settings.aws_region)
                logger.info("secrets.provider.initialized", provider="aws", region=settings.aws_region)
            elif provider_type == "gcp":
                cls._provider = GCPSecretsProvider(settings.google_cloud_project)
                logger.info("secrets.provider.initialized", provider="gcp", project=settings.google_cloud_project)
            elif provider_type == "azure":
                if not settings.azure_key_vault_url:
                    raise ValueError("AZURE_KEY_VAULT_URL is required for Azure provider")
                cls._provider = AzureKeyVaultProvider(settings.azure_key_vault_url)
                logger.info("secrets.provider.initialized", provider="azure")
            else:
                cls._provider = EnvironmentSecretsProvider()
                logger.info("secrets.provider.initialized", provider="environment")

        return cls._provider

    @classmethod
    def get_google_credentials(cls) -> dict[str, Any] | None:
        """Retrieve Google service account credentials from configured source."""
        settings = get_settings()
        provider = cls.get_provider()

        # Try KMS/Secrets Manager first if configured
        if settings.kms_provider == "aws" and settings.aws_secret_name:
            secret = provider.get_secret(settings.aws_secret_name)
            if secret:
                logger.info("credentials.loaded_from_kms", provider="aws")
                return secret

        if settings.kms_provider == "gcp":
            # For GCP, we use the default credentials or workload identity
            # Credentials are typically handled by the environment/GKE
            logger.info("credentials.using_gcp_default")
            return None  # Signal to use default credentials

        if settings.kms_provider == "azure" and settings.azure_secret_name:
            secret = provider.get_secret(settings.azure_secret_name)
            if secret:
                logger.info("credentials.loaded_from_kms", provider="azure")
                return secret

        # Fallback to environment variable (file path or inline JSON)
        if settings.google_application_credentials:
            creds_path = settings.google_application_credentials
            if os.path.isfile(creds_path):
                with open(creds_path) as f:
                    return json.load(f)
            else:
                # Try parsing as inline JSON
                try:
                    return json.loads(creds_path)
                except json.JSONDecodeError:
                    pass

        return None

    @classmethod
    def get_credential_file_path(cls) -> str | None:
        """Get path to a temporary credentials file (creates one if needed from KMS)."""
        settings = get_settings()

        # If it's already a file path, return it
        if settings.google_application_credentials and os.path.isfile(settings.google_application_credentials):
            return settings.google_application_credentials

        # Try to get from KMS and write to temp file
        creds = cls.get_google_credentials()
        if creds:
            import tempfile
            fd, path = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, "w") as f:
                json.dump(creds, f)
            logger.info("credentials.wrote_temp_file", path=path)
            return path

        return None


def get_credentials_manager() -> CredentialsManager:
    return CredentialsManager()
