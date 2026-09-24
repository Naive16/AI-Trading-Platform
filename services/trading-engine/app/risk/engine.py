"""Deterministic Risk Engine enforcing all capital protection rules."""
from datetime import datetime, timezone
from uuid import uuid4

from ..configuration.settings import TradingEngineSettings
from ..models.account import Account
from ..models.market import InstrumentSpec, MarketQuote
from ..models.risk_decision import DecisionType, RiskDecision
from ..models.signal import Signal, SignalAction
from ..models.system_state import SystemState
from ..signals.validator import SignalValidator
from .sizing import PositionSizer


class RiskEngine:
    """
    Deterministic Risk Engine.
    Evaluates trading proposals against account equity, portfolio risk, market conditions,
    and system state without AI or heuristic bypasses.
    """

    def __init__(self, settings: TradingEngineSettings | None = None):
        self.settings = settings or TradingEngineSettings()

    def evaluate(
        self,
        signal: Signal,
        account: Account,
        portfolio_positions: list,
        market_quote: MarketQuote | None = None,
        instrument_spec: InstrumentSpec | None = None,
        system_state: SystemState = SystemState.STOPPED,
        daily_loss_amount: float = 0.0,
        daily_loss_percent: float = 0.0,
        consecutive_losses: int = 0,
        trade_lifecycle_id: str | None = None,
    ) -> RiskDecision:
        """
        Evaluate a signal through all 13 deterministic risk checks.
        Returns a structured RiskDecision conforming to shared/schemas/risk-decision.schema.json.
        """
        lifecycle_id = trade_lifecycle_id or str(uuid4())
        reasons: list[str] = []

        # ---------------------------------------------------------
        # Check 13: System State Check (must be RUNNING)
        # ---------------------------------------------------------
        if system_state == SystemState.EMERGENCY_STOP:
            return RiskDecision(
                decision=DecisionType.REJECTED,
                reasonCodes=["SYSTEM_STATE_EMERGENCY_STOP"],
                tradeLifecycleId=lifecycle_id,
            )
        if system_state == SystemState.STOPPED:
            return RiskDecision(
                decision=DecisionType.REJECTED,
                reasonCodes=["SYSTEM_STATE_STOPPED"],
                tradeLifecycleId=lifecycle_id,
            )
        if system_state == SystemState.PAUSED:
            return RiskDecision(
                decision=DecisionType.REJECTED,
                reasonCodes=["SYSTEM_STATE_PAUSED"],
                tradeLifecycleId=lifecycle_id,
            )
        if system_state == SystemState.DISCONNECTED:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["SYSTEM_STATE_DISCONNECTED"],
                tradeLifecycleId=lifecycle_id,
            )
        if system_state == SystemState.ERROR:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["SYSTEM_STATE_ERROR"],
                tradeLifecycleId=lifecycle_id,
            )
        if system_state != SystemState.RUNNING:
            return RiskDecision(
                decision=DecisionType.REJECTED,
                reasonCodes=[f"SYSTEM_STATE_INVALID_{system_state.value}"],
                tradeLifecycleId=lifecycle_id,
            )

        # ---------------------------------------------------------
        # Check 3: Account Data Integrity (HALT if missing/corrupt)
        # ---------------------------------------------------------
        if account is None:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["ACCOUNT_DATA_MISSING"],
                tradeLifecycleId=lifecycle_id,
            )
        if account.equity is None or account.equity <= 0:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["ACCOUNT_EQUITY_INVALID"],
                tradeLifecycleId=lifecycle_id,
            )
        if account.balance is None or account.balance <= 0:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["ACCOUNT_BALANCE_INVALID"],
                tradeLifecycleId=lifecycle_id,
            )
        if account.freeMargin is None or account.freeMargin < 0:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["ACCOUNT_FREE_MARGIN_INVALID"],
                tradeLifecycleId=lifecycle_id,
            )

        # ---------------------------------------------------------
        # Check 9: Daily Loss Limit (HALT if breached)
        # ---------------------------------------------------------
        eff_daily_loss_pct = daily_loss_percent
        if eff_daily_loss_pct <= 0 and daily_loss_amount > 0 and account.equity > 0:
            eff_daily_loss_pct = (daily_loss_amount / account.equity) * 100.0

        if eff_daily_loss_pct >= self.settings.max_daily_loss_percent:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["DAILY_LOSS_LIMIT_REACHED"],
                tradeLifecycleId=lifecycle_id,
            )
        if (
            self.settings.max_daily_loss_amount is not None
            and daily_loss_amount >= self.settings.max_daily_loss_amount
        ):
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["DAILY_LOSS_LIMIT_REACHED"],
                tradeLifecycleId=lifecycle_id,
            )

        # ---------------------------------------------------------
        # Check 10: Maximum Account Drawdown (HALT if breached)
        # ---------------------------------------------------------
        current_drawdown = account.drawdownPercent or 0.0
        if current_drawdown >= self.settings.max_drawdown_percent:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["MAX_DRAWDOWN_REACHED"],
                tradeLifecycleId=lifecycle_id,
            )

        # ---------------------------------------------------------
        # Check 11: Consecutive Losses Limit (HALT if breached)
        # ---------------------------------------------------------
        if consecutive_losses >= self.settings.max_consecutive_losses:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["CONSECUTIVE_LOSS_LIMIT_REACHED"],
                tradeLifecycleId=lifecycle_id,
            )

        # ---------------------------------------------------------
        # Check 12: Market Data Integrity & Freshness (HALT if invalid)
        # ---------------------------------------------------------
        if market_quote is None:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["MARKET_DATA_UNAVAILABLE"],
                tradeLifecycleId=lifecycle_id,
            )
        if not market_quote.isMarketOpen:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["MARKET_CLOSED"],
                tradeLifecycleId=lifecycle_id,
            )

        # Data freshness check
        now = datetime.now(timezone.utc)
        quote_time = market_quote.timestamp
        if quote_time.tzinfo is None:
            quote_time = quote_time.replace(tzinfo=timezone.utc)
        age_seconds = (now - quote_time).total_seconds()
        if age_seconds > self.settings.max_quote_age_seconds:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["MARKET_DATA_STALE"],
                tradeLifecycleId=lifecycle_id,
            )

        # Spread check
        spread = market_quote.spread or (market_quote.ask - market_quote.bid)
        if spread > self.settings.max_spread:
            return RiskDecision(
                decision=DecisionType.HALTED,
                reasonCodes=["SPREAD_TOO_HIGH"],
                tradeLifecycleId=lifecycle_id,
            )

        # ---------------------------------------------------------
        # Check 1: Signal Validity
        # ---------------------------------------------------------
        is_valid, validation_errors = SignalValidator.validate_signal(signal)
        if not is_valid:
            return RiskDecision(
                decision=DecisionType.REJECTED,
                reasonCodes=validation_errors,
                tradeLifecycleId=lifecycle_id,
            )

        # ---------------------------------------------------------
        # Check 2: WAIT Signal (First-class reject: never executable)
        # ---------------------------------------------------------
        if signal.action == SignalAction.WAIT:
            return RiskDecision(
                decision=DecisionType.REJECTED,
                reasonCodes=["WAIT_SIGNAL"],
                tradeLifecycleId=lifecycle_id,
            )

        # ---------------------------------------------------------
        # Check 4: Stop Loss Requirement
        # ---------------------------------------------------------
        if self.settings.require_stop_loss and (signal.stopLoss is None or signal.stopLoss <= 0):
            reasons.append("MISSING_STOP_LOSS")

        entry_price = signal.entry
        if entry_price is None or entry_price <= 0:
            # Fall back to current market price if signal entry is None
            entry_price = market_quote.ask if signal.action == SignalAction.BUY else market_quote.bid

        if signal.stopLoss is not None and entry_price is not None:
            if signal.action == SignalAction.BUY and signal.stopLoss >= entry_price:
                reasons.append("INVALID_STOP_LOSS_BUY_ABOVE_ENTRY")
            elif signal.action == SignalAction.SELL and signal.stopLoss <= entry_price:
                reasons.append("INVALID_STOP_LOSS_SELL_BELOW_ENTRY")

        # ---------------------------------------------------------
        # Check 5: Take Profit Requirement & Risk/Reward
        # ---------------------------------------------------------
        if self.settings.require_take_profit and (signal.takeProfit is None or signal.takeProfit <= 0):
            reasons.append("MISSING_TAKE_PROFIT")

        if signal.takeProfit is not None and signal.stopLoss is not None and entry_price is not None:
            risk_dist = abs(entry_price - signal.stopLoss)
            reward_dist = abs(signal.takeProfit - entry_price)
            if risk_dist > 0:
                rr_ratio = reward_dist / risk_dist
                if rr_ratio < self.settings.min_risk_reward_ratio:
                    reasons.append("RISK_REWARD_RATIO_BELOW_MINIMUM")

        # ---------------------------------------------------------
        # Check 7: Maximum Risk Per Trade
        # ---------------------------------------------------------
        risk_pct = signal.riskPercent if signal.riskPercent is not None else 1.0
        if risk_pct > self.settings.max_risk_per_trade_percent:
            reasons.append("RISK_LIMIT_EXCEEDED")

        # ---------------------------------------------------------
        # Check 8: Portfolio Exposure & Concurrent Trades
        # ---------------------------------------------------------
        if len(portfolio_positions) >= self.settings.max_concurrent_trades:
            reasons.append("CONCURRENT_TRADES_LIMIT_REACHED")

        # Symbol exposure calculation
        symbol_positions = [p for p in portfolio_positions if getattr(p, "symbol", "") == signal.symbol]
        current_symbol_volume = sum(getattr(p, "volume", 0.0) for p in symbol_positions)
        total_portfolio_volume = sum(getattr(p, "volume", 0.0) for p in portfolio_positions)

        # ---------------------------------------------------------
        # Check 6: Position Sizing Derivation
        # ---------------------------------------------------------
        spec = instrument_spec or InstrumentSpec(symbol=signal.symbol)
        stop_loss_val = signal.stopLoss if signal.stopLoss is not None else (entry_price * 0.99)
        volume, _actual_risk = PositionSizer.calculate_volume(
            equity=account.equity,
            risk_percent=risk_pct,
            entry=entry_price,
            stop_loss=stop_loss_val,
            instrument=spec,
        )

        if volume <= 0:
            reasons.append("CALCULATED_VOLUME_BELOW_MINIMUM")

        if current_symbol_volume + volume > self.settings.max_symbol_exposure_volume:
            reasons.append("SYMBOL_EXPOSURE_LIMIT_EXCEEDED")

        if total_portfolio_volume + volume > self.settings.max_portfolio_exposure_volume:
            reasons.append("PORTFOLIO_EXPOSURE_LIMIT_EXCEEDED")

        # Margin requirement check
        required_margin = volume * spec.contractSize * entry_price * spec.marginRate
        if required_margin > account.freeMargin:
            reasons.append("INSUFFICIENT_MARGIN")

        # ---------------------------------------------------------
        # Final Decision
        # ---------------------------------------------------------
        if reasons:
            return RiskDecision(
                decision=DecisionType.REJECTED,
                reasonCodes=reasons,
                riskPercent=risk_pct,
                approvedVolume=None,
                tradeLifecycleId=lifecycle_id,
            )

        return RiskDecision(
            decision=DecisionType.APPROVED,
            reasonCodes=["RISK_CHECKS_PASSED"],
            riskPercent=risk_pct,
            approvedVolume=volume,
            tradeLifecycleId=lifecycle_id,
        )
