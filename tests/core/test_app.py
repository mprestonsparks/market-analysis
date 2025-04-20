"""
Tests for core FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.core.app import app

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

def test_app_title():
    """Test application title and version."""
    assert app.title == "Market Analysis API"
    assert app.version == "1.0.0"

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_cors_headers(client):
    """Test CORS headers are present."""
    test_origin = "http://testserver"
    response = client.options("/health", headers={
        "Origin": test_origin,
        "Access-Control-Request-Method": "GET",
    })
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == test_origin
    assert "access-control-allow-methods" in response.headers
    assert "GET" in response.headers["access-control-allow-methods"]
