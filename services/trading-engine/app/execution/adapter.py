"""Execution adapter interface."""
from abc import ABC, abstractmethod

from ..models.order import OrderAcknowledgement, OrderRequest
from ..models.position import Position


class ExecutionAdapter(ABC):
    """Abstract execution adapter interface."""

    @abstractmethod
    def execute_order(
        self,
        order: OrderRequest,
        market_price: float,
        lifecycle_id: str | None = None,
    ) -> OrderAcknowledgement:
        """Submit order to execution venue."""

    @abstractmethod
    def close_position(
        self,
        position_id: str,
        close_price: float,
    ) -> Position | None:
        """Close an existing position."""
