"""Sprint 5: Site API and CLI integration tests."""

def test_create_site_api(client):
    response = client.post(
        "/sites",
        json={
            "domain": "example.com",
            "name": "Example Site",
            "environment": "prod",
            "blueprint": "saas",
            "consent_preset": "none",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "example.com"
    assert data["ga4_measurement_id"] is not None
    assert data["gtm_container_public_id"] is not None
    assert data["snippets"] is not None


def test_list_sites_api(client):
    client.post("/sites", json={"domain": "list-test.com", "name": "List Test", "blueprint": "saas"})
    response = client.get("/sites")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_site_api(client):
    client.post("/sites", json={"domain": "status-test.com", "name": "Status Test", "blueprint": "saas"})
    response = client.get("/sites/status-test.com")
    assert response.status_code == 200
    assert response.json()["domain"] == "status-test.com"


def test_apply_blueprint_api(client):
    client.post("/sites", json={"domain": "apply-test.com", "name": "Apply Test", "blueprint": "saas"})
    response = client.post("/sites/apply-test.com/blueprint", json={"blueprint": "ecommerce"})
    assert response.status_code == 200
    assert response.json()["blueprint"] == "ecommerce"


def test_create_idempotent(client):
    body = {"domain": "idempotent.com", "name": "Idempotent", "blueprint": "saas"}
    r1 = client.post("/sites", json=body)
    r2 = client.post("/sites", json=body)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json().get("reused") is True
