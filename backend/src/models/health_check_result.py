"""Health check result model."""

from datetime import datetime

from database import Base
from sqlalchemy import JSON, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column


class HealthCheckResult(Base):
    __tablename__ = "health_check_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(50))
    event_count_24h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversion_count_24h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    traffic_sessions_24h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anomaly_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    baseline_conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
