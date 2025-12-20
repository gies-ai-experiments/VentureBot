"""
Basic API health check tests for VentureBot.

This test file verifies that the core API endpoints are accessible
and returning expected responses.
"""
import pytest
from fastapi.testclient import TestClient
from services.api_gateway.app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_healthcheck_endpoint(client):
    """Test that the health check endpoint returns OK status."""
    response = client.get("/healthz")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_structure():
    """Test that the FastAPI app is properly configured."""
    # Verify app exists and has expected attributes
    assert app is not None
    assert app.title is not None
    
    # Verify routers are included
    routes = [route.path for route in app.routes]
    assert "/healthz" in routes
    # Check for routes starting with /api/chat
    assert any(route.startswith("/api/chat") for route in routes)
