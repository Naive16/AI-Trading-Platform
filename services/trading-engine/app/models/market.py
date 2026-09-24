"""Market data and instrument specification models."""
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class InstrumentSpec(BaseModel):
    """Trading instrument contract specifications."""
    symbol: str
    contractSize: float = 100.0  # e.g., 100 oz for XAUUSD, 100,000 for EURUSD
    minVolume: float = 0.01
    maxVolume: float = 100.0
    volumeStep: float = 0.01
    digits: int = 2
    pointSize: float = 0.01
    marginRate: float = 0.01  # 1% margin required (1:100 leverage)


class MarketQuote(BaseModel):
    """Market price quote snapshot."""
    symbol: str
    bid: float
    ask: float
    spread: float | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    isMarketOpen: bool = True

    def model_post_init(self, context: object, /) -> None:
        if self.spread is None:
            self.spread = round(max(0.0, self.ask - self.bid), 5)
