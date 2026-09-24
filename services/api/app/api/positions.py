"""Positions endpoint."""

from fastapi import APIRouter, Depends

from services.trading_engine.app.main import engine_instance
from services.trading_engine.app.models.position import Position

from ..dependencies import reject_broker_credentials, verify_dev_authorization

router = APIRouter(prefix="/api/v1/positions", tags=["Positions"])


@router.get(
    "",
    response_model=list[Position],
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def get_open_positions() -> list[Position]:
    """Retrieve list of open positions in the simulation portfolio."""
    return engine_instance.portfolio.get_positions()
