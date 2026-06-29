"""Sprint 7: Consent, multi-environment, cross-domain tests."""

ADMIN_HEADERS = {"X-API-Key": "test-admin-key"}
READONLY_HEADERS = {"X-API-Key": "test-readonly-key"}


def test_create_with_consent_basic(client):
    response = client.post(
        "/sites",
        json={
            "domain": "consent-test.com",
            "name": "Consent Test",
            "consent_preset": "basic",
            "blueprint": "saas",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["consent_preset"] == "basic"


def test_create_stage_environment(client):
    response = client.post(
        "/sites",
        json={
            "domain": "stage-test.com",
            "name": "Stage Test",
            "environment": "stage",
            "blueprint": "saas",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["environment"] == "stage"


def test_cross_domain_config(client):
    response = client.post(
        "/sites",
        json={
            "domain": "primary.com",
            "name": "Cross Domain",
            "primary_domain": "primary.com",
            "linked_domains": ["shop.primary.com", "app.primary.com"],
            "blueprint": "saas",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["primary_domain"] == "primary.com"
    assert "shop.primary.com" in data["linked_domains"]


def test_describe_includes_consent(client):
    client.post(
        "/sites",
        json={
            "domain": "describe-consent.com",
            "name": "Describe",
            "consent_preset": "advanced",
            "blueprint": "saas",
        },
        headers=ADMIN_HEADERS,
    )
    response = client.get("/sites/describe-consent.com/describe", headers=READONLY_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["consent_preset"] == "advanced"
    assert "consent_explanation" in data
