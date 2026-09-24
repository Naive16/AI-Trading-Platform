"""Tests for GET /health endpoint."""
from fastapi.testclient import TestClient

from services.api.app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint strictly returns simulation environment with trading disabled."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == "simulation"
    assert data["liveTrading"] is False
    assert data["mt5Connected"] is False
    assert data["brokerConnected"] is False
