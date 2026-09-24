"""Signal models strictly matching shared/schemas/signal.schema.json."""
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SignalAction(str, Enum):
    """Permitted signal actions."""
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


class Signal(BaseModel):
    """Trading signal model conforming to shared/schemas/signal.schema.json."""
    model_config = ConfigDict(populate_by_name=True)

    signalId: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str = Field(..., min_length=1)
    timeframe: str = Field(..., min_length=1)
    action: SignalAction
    confidence: float = Field(..., ge=0.0, le=1.0)
    entry: float | None = None
    stopLoss: float | None = None
    takeProfit: float | None = None
    riskPercent: float | None = Field(default=None, ge=0.0)
    strategy: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Symbol must not be empty")
        return cleaned

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Timeframe must not be empty")
        return cleaned
