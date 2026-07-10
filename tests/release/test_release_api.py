import pytest
from fastapi.testclient import TestClient
from app.main import app
import os

@pytest.fixture(autouse=True)
def disable_poc_bypass(monkeypatch):
    monkeypatch.setenv("ENABLE_POC_BYPASS", "false")
    monkeypatch.setenv("TESTING", "false")

client = TestClient(app)


def test_openapi_schema_consistency():
    """
    Validates that the OpenAPI schema can be generated and is well-formed.
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert len(schema["paths"]) > 0


@pytest.fixture
def api_paths():
    response = client.get("/openapi.json")
    schema = response.json()
    return schema["paths"]


def test_all_endpoints_exist_and_authorized(api_paths, monkeypatch):
    """
    Checks that every endpoint exists (no 404s) and enforces authentication
    if it's not a public endpoint like /health or /openapi.json.
    """
    monkeypatch.delenv("TESTING", raising=False)
    public_endpoints = [
        "/",
        "/health",
        "/health/live",
        "/health/ready",
        "/ready",
        "/live",
        "/metrics",
        "/embedding-test",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/token",
    ]

    for path, methods in api_paths.items():
        for method, operation in methods.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue

            # Send an unauthenticated request to check auth enforcement
            if method.lower() == "get":
                res = client.get(path)
            elif method.lower() == "post":
                res = client.post(path, json={})
            elif method.lower() == "put":
                res = client.put(path, json={})
            elif method.lower() == "delete":
                res = client.delete(path)
            elif method.lower() == "patch":
                res = client.patch(path, json={})

            if path in public_endpoints:
                # Public endpoints should not return 401
                assert res.status_code != 401, f"Public endpoint {path} returned 401"
                assert res.status_code != 404, f"Public endpoint {path} returned 404"
            else:
                # Protected endpoints should return 401/403 or 422 (if payload validation happens before auth in some frameworks, though usually auth is first)
                assert res.status_code in [
                    401,
                    403,
                    422,
                    405,
                ], f"Protected endpoint {method.upper()} {path} returned {res.status_code} without auth"
