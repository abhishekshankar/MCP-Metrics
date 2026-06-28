"""Initial schema migration."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("environment", sa.String(50), nullable=False),
        sa.Column("blueprint", sa.String(100), nullable=True),
        sa.Column("consent_preset", sa.String(50), nullable=False),
        sa.Column("ga4_property_id", sa.String(100), nullable=True),
        sa.Column("ga4_measurement_id", sa.String(50), nullable=True),
        sa.Column("ga4_data_stream_id", sa.String(100), nullable=True),
        sa.Column("gtm_container_id", sa.String(50), nullable=True),
        sa.Column("gtm_container_public_id", sa.String(50), nullable=True),
        sa.Column("gtm_workspace_id", sa.String(50), nullable=True),
        sa.Column("gtm_latest_version_id", sa.String(50), nullable=True),
        sa.Column("gtm_snippets", sa.JSON(), nullable=True),
        sa.Column("primary_domain", sa.String(255), nullable=True),
        sa.Column("linked_domains", sa.JSON(), nullable=True),
        sa.Column("bigquery_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bigquery_project", sa.String(255), nullable=True),
        sa.Column("bigquery_dataset", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("config_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sites_domain", "sites", ["domain"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("actor_type", sa.String(50), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_site_id", "audit_logs", ["site_id"])
    op.create_index("ix_audit_logs_domain", "audit_logs", ["domain"])
    op.create_index("ix_audit_logs_operation", "audit_logs", ["operation"])

    op.create_table(
        "blueprint_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("blueprint_name", sa.String(100), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("gtm_version_id", sa.String(50), nullable=True),
        sa.Column("config_snapshot", sa.JSON(), nullable=False),
        sa.Column("gtm_config_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_blueprint_versions_site_id", "blueprint_versions", ["site_id"])

    op.create_table(
        "health_check_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("event_count_24h", sa.Integer(), nullable=True),
        sa.Column("conversion_count_24h", sa.Integer(), nullable=True),
        sa.Column("traffic_sessions_24h", sa.Integer(), nullable=True),
        sa.Column("anomaly_flags", sa.JSON(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("baseline_conversion_rate", sa.Float(), nullable=True),
        sa.Column("message", sa.String(500), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_check_results_site_id", "health_check_results", ["site_id"])


def downgrade() -> None:
    op.drop_table("health_check_results")
    op.drop_table("blueprint_versions")
    op.drop_table("audit_logs")
    op.drop_table("sites")
