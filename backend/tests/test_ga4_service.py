"""Sprint 2: GA4Service tests."""

from models.site import Site
from services.ga4_service import GA4Service


def test_create_property(db_session):
    service = GA4Service(db_session)
    prop = service.create_property("Test Site", timezone="UTC", currency="USD")
    assert "name" in prop
    assert prop["displayName"] == "Test Site - prod"


def test_create_property_idempotent(db_session):
    service = GA4Service(db_session)
    prop1 = service.create_property("Test Site")
    prop2 = service.create_property("Test Site")
    assert prop1["name"] == prop2["name"]


def test_create_web_data_stream(db_session):
    service = GA4Service(db_session)
    prop = service.create_property("Test Site")
    stream = service.create_web_data_stream(prop["name"], "example.com")
    assert stream["measurementId"].startswith("G-")
    stream2 = service.create_web_data_stream(prop["name"], "example.com")
    assert stream["measurementId"] == stream2["measurementId"]


def test_provision_for_site(db_session):
    service = GA4Service(db_session)
    site = Site(domain="example.com", name="Example", environment="prod", status="pending")
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)

    result = service.provision_for_site(site)
    assert result.ga4_property_id is not None
    assert result.ga4_measurement_id is not None

    # Idempotent re-run
    result2 = service.provision_for_site(site)
    assert result2.ga4_property_id == result.ga4_property_id


def test_audit_log_on_create(db_session):
    from services.audit_service import AuditService

    service = GA4Service(db_session)
    service.create_property("Audit Test")
    audit = AuditService(db_session)
    logs = audit.list_logs(operation="ga4.property.create")
    assert len(logs) >= 1
