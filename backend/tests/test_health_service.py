"""Sprint 9: HealthService tests."""

from models.site import Site
from services.ga4_service import GA4Service
from services.gtm_service import GTMService
from services.health_service import HealthService

ADMIN_HEADERS = {"X-API-Key": "test-admin-key"}
READONLY_HEADERS = {"X-API-Key": "test-readonly-key"}


def _active_site(db_session):
    site = Site(domain="health-test.com", name="Health Test", environment="prod", status="pending")
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    site = GA4Service(db_session).provision_for_site(site)
    site = GTMService(db_session).provision_for_site(site)
    site.status = "active"
    db_session.commit()
    return site


def test_health_check(db_session):
    site = _active_site(db_session)
    health = HealthService(db_session)
    result = health.check_site(site)
    assert result.status in ("healthy", "warning", "critical")
    assert result.event_count_24h is not None


def test_health_api(client):
    client.post(
        "/sites",
        json={"domain": "health-api.com", "name": "Health API", "blueprint": "saas"},
        headers=ADMIN_HEADERS,
    )
    response = client.get("/sites/health-api.com/health", headers=READONLY_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "anomaly_flags" in data


def test_simulate_zero_traffic(db_session):
    site = _active_site(db_session)
    health = HealthService(db_session)
    result = health.simulate_zero_traffic(site)
    assert result.status == "critical"
    assert "zero_events_24h" in result.anomaly_flags
