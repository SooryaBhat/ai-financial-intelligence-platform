"""
Pytest configuration and shared fixtures.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """
    Fixture that returns Authorization headers for a test user.
    Replace the token value with a real test JWT from your Supabase project
    for integration tests.
    """
    return {
        "Authorization": "Bearer test-jwt-token",
        "X-Company-ID": "00000000-0000-0000-0000-000000000001",
    }
