"""Sprint 4: BlueprintService tests."""

from models.site import Site
from services.blueprint_service import BlueprintService
from services.ga4_service import GA4Service
from services.gtm_service import GTMService


def _provision_site(db_session, domain="blueprint-test.com"):
    site = Site(domain=domain, name="Blueprint Test", environment="prod", status="pending")
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    site = GA4Service(db_session).provision_for_site(site)
    site = GTMService(db_session).provision_for_site(site)
    return site


def test_list_blueprints(db_session):
    service = BlueprintService(db_session)
    blueprints = service.list_available()
    names = [b["name"] for b in blueprints]
    assert "saas" in names
    assert "ecommerce" in names
    assert "content" in names


def test_load_saas_blueprint(db_session):
    service = BlueprintService(db_session)
    bp = service.load("saas")
    assert bp.name == "saas"
    event_names = [e.name for e in bp.events]
    assert "signup_started" in event_names


def test_apply_saas_blueprint(db_session):
    site = _provision_site(db_session)
    service = BlueprintService(db_session)
    result = service.apply(site, "saas")
    assert result["blueprint"] == "saas"
    assert len(result["tags_created"]) > 0
    assert "helper_snippet" in result
    assert result["dataLayer"]["spec"] is not None
