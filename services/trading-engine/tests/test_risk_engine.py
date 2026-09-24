"""Tests for the deterministic Risk Engine."""
from datetime import datetime, timedelta, timezone

from services.trading_engine.app.configuration.settings import TradingEngineSettings
from services.trading_engine.app.models.account import Account
from services.trading_engine.app.models.market import InstrumentSpec, MarketQuote
from services.trading_engine.app.models.position import Position, PositionSide
from services.trading_engine.app.models.risk_decision import DecisionType
from services.trading_engine.app.models.signal import Signal, SignalAction
from services.trading_engine.app.models.system_state import SystemState
from services.trading_engine.app.risk.engine import RiskEngine


def get_test_fixture():
    settings = TradingEngineSettings(
        max_risk_per_trade_percent=2.0,
        max_daily_loss_percent=5.0,
        max_drawdown_percent=10.0,
        max_consecutive_losses=3,
        max_concurrent_trades=3,
        max_symbol_exposure_volume=5.0,
        max_portfolio_exposure_volume=10.0,
        max_quote_age_seconds=30.0,
        max_spread=5.0,
    )
    risk_engine = RiskEngine(settings=settings)
    account = Account(
        accountId="TEST-ACC",
        currency="USD",
        balance=100000.0,
        equity=100000.0,
        margin=0.0,
        freeMargin=100000.0,
        drawdownPercent=0.0,
    )
    quote = MarketQuote(
        symbol="XAUUSD",
        bid=2650.00,
        ask=2650.25,
        spread=0.25,
        timestamp=datetime.now(timezone.utc),
        isMarketOpen=True,
    )
    spec = InstrumentSpec(symbol="XAUUSD", contractSize=100.0, minVolume=0.01, maxVolume=50.0)
    return risk_engine, account, quote, spec


def test_valid_trade_approved():
    """Verify a conforming BUY trade is APPROVED when bot is RUNNING."""
    engine, account, quote, spec = get_test_fixture()
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
        takeProfit=2670.25,
        riskPercent=1.0,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
    )
    assert decision.decision == DecisionType.APPROVED
    assert decision.approvedVolume is not None
    assert decision.approvedVolume > 0
    assert "RISK_CHECKS_PASSED" in decision.reasonCodes


def test_wait_signal_rejected_not_executable():
    """Verify WAIT signal is immediately REJECTED and never executable."""
    engine, account, quote, spec = get_test_fixture()
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.WAIT,
        confidence=0.5,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
    )
    assert decision.decision == DecisionType.REJECTED
    assert "WAIT_SIGNAL" in decision.reasonCodes
    assert decision.approvedVolume is None


def test_stopped_bot_rejects():
    """Verify proposal is REJECTED when system state is STOPPED."""
    engine, account, quote, spec = get_test_fixture()
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.STOPPED,
    )
    assert decision.decision == DecisionType.REJECTED
    assert "SYSTEM_STATE_STOPPED" in decision.reasonCodes


def test_emergency_stop_rejects():
    """Verify proposal is strictly REJECTED when in EMERGENCY_STOP."""
    engine, account, quote, spec = get_test_fixture()
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.EMERGENCY_STOP,
    )
    assert decision.decision == DecisionType.REJECTED
    assert "SYSTEM_STATE_EMERGENCY_STOP" in decision.reasonCodes


def test_excessive_risk_rejected():
    """Verify proposal exceeding maxRiskPerTrade is REJECTED."""
    engine, account, quote, spec = get_test_fixture()
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
        riskPercent=3.5,  # Exceeds max 2.0%
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
    )
    assert decision.decision == DecisionType.REJECTED
    assert "RISK_LIMIT_EXCEEDED" in decision.reasonCodes


def test_missing_stop_loss_rejected():
    """Verify proposal without a stop loss is REJECTED."""
    engine, account, quote, spec = get_test_fixture()
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=None,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
    )
    assert decision.decision == DecisionType.REJECTED
    assert "MISSING_STOP_LOSS" in decision.reasonCodes


def test_insufficient_margin_rejected():
    """Verify proposal with insufficient free margin is REJECTED."""
    engine, account, quote, spec = get_test_fixture()
    # Modify account freeMargin to very low
    account.freeMargin = 10.0
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
        riskPercent=1.0,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
    )
    assert decision.decision == DecisionType.REJECTED
    assert "INSUFFICIENT_MARGIN" in decision.reasonCodes


def test_excessive_exposure_rejected():
    """Verify proposal exceeding max concurrent trades or exposure is REJECTED."""
    engine, account, quote, spec = get_test_fixture()
    # Already 3 open positions (max concurrent is 3)
    existing_positions = [
        Position(positionId="P1", symbol="EURUSD", side=PositionSide.BUY, volume=1.0),
        Position(positionId="P2", symbol="GBPUSD", side=PositionSide.BUY, volume=1.0),
        Position(positionId="P3", symbol="USDJPY", side=PositionSide.BUY, volume=1.0),
    ]
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
        riskPercent=0.5,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=existing_positions,
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
    )
    assert decision.decision == DecisionType.REJECTED
    assert "CONCURRENT_TRADES_LIMIT_REACHED" in decision.reasonCodes


def test_daily_loss_limit_halts():
    """Verify reaching daily loss limit HALTS the risk engine."""
    engine, account, quote, spec = get_test_fixture()
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
        daily_loss_percent=5.5,  # Exceeds max 5.0%
    )
    assert decision.decision == DecisionType.HALTED
    assert "DAILY_LOSS_LIMIT_REACHED" in decision.reasonCodes


def test_drawdown_limit_halts():
    """Verify reaching maximum drawdown HALTS the risk engine."""
    engine, account, quote, spec = get_test_fixture()
    account.drawdownPercent = 12.0  # Max is 10.0%
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
    )
    assert decision.decision == DecisionType.HALTED
    assert "MAX_DRAWDOWN_REACHED" in decision.reasonCodes


def test_consecutive_losses_halts():
    """Verify reaching consecutive losses limit HALTS the risk engine."""
    engine, account, quote, spec = get_test_fixture()
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
        consecutive_losses=3,  # Max is 3
    )
    assert decision.decision == DecisionType.HALTED
    assert "CONSECUTIVE_LOSS_LIMIT_REACHED" in decision.reasonCodes


def test_stale_market_data_halts():
    """Verify stale market quote HALTS the risk engine."""
    engine, account, quote, spec = get_test_fixture()
    # Quote from 2 minutes ago (threshold is 30 seconds)
    quote.timestamp = datetime.now(timezone.utc) - timedelta(seconds=120)

    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.8,
        entry=2650.25,
        stopLoss=2640.25,
    )
    decision = engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=[],
        market_quote=quote,
        instrument_spec=spec,
        system_state=SystemState.RUNNING,
    )
    assert decision.decision == DecisionType.HALTED
    assert "MARKET_DATA_STALE" in decision.reasonCodes
