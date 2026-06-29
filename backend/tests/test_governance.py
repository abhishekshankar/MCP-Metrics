"""Sprint 8: Governance tests."""

from models.site import Site
from services.blueprint_service import BlueprintService
from services.ga4_service import GA4Service
from services.governance_service import GovernanceService
from services.gtm_service import GTMService

ADMIN_HEADERS = {"X-API-Key": "test-admin-key"}
READONLY_HEADERS = {"X-API-Key": "test-readonly-key"}


def _setup_site(db_session):
    site = Site(domain="gov-test.com", name="Gov Test", environment="prod", status="pending")
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    site = GA4Service(db_session).provision_for_site(site)
    site = GTMService(db_session).provision_for_site(site)
    BlueprintService(db_session).apply(site, "saas")
    return site


def test_audit_log_api(client):
    client.post(
        "/sites",
        json={"domain": "audit-test.com", "name": "Audit", "blueprint": "saas"},
        headers=ADMIN_HEADERS,
    )
    response = client.get("/audit", params={"domain": "audit-test.com"}, headers=READONLY_HEADERS)
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) > 0
    assert any("site.create" in log["operation"] or "ga4" in log["operation"] for log in logs)


def test_rollback(db_session):
    site = _setup_site(db_session)
    governance = GovernanceService(db_session)
    history = governance.get_version_history(site.id)
    assert len(history) >= 1

    result = governance.rollback(site, 1)
    assert result["rolled_back_to_version"] == 1


def test_rollback_api(client):
    client.post(
        "/sites",
        json={"domain": "rollback-test.com", "name": "Rollback", "blueprint": "saas"},
        headers=ADMIN_HEADERS,
    )
    response = client.post(
        "/sites/rollback-test.com/rollback", json={"version": 1}, headers=ADMIN_HEADERS
    )
    assert response.status_code == 200


def test_gtm_diff(db_session):
    site = _setup_site(db_session)
    governance = GovernanceService(db_session)
    BlueprintService(db_session).apply(site, "ecommerce")
    diff = governance.diff_gtm("1", "2", site.gtm_container_id)
    assert "before_version_id" in diff
