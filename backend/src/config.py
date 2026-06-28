"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT_DIR / "docs"
BLUEPRINTS_DIR = DOCS_DIR / "blueprints"
RECIPES_DIR = DOCS_DIR / "recipes"
PLUGINS_DIR = Path(__file__).resolve().parent / "plugins"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://analytics:analytics@localhost:5433/analytics_mcp"
    google_application_credentials: str | None = None
    google_cloud_project: str | None = None
    google_scopes: str = (
        "https://www.googleapis.com/auth/analytics.edit,"
        "https://www.googleapis.com/auth/tagmanager.edit.containers,"
        "https://www.googleapis.com/auth/bigquery"
    )
    gtm_account_id: str = "1234567"
    mock_google_apis: bool = True
    api_secret_key: str = "dev-secret-key"
    admin_api_key: str = "admin-key"
    readonly_api_key: str = "readonly-key"
    alert_webhook_url: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    alert_email_to: str | None = None
    health_check_interval_minutes: int = 60
    plugin_blueprints_dir: str | None = None

    # Retry configuration for Google API calls
    api_retry_attempts: int = 3
    api_retry_backoff_base: float = 1.0  # seconds
    api_retry_max_wait: float = 30.0  # seconds

    # KMS/Secrets Manager configuration
    kms_provider: str | None = None  # "aws", "gcp", "azure", or None for env-only
    aws_region: str = "us-east-1"
    aws_secret_name: str | None = None
    gcp_kms_key_id: str | None = None
    azure_key_vault_url: str | None = None
    azure_secret_name: str | None = None

    @property
    def scope_list(self) -> list[str]:
        return [s.strip() for s in self.google_scopes.split(",") if s.strip()]

    @property
    def blueprints_path(self) -> Path:
        if self.plugin_blueprints_dir:
            return Path(self.plugin_blueprints_dir)
        return BLUEPRINTS_DIR


@lru_cache
def get_settings() -> Settings:
    return Settings()
