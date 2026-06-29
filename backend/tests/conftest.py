"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

os.environ["MOCK_GOOGLE_APIS"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["API_SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_API_KEY"] = "test-admin-key"
os.environ["READONLY_API_KEY"] = "test-readonly-key"

from config import get_settings  # noqa: E402

get_settings.cache_clear()

import models  # noqa: F401, E402
from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_settings():
    os.environ["MOCK_GOOGLE_APIS"] = "true"
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
