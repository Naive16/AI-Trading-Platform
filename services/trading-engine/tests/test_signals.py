"""Tests for signal validation."""
import pytest
from pydantic import ValidationError

from services.trading_engine.app.models.signal import Signal, SignalAction
from services.trading_engine.app.signals.validator import SignalValidator


def test_buy_signal_valid():
    """Verify valid BUY signal passes validation."""
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.85,
        entry=2650.00,
        stopLoss=2640.00,
        takeProfit=2670.00,
        riskPercent=0.5,
        strategy="gold_momentum",
    )
    is_valid, errors = SignalValidator.validate_signal(signal)
    assert is_valid is True
    assert len(errors) == 0


def test_sell_signal_valid():
    """Verify valid SELL signal passes validation."""
    signal = Signal(
        symbol="EURUSD",
        timeframe="H1",
        action=SignalAction.SELL,
        confidence=0.72,
        entry=1.0850,
        stopLoss=1.0900,
        takeProfit=1.0750,
        riskPercent=1.0,
        strategy="trend_follower",
    )
    is_valid, errors = SignalValidator.validate_signal(signal)
    assert is_valid is True
    assert len(errors) == 0


def test_wait_signal_valid_structure():
    """Verify WAIT is a valid signal structure."""
    signal = Signal(
        symbol="USDJPY",
        timeframe="M5",
        action=SignalAction.WAIT,
        confidence=0.50,
    )
    is_valid, errors = SignalValidator.validate_signal(signal)
    assert is_valid is True
    assert len(errors) == 0


def test_malformed_signal_invalid_action():
    """Verify unsupported action fails schema validation."""
    with pytest.raises(ValidationError):
        Signal(
            symbol="XAUUSD",
            timeframe="M15",
            action="HOLD",  # type: ignore[arg-type]
            confidence=0.8,
        )


def test_malformed_signal_invalid_confidence():
    """Verify out-of-range confidence fails validation."""
    with pytest.raises(ValidationError):
        Signal(
            symbol="XAUUSD",
            timeframe="M15",
            action=SignalAction.BUY,
            confidence=1.5,  # must be <= 1.0
        )


def test_malformed_signal_negative_risk():
    """Verify negative risk percentage is rejected."""
    with pytest.raises(ValidationError):
        Signal(
            symbol="XAUUSD",
            timeframe="M15",
            action=SignalAction.BUY,
            confidence=0.5,
            riskPercent=-1.0,
        )


def test_invalid_stop_loss_geometry():
    """Verify BUY with stop loss >= entry is detected as invalid."""
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.00,
        stopLoss=2655.00,  # Invalid: above entry for BUY
    )
    is_valid, errors = SignalValidator.validate_signal(signal)
    assert is_valid is False
    assert any("INVALID_BUY_STOP_LOSS_MUST_BE_BELOW_ENTRY" in e for e in errors)
