"""
Authentication endpoint tests.
These are smoke tests that verify the auth endpoints respond correctly.
For full integration tests, configure real Supabase test credentials.
"""
import pytest
from fastapi.testclient import TestClient


def test_signup_validation(client: TestClient):
    """Signup with invalid data returns 422."""
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "not-an-email", "password": "short", "full_name": ""},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_login_missing_fields(client: TestClient):
    """Login with missing fields returns 422."""
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com"})
    assert response.status_code == 422


def test_protected_route_without_token(client: TestClient):
    """Protected route without token returns 401."""
    response = client.get(
        "/api/v1/companies/me",
        headers={"X-Company-ID": "00000000-0000-0000-0000-000000000001"},
    )
    assert response.status_code == 401


def test_protected_route_without_company_header(client: TestClient):
    """Protected route without X-Company-ID returns 401."""
    response = client.get(
        "/api/v1/companies/me",
        headers={"Authorization": "Bearer fake-token"},
    )
    # Will fail at token verification first
    assert response.status_code in (401, 403)


def test_me_unauthenticated(client: TestClient):
    """GET /auth/me without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
