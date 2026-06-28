"""Sprint 11: BigQuery and API auth tests."""

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
    )
    assert response.status_code == 200
    assert response.json()["bigquery_enabled"] is True


def test_auth_info(client):
    response = client.get("/auth/info")
    assert response.status_code == 200
    assert "roles" in response.json()


def test_unauthorized_with_auth_disabled(client, monkeypatch):
    from config import get_settings

    monkeypatch.setenv("MOCK_GOOGLE_APIS", "false")
    get_settings.cache_clear()
    response = client.get("/sites")
    assert response.status_code == 401
    monkeypatch.setenv("MOCK_GOOGLE_APIS", "true")
    get_settings.cache_clear()
