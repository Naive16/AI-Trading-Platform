"""Position model strictly matching shared/schemas/position.schema.json."""
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class PositionSide(str, Enum):
    """Position side."""
    BUY = "BUY"
    SELL = "SELL"


class Position(BaseModel):
    """Position conforming to shared/schemas/position.schema.json."""
    positionId: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str = Field(..., min_length=1)
    side: PositionSide
    volume: float = Field(..., gt=0.0)
    entryPrice: float | None = None
    currentPrice: float | None = None
    stopLoss: float | None = None
    takeProfit: float | None = None
    unrealizedPnl: float | None = 0.0
    lifecycleId: str | None = None
