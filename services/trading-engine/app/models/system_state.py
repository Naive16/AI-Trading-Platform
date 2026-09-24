"""System state definitions."""
from enum import Enum


class SystemState(str, Enum):
    """Permitted system states."""
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    DISCONNECTED = "DISCONNECTED"

    @property
    def is_execution_allowed(self) -> bool:
        """Only RUNNING state allows order execution."""
        return self == SystemState.RUNNING
