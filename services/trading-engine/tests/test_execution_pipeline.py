"""Tests verifying the strict execution pipeline and non-bypass rules."""
from services.trading_engine.app.configuration.settings import TradingEngineSettings
from services.trading_engine.app.execution.mock_adapter import MockExecutionAdapter
from services.trading_engine.app.main import TradingEngine
from services.trading_engine.app.models.order import OrderStatus
from services.trading_engine.app.models.risk_decision import DecisionType
from services.trading_engine.app.models.signal import Signal, SignalAction
from services.trading_engine.app.models.system_state import SystemState
from services.trading_engine.app.monitoring.audit import AuditLogger
from services.trading_engine.app.portfolio.state import PortfolioManager


def setup_test_engine():
    settings = TradingEngineSettings(
        max_risk_per_trade_percent=2.0,
        max_daily_loss_percent=5.0,
        max_drawdown_percent=10.0,
        max_consecutive_losses=3,
        max_concurrent_trades=3,
    )
    portfolio = PortfolioManager(initial_balance=100000.0)
    execution = MockExecutionAdapter()
    audit = AuditLogger()
    engine = TradingEngine(
        settings=settings,
        portfolio_manager=portfolio,
        execution_adapter=execution,
        audit=audit,
    )
    return engine, execution, portfolio, audit


def test_approved_order_reaches_mock_execution():
    """Verify approved signal successfully flows to mock execution adapter and creates position."""
    engine, execution, portfolio, audit = setup_test_engine()
    engine.start_bot()  # Bot must be RUNNING

    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.85,
        entry=2650.25,
        stopLoss=2640.25,
        takeProfit=2670.25,
        riskPercent=1.0,
    )

    result = engine.process_signal(signal)

    # Assert pipeline status
    assert result.status == "APPROVED_AND_EXECUTED"
    assert result.riskDecision.decision == DecisionType.APPROVED
    assert result.orderAcknowledgement is not None
    assert result.orderAcknowledgement.status == OrderStatus.FILLED
    assert result.position is not None

    # Assert MockExecutionAdapter state
    assert len(execution.order_history) == 1
    assert len(execution.open_positions) == 1

    # Assert Portfolio synchronized
    assert len(portfolio.get_positions()) == 1
    assert len(audit.events) > 0


def test_rejected_order_never_reaches_execution():
    """Verify rejected proposal terminates before reaching execution adapter."""
    engine, execution, portfolio, audit = setup_test_engine()
    engine.start_bot()

    # Excessive risk (3.5% > 2.0%)
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.85,
        entry=2650.25,
        stopLoss=2640.25,
        riskPercent=3.5,
    )

    result = engine.process_signal(signal)

    assert result.status == "REJECTED"
    assert result.riskDecision.decision == DecisionType.REJECTED
    assert result.orderRequest is None
    assert result.orderAcknowledgement is None
    assert result.position is None

    # Execution adapter MUST be untouched
    assert len(execution.order_history) == 0
    assert len(execution.open_positions) == 0
    assert len(portfolio.get_positions()) == 0
    assert len(audit.events) > 0


def test_halted_order_never_reaches_execution():
    """Verify halted proposal terminates without reaching execution adapter."""
    engine, execution, portfolio, audit = setup_test_engine()
    engine.start_bot()

    # Force daily loss limit breach
    portfolio.daily_pnl = -6000.0  # -6% loss on 100k account

    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.85,
        entry=2650.25,
        stopLoss=2640.25,
        riskPercent=1.0,
    )

    result = engine.process_signal(signal)

    assert result.status == "HALTED"
    assert result.riskDecision.decision == DecisionType.HALTED
    assert "DAILY_LOSS_LIMIT_REACHED" in result.riskDecision.reasonCodes

    # Execution adapter MUST be untouched
    assert len(execution.order_history) == 0
    assert len(execution.open_positions) == 0
    assert len(portfolio.get_positions()) == 0
    assert len(audit.events) > 0


def test_wait_never_reaches_execution():
    """
    CRITICAL TEST:
    WAIT is a valid signal, but must NEVER reach the execution adapter.
    """
    engine, execution, portfolio, audit = setup_test_engine()
    engine.start_bot()

    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.WAIT,
        confidence=0.5,
    )

    result = engine.process_signal(signal)

    assert result.status == "WAIT_ACKNOWLEDGED"
    assert result.riskDecision.decision == DecisionType.REJECTED
    assert "WAIT_SIGNAL" in result.riskDecision.reasonCodes
    assert result.orderRequest is None
    assert result.orderAcknowledgement is None
    assert result.position is None

    # Execution adapter MUST be untouched
    assert len(execution.order_history) == 0
    assert len(execution.open_positions) == 0
    assert len(portfolio.get_positions()) == 0
    assert len(audit.events) > 0


def test_stopped_bot_never_reaches_execution():
    """Verify orders are not sent when bot is STOPPED."""
    engine, execution, _portfolio, audit = setup_test_engine()
    assert engine.system_state == SystemState.STOPPED

    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.85,
        entry=2650.25,
        stopLoss=2640.25,
    )

    result = engine.process_signal(signal)

    assert result.status == "REJECTED"
    assert "SYSTEM_STATE_STOPPED" in result.riskDecision.reasonCodes
    assert len(execution.order_history) == 0
    assert len(audit.events) > 0
