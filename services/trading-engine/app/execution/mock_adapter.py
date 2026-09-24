"""Mock simulation execution adapter (strictly local, in-memory, no external network)."""
from datetime import datetime, timezone
from uuid import uuid4

from ..models.order import OrderAcknowledgement, OrderRequest, OrderSide, OrderStatus
from ..models.position import Position, PositionSide
from .adapter import ExecutionAdapter


class MockExecutionAdapter(ExecutionAdapter):
    """
    Simulated in-memory execution adapter.
    Never connects to MT5, broker, or external networks.
    """

    def __init__(self, simulate_slippage: float = 0.0):
        self.simulate_slippage = simulate_slippage
        self.open_positions: dict[str, Position] = {}
        self.order_history: list[OrderAcknowledgement] = []
        self.force_failure: bool = False
        self.failure_reason: str = "SIMULATED_EXECUTION_FAILURE"

    def set_force_failure(self, fail: bool, reason: str = "SIMULATED_EXECUTION_FAILURE") -> None:
        """Enable or disable simulated order execution failure."""
        self.force_failure = fail
        self.failure_reason = reason

    def execute_order(
        self,
        order: OrderRequest,
        market_price: float,
        lifecycle_id: str | None = None,
    ) -> OrderAcknowledgement:
        """Simulate order execution and return acknowledgement."""
        if self.force_failure:
            ack = OrderAcknowledgement(
                orderId=order.orderId,
                signalId=order.signalId,
                status=OrderStatus.REJECTED,
                symbol=order.symbol,
                side=order.side,
                volume=order.volume,
                executionPrice=0.0,
                message=self.failure_reason,
            )
            self.order_history.append(ack)
            return ack

        # Simulate execution price with optional slippage
        exec_price = order.entry if order.entry is not None else market_price
        if order.side == OrderSide.BUY:
            exec_price += self.simulate_slippage
        else:
            exec_price -= self.simulate_slippage

        exec_price = round(exec_price, 5)
        position_id = str(uuid4())

        position = Position(
            positionId=position_id,
            symbol=order.symbol,
            side=PositionSide(order.side.value),
            volume=order.volume,
            entryPrice=exec_price,
            currentPrice=exec_price,
            stopLoss=order.stopLoss,
            takeProfit=order.takeProfit,
            unrealizedPnl=0.0,
            lifecycleId=lifecycle_id,
        )
        self.open_positions[position_id] = position

        ack = OrderAcknowledgement(
            orderId=order.orderId,
            signalId=order.signalId,
            status=OrderStatus.FILLED,
            symbol=order.symbol,
            side=order.side,
            volume=order.volume,
            executionPrice=exec_price,
            filledAt=datetime.now(timezone.utc).isoformat(),
            positionId=position_id,
            message="ORDER_SIMULATED_SUCCESSFULLY",
        )
        self.order_history.append(ack)
        return ack

    def close_position(
        self,
        position_id: str,
        close_price: float,
    ) -> Position | None:
        """Close an existing simulated position."""
        if position_id not in self.open_positions:
            return None

        pos = self.open_positions.pop(position_id)
        entry_price = pos.entryPrice or close_price
        # Simple pnl = (close - entry) * volume * contractSize (standardized)
        pnl = (close_price - entry_price) if pos.side == PositionSide.BUY else (entry_price - close_price)
        pos.currentPrice = close_price
        pos.unrealizedPnl = round(pnl * pos.volume * 100.0, 2)
        return pos

    def get_positions(self) -> list[Position]:
        """Return all open positions."""
        return list(self.open_positions.values())

    def clear(self) -> None:
        """Reset mock adapter state."""
        self.open_positions.clear()
        self.order_history.clear()
        self.force_failure = False
