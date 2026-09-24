"""Trading Engine Coordinator implementing the strict execution pipeline."""
from dataclasses import dataclass
from uuid import uuid4

from .configuration.settings import TradingEngineSettings, get_default_settings
from .execution.mock_adapter import MockExecutionAdapter
from .models.audit_event import AuditEventType, AuditSeverity
from .models.market import InstrumentSpec, MarketQuote
from .models.order import OrderAcknowledgement, OrderRequest, OrderSide, OrderStatus
from .models.position import Position
from .models.risk_decision import DecisionType, RiskDecision
from .models.signal import Signal, SignalAction
from .models.system_state import SystemState
from .monitoring.audit import AuditLogger, audit_logger
from .portfolio.state import PortfolioManager
from .risk.engine import RiskEngine
from .signals.validator import SignalValidator


@dataclass
class PipelineResult:
    """Outcome of processing a trading signal through the pipeline."""
    tradeLifecycleId: str
    status: str  # "APPROVED_AND_EXECUTED", "REJECTED", "HALTED", "WAIT_ACKNOWLEDGED", "EXECUTION_FAILED"
    signal: Signal
    riskDecision: RiskDecision
    orderRequest: OrderRequest | None = None
    orderAcknowledgement: OrderAcknowledgement | None = None
    position: Position | None = None
    message: str | None = None


