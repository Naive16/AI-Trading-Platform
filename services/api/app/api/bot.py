"""Bot control and emergency stop endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from services.trading_engine.app.main import engine_instance
from services.trading_engine.app.models.system_state import SystemState

from ..dependencies import reject_broker_credentials, verify_dev_authorization

router = APIRouter(tags=["Bot"])


class BotStatusResponse(BaseModel):
    """Bot status representation."""
    state: SystemState
    executionAllowed: bool
    environment: str
    liveTrading: bool
    openPositionsCount: int
    dailyPnL: float
    consecutiveLosses: int


class BotActionResponse(BaseModel):
    """Response after state change request."""
    previousState: SystemState
    currentState: SystemState
    message: str


@router.get(
    "/api/v1/bot/status",
    response_model=BotStatusResponse,
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def get_bot_status() -> BotStatusResponse:
    """Get current bot execution state and portfolio metrics."""
    return BotStatusResponse(
        state=engine_instance.system_state,
        executionAllowed=engine_instance.system_state.is_execution_allowed,
        environment=engine_instance.settings.environment,
        liveTrading=engine_instance.settings.live_trading,
        openPositionsCount=len(engine_instance.portfolio.get_positions()),
        dailyPnL=round(engine_instance.portfolio.daily_pnl, 2),
        consecutiveLosses=engine_instance.portfolio.consecutive_losses,
    )


@router.post(
    "/api/v1/bot/start",
    response_model=BotActionResponse,
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def start_bot() -> BotActionResponse:
    """Transition bot to RUNNING state."""
    prev = engine_instance.system_state
    curr = engine_instance.start_bot(actor="api-operator")
    return BotActionResponse(
        previousState=prev,
        currentState=curr,
        message="Bot transitioned to RUNNING state. Order proposals may now be approved by the risk engine.",
    )


@router.post(
    "/api/v1/bot/pause",
    response_model=BotActionResponse,
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def pause_bot() -> BotActionResponse:
    """Transition bot to PAUSED state (no new orders permitted)."""
    prev = engine_instance.system_state
    curr = engine_instance.pause_bot(actor="api-operator")
    return BotActionResponse(
        previousState=prev,
        currentState=curr,
        message="Bot paused. No new orders may be executed.",
    )


@router.post(
    "/api/v1/bot/stop",
    response_model=BotActionResponse,
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def stop_bot() -> BotActionResponse:
    """Transition bot to STOPPED state (no new orders permitted)."""
    prev = engine_instance.system_state
    curr = engine_instance.stop_bot(actor="api-operator")
    return BotActionResponse(
        previousState=prev,
        currentState=curr,
        message="Bot stopped. Order execution disabled.",
    )


@router.post(
    "/api/v1/emergency/stop",
    response_model=BotActionResponse,
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def emergency_stop() -> BotActionResponse:
    """Trigger EMERGENCY_STOP locking all order proposals immediately."""
    prev = engine_instance.system_state
    curr = engine_instance.emergency_stop(actor="api-operator")
    return BotActionResponse(
        previousState=prev,
        currentState=curr,
        message="EMERGENCY_STOP engaged. All order proposals will be strictly rejected.",
    )
