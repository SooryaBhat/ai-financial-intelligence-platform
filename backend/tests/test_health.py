"""
Health check tests — validate the app starts correctly.
"""
from fastapi.testclient import TestClient

from app.main import app


def test_health(client: TestClient):
    """The /health endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_root(client: TestClient):
    """The root / endpoint returns 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_docs_accessible(client: TestClient):
    """Swagger UI is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema(client: TestClient):
    """OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AI Financial Intelligence Platform"