class TradingEngine:
    """
    Core Trading Engine coordinating the linear pipeline:
    Signal -> Validation -> Risk Engine -> (Approved?) -> Mock Execution
    """

    def __init__(
        self,
        settings: TradingEngineSettings | None = None,
        portfolio_manager: PortfolioManager | None = None,
        execution_adapter: MockExecutionAdapter | None = None,
        audit: AuditLogger | None = None,
    ):
        self.settings = settings or get_default_settings()
        self.system_state: SystemState = SystemState.STOPPED
        self.portfolio: PortfolioManager = portfolio_manager or PortfolioManager()
        self.execution: MockExecutionAdapter = execution_adapter or MockExecutionAdapter()
        self.risk_engine: RiskEngine = RiskEngine(settings=self.settings)
        self.audit: AuditLogger = audit or audit_logger

        # Simulated market quotes and instrument specifications
        self.market_quotes: dict[str, MarketQuote] = {
            "XAUUSD": MarketQuote(symbol="XAUUSD", bid=2650.00, ask=2650.25, isMarketOpen=True),
            "EURUSD": MarketQuote(symbol="EURUSD", bid=1.0850, ask=1.0852, isMarketOpen=True),
            "GBPUSD": MarketQuote(symbol="GBPUSD", bid=1.3020, ask=1.3023, isMarketOpen=True),
            "USDJPY": MarketQuote(symbol="USDJPY", bid=148.50, ask=148.52, isMarketOpen=True),
        }
        self.instrument_specs: dict[str, InstrumentSpec] = {
            "XAUUSD": InstrumentSpec(symbol="XAUUSD", contractSize=100.0, minVolume=0.01, maxVolume=50.0, volumeStep=0.01),
            "EURUSD": InstrumentSpec(symbol="EURUSD", contractSize=100000.0, minVolume=0.01, maxVolume=50.0, volumeStep=0.01),
            "GBPUSD": InstrumentSpec(symbol="GBPUSD", contractSize=100000.0, minVolume=0.01, maxVolume=50.0, volumeStep=0.01),
            "USDJPY": InstrumentSpec(symbol="USDJPY", contractSize=100000.0, minVolume=0.01, maxVolume=50.0, volumeStep=0.01),
        }

    # -------------------------------------------------------------
    # Bot State Management
    # -------------------------------------------------------------
    def start_bot(self, actor: str = "operator") -> SystemState:
        """Transition bot to RUNNING only when simulation is healthy."""
        old_state = self.system_state
        self.system_state = SystemState.RUNNING
        self.audit.log(
            event_type=AuditEventType.BOT_STARTED,
            actor=actor,
            severity=AuditSeverity.INFO,
            metadata={"previousState": old_state.value, "newState": self.system_state.value},
        )
        self.audit.log(
            event_type=AuditEventType.SYSTEM_STATE_CHANGE,
            actor=actor,
            severity=AuditSeverity.INFO,
            metadata={"from": old_state.value, "to": self.system_state.value},
        )
        return self.system_state

    def pause_bot(self, actor: str = "operator") -> SystemState:
        """Pause bot (prevents new orders)."""
        old_state = self.system_state
        self.system_state = SystemState.PAUSED
        self.audit.log(
            event_type=AuditEventType.BOT_PAUSED,
            actor=actor,
            severity=AuditSeverity.WARNING,
            metadata={"previousState": old_state.value, "newState": self.system_state.value},
        )
        return self.system_state

    def stop_bot(self, actor: str = "operator") -> SystemState:
        """Stop bot (prevents new orders)."""
        old_state = self.system_state
        self.system_state = SystemState.STOPPED
        self.audit.log(
            event_type=AuditEventType.BOT_STOPPED,
            actor=actor,
            severity=AuditSeverity.INFO,
            metadata={"previousState": old_state.value, "newState": self.system_state.value},
        )
        return self.system_state

    def emergency_stop(self, actor: str = "operator") -> SystemState:
        """Trigger emergency stop (locks execution)."""
        old_state = self.system_state
        self.system_state = SystemState.EMERGENCY_STOP
        self.audit.log(
            event_type=AuditEventType.EMERGENCY_STOP,
            actor=actor,
            severity=AuditSeverity.CRITICAL,
            metadata={"previousState": old_state.value, "newState": self.system_state.value},
        )
        return self.system_state

    # -------------------------------------------------------------
    # Market Data Simulation Controls
    # -------------------------------------------------------------
    def update_quote(self, quote: MarketQuote) -> None:
        """Update simulated market quote."""
        self.market_quotes[quote.symbol] = quote
        # Mark to market open positions
        self.portfolio.mark_to_market({quote.symbol: quote.bid})

    # -------------------------------------------------------------
    # Execution Pipeline
    # -------------------------------------------------------------
    def process_signal(self, signal: Signal, actor: str = "system") -> PipelineResult:
        """
        Execute strict 5-stage pipeline:
        1. SIGNAL CREATED
        2. VALIDATION
        3. RISK EVALUATION
        4. APPROVAL / REJECTION / HALTED GATE
        5. MOCK EXECUTION (only if APPROVED)
        """
        lifecycle_id = str(uuid4())

        # Stage 1: Signal Log
        self.audit.log(
            event_type=AuditEventType.SIGNAL_CREATED,
            actor=actor,
            trade_lifecycle_id=lifecycle_id,
            severity=AuditSeverity.INFO,
            metadata={
                "signalId": signal.signalId,
                "symbol": signal.symbol,
                "action": signal.action.value,
                "confidence": signal.confidence,
                "entry": signal.entry,
                "stopLoss": signal.stopLoss,
                "takeProfit": signal.takeProfit,
                "riskPercent": signal.riskPercent,
            },
        )

        # Stage 2: Signal Validation
        is_valid, validation_errors = SignalValidator.validate_signal(signal)
        if not is_valid:
            rejection_decision = RiskDecision(
                decision=DecisionType.REJECTED,
                reasonCodes=validation_errors,
                tradeLifecycleId=lifecycle_id,
            )
            self.audit.log(
                event_type=AuditEventType.RISK_REJECTION,
                actor=actor,
                trade_lifecycle_id=lifecycle_id,
                severity=AuditSeverity.WARNING,
                metadata={"reasonCodes": validation_errors},
            )
            return PipelineResult(
                tradeLifecycleId=lifecycle_id,
                status="REJECTED",
                signal=signal,
                riskDecision=rejection_decision,
                message="Signal validation failed before risk evaluation.",
            )

        # Stage 3: Risk Evaluation
        account = self.portfolio.get_account_snapshot()
        positions = self.portfolio.get_positions()
        quote = self.market_quotes.get(signal.symbol)
        spec = self.instrument_specs.get(signal.symbol, InstrumentSpec(symbol=signal.symbol))

        risk_decision = self.risk_engine.evaluate(
            signal=signal,
            account=account,
            portfolio_positions=positions,
            market_quote=quote,
            instrument_spec=spec,
            system_state=self.system_state,
            daily_loss_amount=abs(min(0.0, self.portfolio.daily_pnl)),
            consecutive_losses=self.portfolio.consecutive_losses,
            trade_lifecycle_id=lifecycle_id,
        )

        self.audit.log(
            event_type=AuditEventType.RISK_EVALUATION,
            actor=actor,
            trade_lifecycle_id=lifecycle_id,
            severity=AuditSeverity.INFO,
            metadata={
                "decision": risk_decision.decision.value,
                "reasonCodes": risk_decision.reasonCodes,
                "approvedVolume": risk_decision.approvedVolume,
            },
        )

        # Stage 4: Decision Gate — STOP if not APPROVED
        if risk_decision.decision != DecisionType.APPROVED:
            event_type = (
                AuditEventType.RISK_REJECTION
                if risk_decision.decision == DecisionType.REJECTED
                else AuditEventType.ERROR
            )
            severity = (
                AuditSeverity.WARNING
                if risk_decision.decision == DecisionType.REJECTED
                else AuditSeverity.ERROR
            )
            self.audit.log(
                event_type=event_type,
                actor=actor,
                trade_lifecycle_id=lifecycle_id,
                severity=severity,
                metadata={
                    "decision": risk_decision.decision.value,
                    "reasonCodes": risk_decision.reasonCodes,
                },
            )

            status_label = "WAIT_ACKNOWLEDGED" if signal.action == SignalAction.WAIT else risk_decision.decision.value
            return PipelineResult(
                tradeLifecycleId=lifecycle_id,
                status=status_label,
                signal=signal,
                riskDecision=risk_decision,
                message=f"Order proposal stopped at risk engine: {', '.join(risk_decision.reasonCodes)}",
            )

        # Stage 5: Mock Execution (Only for APPROVED orders)
        self.audit.log(
            event_type=AuditEventType.RISK_APPROVAL,
            actor=actor,
            trade_lifecycle_id=lifecycle_id,
            severity=AuditSeverity.INFO,
            metadata={
                "approvedVolume": risk_decision.approvedVolume,
                "riskPercent": risk_decision.riskPercent,
            },
        )

        # Construct OrderRequest from approved signal
        order_side = OrderSide.BUY if signal.action == SignalAction.BUY else OrderSide.SELL
        order_request = OrderRequest(
            signalId=signal.signalId,
            symbol=signal.symbol,
            side=order_side,
            volume=risk_decision.approvedVolume or 0.01,
            entry=signal.entry,
            stopLoss=signal.stopLoss,
            takeProfit=signal.takeProfit,
        )

        self.audit.log(
            event_type=AuditEventType.ORDER_REQUESTED,
            actor=actor,
            trade_lifecycle_id=lifecycle_id,
            severity=AuditSeverity.INFO,
            metadata={
                "orderId": order_request.orderId,
                "side": order_request.side.value,
                "volume": order_request.volume,
                "symbol": order_request.symbol,
            },
        )

        exec_price = (
            (quote.ask if order_side == OrderSide.BUY else quote.bid)
            if quote
            else (signal.entry or 0.0)
        )
        order_ack = self.execution.execute_order(
            order=order_request,
            market_price=exec_price,
            lifecycle_id=lifecycle_id,
        )

        self.audit.log(
            event_type=AuditEventType.ORDER_ACKNOWLEDGED,
            actor=actor,
            trade_lifecycle_id=lifecycle_id,
            severity=AuditSeverity.INFO if order_ack.status == OrderStatus.FILLED else AuditSeverity.ERROR,
            metadata={
                "orderId": order_ack.orderId,
                "status": order_ack.status.value,
                "executionPrice": order_ack.executionPrice,
                "positionId": order_ack.positionId,
            },
        )

        if order_ack.status != OrderStatus.FILLED:
            return PipelineResult(
                tradeLifecycleId=lifecycle_id,
                status="EXECUTION_FAILED",
                signal=signal,
                riskDecision=risk_decision,
                orderRequest=order_request,
                orderAcknowledgement=order_ack,
                message=order_ack.message or "Execution failed",
            )

        # Position successfully opened in mock adapter, sync to portfolio
        opened_pos = self.execution.open_positions.get(order_ack.positionId or "")
        if opened_pos:
            self.portfolio.add_position(opened_pos)
            self.audit.log(
                event_type=AuditEventType.POSITION_OPENED,
                actor=actor,
                trade_lifecycle_id=lifecycle_id,
                severity=AuditSeverity.INFO,
                metadata={
                    "positionId": opened_pos.positionId,
                    "symbol": opened_pos.symbol,
                    "side": opened_pos.side.value,
                    "volume": opened_pos.volume,
                    "entryPrice": opened_pos.entryPrice,
                },
            )

        return PipelineResult(
            tradeLifecycleId=lifecycle_id,
            status="APPROVED_AND_EXECUTED",
            signal=signal,
            riskDecision=risk_decision,
            orderRequest=order_request,
            orderAcknowledgement=order_ack,
            position=opened_pos,
            message="Trade proposal evaluated, approved, and executed in simulation.",
        )


# Global singleton instance of the TradingEngine
engine_instance = TradingEngine()
