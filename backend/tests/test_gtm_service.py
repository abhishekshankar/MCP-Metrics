"""Sprint 3: GTMService tests."""

from models.site import Site
from services.gtm_service import GTMService


def test_create_container(db_session):
    service = GTMService(db_session)
    container = service.create_container("Test", "example.com")
    assert "containerId" in container
    assert container["publicId"].startswith("GTM-")


def test_create_ga4_config_tag(db_session):
    service = GTMService(db_session)
    container = service.create_container("Test", "example.com")
    workspace = service.create_workspace(container["containerId"])
    tag = service.create_ga4_config_tag(
        container["containerId"], workspace["workspaceId"], "G-TEST123"
    )
    assert tag["tagId"] is not None


def test_generate_snippets(db_session):
    service = GTMService(db_session)
    snippets = service.generate_snippets("GTM-ABCD")
    assert "GTM-ABCD" in snippets["head"]
    assert "GTM-ABCD" in snippets["noscript"]


def test_save_and_publish(db_session):
    service = GTMService(db_session)
    container = service.create_container("Test", "example.com")
    workspace = service.create_workspace(container["containerId"])
    service.create_ga4_config_tag(container["containerId"], workspace["workspaceId"], "G-TEST123")
    result = service.save_and_publish(container["containerId"], workspace["workspaceId"])
    assert result["published"]["published"] is True


def test_provision_for_site_e2e(db_session):
    from services.ga4_service import GA4Service

    site = Site(
        domain="gtm-test.com",
        name="GTM Test",
        environment="prod",
        status="pending",
    )
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)

    ga4 = GA4Service(db_session)
    site = ga4.provision_for_site(site)

    gtm = GTMService(db_session)
    site = gtm.provision_for_site(site)

    assert site.gtm_container_id is not None
    assert site.gtm_snippets is not None
    assert "head" in site.gtm_snippets
