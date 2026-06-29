"""Sprint 5: Site API and CLI integration tests."""

# Test API key for authentication
TEST_ADMIN_KEY = "test-admin-key"
TEST_READONLY_KEY = "test-readonly-key"


def get_headers(role="admin"):
    """Get API headers with appropriate key."""
    key = TEST_ADMIN_KEY if role == "admin" else TEST_READONLY_KEY
    return {"X-API-Key": key}


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
        headers=get_headers("admin"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "example.com"
    assert data["ga4_measurement_id"] is not None
    assert data["gtm_container_public_id"] is not None
    assert data["snippets"] is not None


def test_list_sites_api(client):
    client.post(
        "/sites",
        json={"domain": "list-test.com", "name": "List Test", "blueprint": "saas"},
        headers=get_headers("admin"),
    )
    response = client.get("/sites", headers=get_headers("readonly"))
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_site_api(client):
    client.post(
        "/sites",
        json={"domain": "status-test.com", "name": "Status Test", "blueprint": "saas"},
        headers=get_headers("admin"),
    )
    response = client.get("/sites/status-test.com", headers=get_headers("readonly"))
    assert response.status_code == 200
    assert response.json()["domain"] == "status-test.com"


def test_apply_blueprint_api(client):
    client.post(
        "/sites",
        json={"domain": "apply-test.com", "name": "Apply Test", "blueprint": "saas"},
        headers=get_headers("admin"),
    )
    response = client.post(
        "/sites/apply-test.com/blueprint",
        json={"blueprint": "ecommerce"},
        headers=get_headers("admin"),
    )
    assert response.status_code == 200
    assert response.json()["blueprint"] == "ecommerce"


def test_create_idempotent(client):
    body = {"domain": "idempotent.com", "name": "Idempotent", "blueprint": "saas"}
    r1 = client.post("/sites", json=body, headers=get_headers("admin"))
    r2 = client.post("/sites", json=body, headers=get_headers("admin"))
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json().get("reused") is True


def test_unauthorized_without_api_key(client):
    """Test that requests without API key are rejected."""
    response = client.post("/sites", json={"domain": "unauth.com", "name": "Unauth"})
    assert response.status_code == 401


def test_forbidden_readonly_on_admin_endpoint(client):
    """Test that readonly key cannot access admin endpoints."""
    response = client.post(
        "/sites",
        json={"domain": "readonly-test.com", "name": "Readonly Test"},
        headers=get_headers("readonly"),
    )
    assert response.status_code == 403
