"""In-memory portfolio and account state management."""
from datetime import datetime, timezone

from ..models.account import Account
from ..models.position import Position, PositionSide


class PortfolioManager:
    """Manages in-memory account, positions, daily PnL, and exposure metrics."""

    def __init__(
        self,
        account_id: str = "SIM-ACC-001",
        initial_balance: float = 100000.0,
        currency: str = "USD",
    ):
        self.account_id = account_id
        self.currency = currency
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.peak_equity = initial_balance
        self.daily_pnl = 0.0
        self.consecutive_losses = 0

        self.positions: dict[str, Position] = {}
        self.closed_trades: list[dict] = []

    def get_account_snapshot(self) -> Account:
        """Calculate and return current Account snapshot."""
        margin_used = sum(
            pos.volume * 1000.0 for pos in self.positions.values()
        )  # standard margin estimate
        free_margin = max(0.0, self.equity - margin_used)

        drawdown = 0.0
        if self.peak_equity > 0:
            drawdown = max(0.0, ((self.peak_equity - self.equity) / self.peak_equity) * 100.0)

        return Account(
            accountId=self.account_id,
            currency=self.currency,
            balance=round(self.balance, 2),
            equity=round(self.equity, 2),
            margin=round(margin_used, 2),
            freeMargin=round(free_margin, 2),
            drawdownPercent=round(drawdown, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def add_position(self, position: Position) -> None:
        """Add newly opened position to portfolio."""
        self.positions[position.positionId] = position
        self._update_equity()

    def remove_position(self, position_id: str, close_price: float) -> Position | None:
        """Close position and update balance, daily PnL, and loss streak."""
        if position_id not in self.positions:
            return None

        pos = self.positions.pop(position_id)
        entry_price = pos.entryPrice or close_price
        pnl_multiplier = 100.0  # contract multiplier
        if pos.side == PositionSide.BUY:
            pnl = (close_price - entry_price) * pos.volume * pnl_multiplier
        else:
            pnl = (entry_price - close_price) * pos.volume * pnl_multiplier

        self.balance += pnl
        self.daily_pnl += pnl

        if pnl < 0:
            self.consecutive_losses += 1
        elif pnl > 0:
            self.consecutive_losses = 0

        self._update_equity()

        self.closed_trades.append({
            "positionId": position_id,
            "symbol": pos.symbol,
            "side": pos.side.value,
            "volume": pos.volume,
            "entryPrice": entry_price,
            "closePrice": close_price,
            "pnl": round(pnl, 2),
            "closedAt": datetime.now(timezone.utc).isoformat(),
        })
        return pos

    def mark_to_market(self, quotes: dict[str, float]) -> None:
        """Update unrealized PnL of positions with current quotes."""
        total_unrealized = 0.0
        for pos in self.positions.values():
            curr_price = quotes.get(pos.symbol)
            if curr_price is not None:
                pos.currentPrice = curr_price
                entry = pos.entryPrice or curr_price
                if pos.side == PositionSide.BUY:
                    pos.unrealizedPnl = round((curr_price - entry) * pos.volume * 100.0, 2)
                else:
                    pos.unrealizedPnl = round((entry - curr_price) * pos.volume * 100.0, 2)
                total_unrealized += pos.unrealizedPnl or 0.0

        self.equity = self.balance + total_unrealized
        self.peak_equity = max(self.peak_equity, self.equity)

    def _update_equity(self) -> None:
        """Recalculate equity from balance + unrealized PnL."""
        total_unrealized = sum(pos.unrealizedPnl or 0.0 for pos in self.positions.values())
        self.equity = self.balance + total_unrealized
        self.peak_equity = max(self.peak_equity, self.equity)

    def get_positions(self) -> list[Position]:
        """Return list of open positions."""
        return list(self.positions.values())

    def get_exposure(self) -> dict[str, float]:
        """Return volume exposure by symbol and total portfolio volume."""
        symbol_exp: dict[str, float] = {}
        total = 0.0
        for pos in self.positions.values():
            symbol_exp[pos.symbol] = symbol_exp.get(pos.symbol, 0.0) + pos.volume
            total += pos.volume
        symbol_exp["_TOTAL_"] = total
        return symbol_exp

    def reset(self) -> None:
        """Reset portfolio to initial state."""
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self.peak_equity = self.initial_balance
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.positions.clear()
        self.closed_trades.clear()
