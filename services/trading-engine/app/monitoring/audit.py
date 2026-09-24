"""Structured audit logger with sanitization."""
import logging
from typing import Any

from ..models.audit_event import AuditEvent, AuditEventType, AuditSeverity

logger = logging.getLogger("trading.audit")

FORBIDDEN_SECRET_KEYS = {
    "password", "secret", "token", "brokerpassword", "brokerlogin",
    "apikey", "key", "authorization", "privatekey", "investorpassword"
}


class AuditLogger:
    """Thread-safe in-memory audit log store with sanitization."""

    def __init__(self, max_events: int = 5000):
        self.max_events = max_events
        self.events: list[AuditEvent] = []

    def _sanitize_metadata(self, meta: dict[str, Any]) -> dict[str, Any]:
        """Strip any accidental credential fields before storing."""
        sanitized: dict[str, Any] = {}
        for k, v in meta.items():
            if any(forbidden in k.lower() for forbidden in FORBIDDEN_SECRET_KEYS):
                sanitized[k] = "[REDACTED_SECRET]"
            elif isinstance(v, dict):
                sanitized[k] = self._sanitize_metadata(v)
            else:
                sanitized[k] = v
        return sanitized

    def log(
        self,
        event_type: AuditEventType,
        actor: str = "system",
        trade_lifecycle_id: str | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Create, sanitize, and record an audit event."""
        sanitized_meta = self._sanitize_metadata(metadata or {})
        event = AuditEvent(
            eventType=event_type,
            actor=actor,
            tradeLifecycleId=trade_lifecycle_id,
            severity=severity,
            metadata=sanitized_meta,
        )
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)

        # Output to structured standard log
        log_msg = f"[{event.eventType.value}] actor={event.actor} lifecycle={event.tradeLifecycleId} - {event.metadata}"
        if severity == AuditSeverity.CRITICAL or severity == AuditSeverity.ERROR:
            logger.error(log_msg)
        elif severity == AuditSeverity.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        return event

    def get_events(self, limit: int = 100, event_type: AuditEventType | None = None) -> list[AuditEvent]:
        """Retrieve recent audit events."""
        filtered = self.events
        if event_type:
            filtered = [e for e in filtered if e.eventType == event_type]
        return filtered[-limit:]

    def clear(self) -> None:
        """Clear audit history (e.g. for tests)."""
        self.events.clear()


# Global audit logger instance
audit_logger = AuditLogger()
