"""Order models strictly matching shared/schemas/order.schema.json."""
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class OrderSide(str, Enum):
    """Permitted order sides."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Simulation order status."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class OrderRequest(BaseModel):
    """Order request conforming to shared/schemas/order.schema.json."""
    orderId: str = Field(default_factory=lambda: str(uuid4()))
    signalId: str
    symbol: str = Field(..., min_length=1)
    side: OrderSide
    volume: float = Field(..., gt=0.0)
    entry: float | None = None
    stopLoss: float | None = None
    takeProfit: float | None = None
    timestamp: str | None = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OrderAcknowledgement(BaseModel):
    """Order acknowledgement from execution adapter."""
    orderId: str
    signalId: str
    status: OrderStatus
    symbol: str
    side: OrderSide
    volume: float
    executionPrice: float
    filledAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    positionId: str | None = None
    message: str | None = None
