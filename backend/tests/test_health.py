"""Tests for the SOUL API health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_successful_response():
    response = client.get("/health")

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["status"] == "ok"
    assert response_data["service"]
    assert response_data["version"]
