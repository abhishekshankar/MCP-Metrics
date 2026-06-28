"""Sprint 7: Consent, multi-environment, cross-domain tests."""

def test_create_with_consent_basic(client):
    response = client.post(
        "/sites",
        json={
            "domain": "consent-test.com",
            "name": "Consent Test",
            "consent_preset": "basic",
            "blueprint": "saas",
        },
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
    )
    response = client.get("/sites/describe-consent.com/describe")
    assert response.status_code == 200
    data = response.json()
    assert data["consent_preset"] == "advanced"
    assert "consent_explanation" in data
