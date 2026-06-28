"""SQLAlchemy model tests."""

from models.audit_log import AuditLog
from models.blueprint_version import BlueprintVersion
from models.health_check_result import HealthCheckResult
from models.site import Site


def test_create_site_with_related_records(db_session) -> None:
    site = Site(
        domain="example.com",
        name="Example Site",
        environment="prod",
        ga4_measurement_id="G-TEST123",
        gtm_container_id="GTM-ABC",
        consent_preset="basic",
        blueprint="saas",
        bigquery_enabled=True,
        bigquery_project="my-project",
        bigquery_dataset="analytics_export",
        linked_domains=["app.example.com"],
        status="active",
    )
    db_session.add(site)
    db_session.flush()

    audit = AuditLog(
        site_id=site.id,
        domain=site.domain,
        operation="site_create",
        actor="pytest",
        details={"domain": "example.com"},
    )
    version = BlueprintVersion(
        site_id=site.id,
        blueprint_name="saas",
        version_number=1,
        config_snapshot={"events": ["page_view"]},
    )
    health = HealthCheckResult(
        site_id=site.id,
        status="healthy",
        event_count_24h=100,
        conversion_count_24h=5,
        anomaly_flags=[],
        metrics={"source": "test"},
    )
    db_session.add_all([audit, version, health])
    db_session.commit()

    saved = db_session.get(Site, site.id)
    assert saved is not None
    assert saved.domain == "example.com"
    assert saved.environment == "prod"
    assert saved.consent_preset == "basic"
    assert saved.ga4_measurement_id == "G-TEST123"


def test_audit_log_persists_without_site(db_session) -> None:
    audit = AuditLog(operation="api_request", actor="cli", details={"command": "list"})
    db_session.add(audit)
    db_session.commit()

    saved = db_session.get(AuditLog, audit.id)
    assert saved is not None
    assert saved.site_id is None
    assert saved.operation == "api_request"
