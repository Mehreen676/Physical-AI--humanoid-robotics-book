"""
Tests for health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test GET /health endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data


def test_health_response_format(client):
    """Test health response has correct format."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert data["status"] == "healthy"
    assert isinstance(data["timestamp"], str)
    assert data["version"] == "1.0.0"
