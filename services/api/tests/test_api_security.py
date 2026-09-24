"""Tests for API security boundary, authorization, and broker credential rejection."""
from fastapi.testclient import TestClient

from services.api.app.config import api_settings
from services.api.app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": api_settings.dev_api_key}


def test_unauthorized_request_rejected():
    """Verify missing or invalid API key returns 401 Unauthorized."""
    # No auth header
    res_no_auth = client.get("/api/v1/system/status")
    assert res_no_auth.status_code == 401
    data = res_no_auth.json()
    assert data["error"]["code"] == "UNAUTHORIZED"

    # Wrong auth header
    res_bad_auth = client.get("/api/v1/system/status", headers={"X-API-Key": "wrong-secret"})
    assert res_bad_auth.status_code == 401


def test_broker_credentials_in_headers_rejected():
    """Verify attempt to pass broker credentials in headers is strictly rejected with 400."""
    headers_with_broker = {
        **AUTH_HEADERS,
        "X-Broker-Password": "super_secret_broker_password",
    }
    response = client.get("/api/v1/system/status", headers=headers_with_broker)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "BROKER_CREDENTIALS_FORBIDDEN"


def test_broker_credentials_in_query_rejected():
    """Verify attempt to pass broker credentials in query params is strictly rejected with 400."""
    response = client.get("/api/v1/system/status?broker_login=123456", headers=AUTH_HEADERS)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "BROKER_CREDENTIALS_FORBIDDEN"


def test_correlation_id_propagated():
    """Verify custom X-Correlation-ID is preserved in response headers."""
    custom_id = "test-corr-id-98765"
    response = client.get("/health", headers={"X-Correlation-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_id


def test_secrets_not_leaked_in_responses():
    """Verify system status and health endpoints never leak sensitive keys."""
    res_health = client.get("/health")
    assert "password" not in res_health.text.lower()
    assert "secret" not in res_health.text.lower()

    res_status = client.get("/api/v1/system/status", headers=AUTH_HEADERS)
    assert "password" not in res_status.text.lower()
    assert "broker_key" not in res_status.text.lower()
