"""GoogleAuthProvider tests."""

import json
from unittest.mock import MagicMock, patch

import pytest
from services.google_auth import GoogleAuthError, GoogleAuthProvider


@pytest.fixture
def google_service_account_info() -> dict:
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key-id",
        "private_key": (
            "-----BEGIN PRIVATE KEY-----\n"
            "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7\n"
            "-----END PRIVATE KEY-----\n"
        ),
        "client_email": "analytics@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }


def test_load_credentials_from_json_env(monkeypatch, google_service_account_info) -> None:
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", json.dumps(google_service_account_info))
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setenv("MOCK_GOOGLE_APIS", "false")
    get_settings = __import__("config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    with patch(
        "services.google_auth.service_account.Credentials.from_service_account_info"
    ) as mock_from_info:
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.token = "test-token"
        mock_from_info.return_value = mock_credentials

        provider = GoogleAuthProvider()
        credentials = provider.load_credentials()

        assert credentials is mock_credentials
        mock_from_info.assert_called_once()


def test_load_credentials_from_file_env(monkeypatch, google_service_account_info, tmp_path) -> None:
    creds_file = tmp_path / "service-account.json"
    creds_file.write_text(json.dumps(google_service_account_info))
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds_file))
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.setenv("MOCK_GOOGLE_APIS", "false")
    get_settings = __import__("config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    with patch(
        "services.google_auth.service_account.Credentials.from_service_account_file"
    ) as mock_from_file:
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_from_file.return_value = mock_credentials

        provider = GoogleAuthProvider()
        credentials = provider.load_credentials()

        assert credentials is mock_credentials
        mock_from_file.assert_called_once_with(str(creds_file), scopes=provider.scopes)


def test_missing_credentials_raises_when_mock_disabled(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.setenv("MOCK_GOOGLE_APIS", "false")
    get_settings = __import__("config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    provider = GoogleAuthProvider()
    with pytest.raises(GoogleAuthError, match="Google credentials not configured"):
        provider.load_credentials()


def test_mock_mode_when_enabled(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.setenv("MOCK_GOOGLE_APIS", "true")
    get_settings = __import__("config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    with patch(
        "services.google_auth.service_account.Credentials.from_service_account_info"
    ) as mock_from_info:
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_from_info.return_value = mock_credentials

        provider = GoogleAuthProvider()
        credentials = provider.load_credentials()

        assert credentials is mock_credentials


def test_refresh_if_needed_refreshes_invalid_credentials(
    monkeypatch, google_service_account_info
) -> None:
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", json.dumps(google_service_account_info))
    monkeypatch.setenv("MOCK_GOOGLE_APIS", "false")
    get_settings = __import__("config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    with patch(
        "services.google_auth.service_account.Credentials.from_service_account_info"
    ) as mock_from_info:
        mock_credentials = MagicMock()
        mock_credentials.valid = False
        mock_from_info.return_value = mock_credentials

        provider = GoogleAuthProvider()
        with patch("services.google_auth.Request"):
            refreshed = provider.refresh_if_needed()

        mock_credentials.refresh.assert_called_once()
        assert refreshed is mock_credentials
