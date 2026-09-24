"""API routes package."""
from .bot import router as bot_router
from .health import router as health_router
from .orders import router as orders_router
from .positions import router as positions_router
from .risk import router as risk_router
from .signals import router as signals_router
from .system import router as system_router

__all__ = [
    "bot_router",
    "health_router",
    "orders_router",
    "positions_router",
    "risk_router",
    "signals_router",
    "system_router",
]
