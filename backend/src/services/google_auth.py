"""Google Cloud authentication provider with token refresh."""

from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.credentials import Credentials
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from config import Settings, get_settings


class GoogleAuthError(Exception):
    """Raised when Google credentials cannot be loaded or refreshed."""


_MOCK_SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "mock-project",
    "private_key_id": "mock",
    "private_key": (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHB/8aG3j8f4\n"
        "-----END RSA PRIVATE KEY-----\n"
    ),
    "client_email": "mock@mock-project.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
}


class GoogleAuthProvider:
    """Load service account credentials and provide refreshed access tokens."""

    def __init__(
        self,
        settings: Settings | None = None,
        credentials_path: str | None = None,
        scopes: list[str] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self.credentials_path = credentials_path or self._settings.google_application_credentials
        self.scopes = scopes or self._settings.scope_list
        self._credentials: Credentials | None = None

    def get_credentials(self) -> Credentials:
        """Return valid credentials, loading or refreshing as needed."""
        return self.load_credentials()

    def load_credentials(self) -> Credentials:
        if self._credentials is not None and self._credentials.valid:
            return self._credentials

        if self._credentials and self._credentials.expired and self._credentials.refresh_token:
            self._credentials.refresh(Request())
            return self._credentials

        creds_data = self._load_credentials_json()
        if creds_data:
            self._credentials = service_account.Credentials.from_service_account_info(
                creds_data, scopes=self.scopes
            )
        elif self.credentials_path and Path(self.credentials_path).is_file():
            self._credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=self.scopes
            )
        elif self._settings.mock_google_apis:
            self._credentials = service_account.Credentials.from_service_account_info(
                _MOCK_SERVICE_ACCOUNT, scopes=self.scopes
            )
        else:
            raise GoogleAuthError(
                "Google credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS "
                "or GOOGLE_SERVICE_ACCOUNT_JSON."
            )

        return self._credentials

    def get_access_token(self) -> str:
        credentials = self.load_credentials()
        if not credentials.valid:
            credentials.refresh(Request())
            self._credentials = credentials
        token = credentials.token
        if not token:
            raise GoogleAuthError("Failed to obtain Google access token after refresh")
        return token

    def refresh_if_needed(self) -> Credentials:
        credentials = self.load_credentials()
        if not credentials.valid:
            credentials.refresh(Request())
            self._credentials = credentials
        return credentials

    def _load_credentials_json(self) -> dict | None:
        env_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        if env_json:
            try:
                return json.loads(env_json)
            except json.JSONDecodeError as exc:
                raise GoogleAuthError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON") from exc
        return None
