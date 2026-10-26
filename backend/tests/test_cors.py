"""
CORS and preflight tests for ALLADIN production and local origins.
Validates headers, methods, credentials, and preflight handling.
"""
from fastapi.testclient import TestClient

PROD_ORIGIN = "https://ai-financial-intelligence-platform-8gku08g6h.vercel.app"


def test_cors_preflight_production_origin(client: TestClient):
    """OPTIONS preflight for production Vercel frontend succeeds with 200 and correct CORS headers."""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": PROD_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization,x-company-id",
        },
    )
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert headers.get("access-control-allow-credentials") == "true"
    allowed_methods = headers.get("access-control-allow-methods", "")
    assert "POST" in allowed_methods
    assert "OPTIONS" in allowed_methods
    allowed_headers = headers.get("access-control-allow-headers", "").lower()
    assert "content-type" in allowed_headers
    assert "authorization" in allowed_headers
    assert "x-company-id" in allowed_headers


def test_cors_actual_post_request_production_origin(client: TestClient):
    """POST request from production Vercel origin includes Access-Control-Allow-Origin header."""
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": PROD_ORIGIN},
        json={"email": "invalid_format", "password": "short"},
    )
    # The request should have CORS headers regardless of endpoint validation response
    assert response.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallowed_origin_rejected(client: TestClient):
    """Preflight request from unknown/unauthorized origin is rejected without allow header."""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://malicious-site.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    # Starlette CORSMiddleware returns 400 for disallowed CORS origin on preflight
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_localhost_dev_allowed(client: TestClient):
    """Localhost origin is allowed for local frontend development."""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_no_wildcard_with_credentials(client: TestClient):
    """Access-Control-Allow-Origin must NEVER be wildcard '*' when credentials are true."""
    for origin in [PROD_ORIGIN, "http://localhost:5173"]:
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.headers.get("access-control-allow-origin") != "*"
        assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_vercel_preview_subdomains_allowed(client: TestClient):
    """Vercel production and preview subdomains for ALLADIN are permitted."""
    vercel_origins = [
        "https://ai-financial-intelligence-platform.vercel.app",
        "https://ai-financial-intelligence-platform-8gku08g6h.vercel.app",
        "https://ai-financial-intelligence-platform-git-main.vercel.app",
    ]
    for origin in vercel_origins:
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )
        assert response.status_code == 200, f"Expected 200 for {origin}, got {response.status_code}"
        assert response.headers.get("access-control-allow-origin") == origin

