"""Blueprint version model for governance."""

from datetime import datetime

from database import Base
from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column


class BlueprintVersion(Base):
    __tablename__ = "blueprint_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(Integer, index=True)
    blueprint_name: Mapped[str] = mapped_column(String(100))
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    gtm_version_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    config_snapshot: Mapped[dict] = mapped_column(JSON)
    gtm_config_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
