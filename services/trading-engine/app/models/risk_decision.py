"""Risk decision model strictly matching shared/schemas/risk-decision.schema.json."""
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    """Allowed risk decisions."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    HALTED = "HALTED"


class RiskDecision(BaseModel):
    """Risk decision conforming to shared/schemas/risk-decision.schema.json."""
    decision: DecisionType
    reasonCodes: list[str] = Field(default_factory=list)
    riskPercent: float | None = Field(default=None, ge=0.0)
    approvedVolume: float | None = Field(default=None, ge=0.0)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tradeLifecycleId: str | None = None
