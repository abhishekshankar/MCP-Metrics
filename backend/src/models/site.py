"""Site model."""

from datetime import datetime

from database import Base
from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255))
    environment: Mapped[str] = mapped_column(String(50), default="prod")
    blueprint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    consent_preset: Mapped[str] = mapped_column(String(50), default="none")

    # GA4
    ga4_property_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ga4_measurement_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ga4_data_stream_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # GTM
    gtm_container_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gtm_container_public_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gtm_workspace_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gtm_latest_version_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gtm_snippets: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Cross-domain
    primary_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_domains: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # BigQuery
    bigquery_enabled: Mapped[bool] = mapped_column(default=False)
    bigquery_project: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bigquery_dataset: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Metadata
    status: Mapped[str] = mapped_column(String(50), default="pending")
    config_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def site_key(self) -> str:
        return f"{self.domain}:{self.environment}"
