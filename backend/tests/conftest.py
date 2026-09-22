"""
Shared test fixtures for the Spend Tracker test suite.

Creates an isolated in-memory SQLite database for each test session
and provides a pre-authenticated test client.
"""

import secrets
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import ApiKey
from app.main import app


# ── In-memory test database ─────────────────────────────────────────────────

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Yield a test session that rolls back after the request."""
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db():
    """Provide a raw database session for tests that need direct DB access."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def api_key(db) -> str:
    """Create and return a valid API key string."""
    raw_key = secrets.token_urlsafe(32)
    db_key = ApiKey(key=raw_key, name="test-key")
    db.add(db_key)
    db.commit()
    return raw_key


@pytest.fixture()
def auth_headers(api_key) -> dict[str, str]:
    """Return headers dict with a valid X-API-Key."""
    return {"X-API-Key": api_key}


@pytest.fixture()
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)
