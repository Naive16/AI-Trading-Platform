"""Account model strictly matching shared/schemas/account.schema.json."""
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Account(BaseModel):
    """Trading account snapshot conforming to shared/schemas/account.schema.json."""
    accountId: str
    currency: str = "USD"
    balance: float
    equity: float
    margin: float | None = 0.0
    freeMargin: float | None = None
    drawdownPercent: float | None = 0.0
    timestamp: str | None = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def model_post_init(self, context: object, /) -> None:
        if self.freeMargin is None:
            margin_used = self.margin or 0.0
            self.freeMargin = max(0.0, self.equity - margin_used)
