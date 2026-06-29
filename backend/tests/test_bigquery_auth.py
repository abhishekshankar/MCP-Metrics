"""Sprint 11: BigQuery and API auth tests."""

ADMIN_HEADERS = {"X-API-Key": "test-admin-key"}


def test_bigquery_enable(client):
    response = client.post(
        "/sites",
        json={
            "domain": "bq-test.com",
            "name": "BQ Test",
            "blueprint": "saas",
            "enable_bigquery": True,
            "bigquery_project": "my-project",
            "bigquery_dataset": "analytics_export",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["bigquery_enabled"] is True


def test_auth_info(client):
    response = client.get("/auth/info", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert "roles" in response.json()


def test_unauthorized_without_api_key(client):
    """Test that requests without API key are rejected."""
    response = client.get("/sites")
    assert response.status_code == 401


def test_unauthorized_with_invalid_key(client):
    """Test that requests with invalid API key are rejected."""
    response = client.get("/sites", headers={"X-API-Key": "invalid-key"})
    assert response.status_code == 401
