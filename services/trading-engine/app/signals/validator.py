"""Signal validation against schema rules and domain constraints."""
from datetime import datetime

from ..models.signal import Signal, SignalAction


class SignalValidator:
    """Validates signal structure, prices, stop loss geometry, and values."""

    @staticmethod
    def validate_signal(signal: Signal) -> tuple[bool, list[str]]:
        """Validate signal. Returns (is_valid, error_messages)."""
        errors: list[str] = []

        if not signal.symbol or not signal.symbol.strip():
            errors.append("MALFORMED_SIGNAL_EMPTY_SYMBOL")

        if not signal.timeframe or not signal.timeframe.strip():
            errors.append("MALFORMED_SIGNAL_EMPTY_TIMEFRAME")

        if signal.action not in (SignalAction.BUY, SignalAction.SELL, SignalAction.WAIT):
            errors.append(f"UNSUPPORTED_ACTION_{signal.action}")

        if not (0.0 <= signal.confidence <= 1.0):
            errors.append(f"INVALID_CONFIDENCE_{signal.confidence}")

        if signal.riskPercent is not None and signal.riskPercent <= 0:
            errors.append("INVALID_RISK_PERCENT_NON_POSITIVE")

        # Timestamp validation
        try:
            # Check ISO format
            datetime.fromisoformat(signal.timestamp.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            errors.append("INVALID_TIMESTAMP_FORMAT")

        # Trading direction constraints for BUY / SELL
        if signal.action in (SignalAction.BUY, SignalAction.SELL):
            if signal.entry is not None and signal.entry <= 0:
                errors.append("INVALID_ENTRY_PRICE")

            if signal.stopLoss is not None and signal.stopLoss <= 0:
                errors.append("INVALID_STOP_LOSS_PRICE")

            # Validate stopLoss relative to entry
            if signal.entry is not None and signal.stopLoss is not None:
                if signal.action == SignalAction.BUY and signal.stopLoss >= signal.entry:
                    errors.append("INVALID_BUY_STOP_LOSS_MUST_BE_BELOW_ENTRY")
                elif signal.action == SignalAction.SELL and signal.stopLoss <= signal.entry:
                    errors.append("INVALID_SELL_STOP_LOSS_MUST_BE_ABOVE_ENTRY")

            # Validate takeProfit relative to entry
            if signal.entry is not None and signal.takeProfit is not None:
                if signal.takeProfit <= 0:
                    errors.append("INVALID_TAKE_PROFIT_PRICE")
                elif signal.action == SignalAction.BUY and signal.takeProfit <= signal.entry:
                    errors.append("INVALID_BUY_TAKE_PROFIT_MUST_BE_ABOVE_ENTRY")
                elif signal.action == SignalAction.SELL and signal.takeProfit >= signal.entry:
                    errors.append("INVALID_SELL_TAKE_PROFIT_MUST_BE_BELOW_ENTRY")

        return (len(errors) == 0, errors)
