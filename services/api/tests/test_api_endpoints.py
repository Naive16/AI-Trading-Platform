"""Tests for all core API endpoints."""
from fastapi.testclient import TestClient

from services.api.app.config import api_settings
from services.api.app.main import app
from services.trading_engine.app.main import engine_instance
from services.trading_engine.app.models.system_state import SystemState

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": api_settings.dev_api_key}


def setup_function():
    """Reset engine state before each test."""
    engine_instance.portfolio.reset()
    engine_instance.execution.clear()
    engine_instance.stop_bot()


def test_system_status():
    """Verify /api/v1/system/status returns full system state and limits."""
    response = client.get("/api/v1/system/status", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "STOPPED"
    assert data["environment"] == "simulation"
    assert data["liveTrading"] is False
    assert "limits" in data
    assert "account" in data


def test_bot_lifecycle_transitions():
    """Verify bot start, pause, stop, and emergency stop state transitions."""
    # 1. Start bot -> RUNNING
    start_res = client.post("/api/v1/bot/start", headers=AUTH_HEADERS)
    assert start_res.status_code == 200
    assert start_res.json()["currentState"] == "RUNNING"
    assert engine_instance.system_state == SystemState.RUNNING

    # 2. Pause bot -> PAUSED
    pause_res = client.post("/api/v1/bot/pause", headers=AUTH_HEADERS)
    assert pause_res.status_code == 200
    assert pause_res.json()["currentState"] == "PAUSED"
    assert engine_instance.system_state == SystemState.PAUSED

    # 3. Stop bot -> STOPPED
    stop_res = client.post("/api/v1/bot/stop", headers=AUTH_HEADERS)
    assert stop_res.status_code == 200
    assert stop_res.json()["currentState"] == "STOPPED"
    assert engine_instance.system_state == SystemState.STOPPED

    # 4. Emergency Stop -> EMERGENCY_STOP
    emerg_res = client.post("/api/v1/emergency/stop", headers=AUTH_HEADERS)
    assert emerg_res.status_code == 200
    assert emerg_res.json()["currentState"] == "EMERGENCY_STOP"
    assert engine_instance.system_state == SystemState.EMERGENCY_STOP


def test_signals_evaluate_endpoint():
    """Verify /api/v1/signals/evaluate returns validation and risk evaluation."""
    payload = {
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "action": "BUY",
        "confidence": 0.82,
        "entry": 2650.25,
        "stopLoss": 2640.25,
        "takeProfit": 2670.25,
        "riskPercent": 1.0,
    }
    response = client.post("/api/v1/signals/evaluate", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["isValid"] is True
    assert "riskDecision" in data


def test_risk_evaluate_endpoint():
    """Verify /api/v1/risk/evaluate returns structured RiskDecision."""
    payload = {
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "action": "BUY",
        "confidence": 0.85,
        "entry": 2650.25,
        "stopLoss": 2640.25,
        "riskPercent": 1.0,
    }
    response = client.post("/api/v1/risk/evaluate", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "reasonCodes" in data


def test_orders_simulate_endpoint_flow():
    """Verify /api/v1/orders/simulate completes mock execution when bot is started."""
    # Start bot
    client.post("/api/v1/bot/start", headers=AUTH_HEADERS)

    payload = {
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "action": "BUY",
        "confidence": 0.88,
        "entry": 2650.25,
        "stopLoss": 2640.25,
        "takeProfit": 2670.25,
        "riskPercent": 1.0,
    }
    response = client.post("/api/v1/orders/simulate", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED_AND_EXECUTED"
    assert data["orderAcknowledgement"]["status"] == "FILLED"
    assert data["position"] is not None

    # Check positions endpoint now returns the open position
    pos_res = client.get("/api/v1/positions", headers=AUTH_HEADERS)
    assert pos_res.status_code == 200
    positions = pos_res.json()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "XAUUSD"


def test_orders_simulate_stopped_bot_rejects():
    """Verify /api/v1/orders/simulate rejects when bot is STOPPED."""
    payload = {
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "action": "BUY",
        "confidence": 0.88,
        "entry": 2650.25,
        "stopLoss": 2640.25,
    }
    response = client.post("/api/v1/orders/simulate", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"
    assert "SYSTEM_STATE_STOPPED" in data["riskDecision"]["reasonCodes"]
    assert data["position"] is None


def test_malformed_request_fails_validation():
    """Verify malformed payload returns 422 with structured error format."""
    payload = {
        "symbol": "XAUUSD",
        "action": "INVALID_ACTION",  # Malformed
    }
    response = client.post("/api/v1/signals/evaluate", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "correlationId" in data
