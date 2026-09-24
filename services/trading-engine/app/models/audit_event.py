"""Structured audit event model."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Permitted audit event types."""
    SIGNAL_CREATED = "signal_created"
    RISK_EVALUATION = "risk_evaluation"
    RISK_APPROVAL = "risk_approval"
    RISK_REJECTION = "risk_rejection"
    ORDER_REQUESTED = "order_requested"
    ORDER_ACKNOWLEDGED = "order_acknowledged"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    BOT_STARTED = "bot_started"
    BOT_PAUSED = "bot_paused"
    BOT_STOPPED = "bot_stopped"
    EMERGENCY_STOP = "emergency_stop"
    SYSTEM_STATE_CHANGE = "system_state_change"
    ERROR = "error"


class AuditSeverity(str, Enum):
    """Audit severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditEvent(BaseModel):
    """Structured audit event for full lifecycle observability."""
    eventId: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    eventType: AuditEventType
    actor: str = "system"
    tradeLifecycleId: str | None = None
    severity: AuditSeverity = AuditSeverity.INFO
    metadata: dict[str, Any] = Field(default_factory=dict)
