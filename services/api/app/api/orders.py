"""Order simulation endpoint executing the strict pipeline."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from services.trading_engine.app.main import engine_instance
from services.trading_engine.app.models.order import OrderAcknowledgement, OrderRequest
from services.trading_engine.app.models.position import Position
from services.trading_engine.app.models.risk_decision import RiskDecision
from services.trading_engine.app.models.signal import Signal

from ..dependencies import reject_broker_credentials, verify_dev_authorization

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


class OrderSimulationResponse(BaseModel):
    """Pipeline execution outcome."""
    tradeLifecycleId: str
    status: str
    signal: Signal
    riskDecision: RiskDecision
    orderRequest: OrderRequest | None = None
    orderAcknowledgement: OrderAcknowledgement | None = None
    position: Position | None = None
    message: str | None = None


@router.post(
    "/simulate",
    response_model=OrderSimulationResponse,
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def simulate_order(signal: Signal) -> OrderSimulationResponse:
    """
    Simulate an order proposal through the strict pipeline:
    SIGNAL -> VALIDATION -> RISK ENGINE -> GATE -> MOCK EXECUTION.
    If REJECTED, HALTED, or WAIT: never reaches mock execution.
    """
    result = engine_instance.process_signal(signal, actor="api-client")

    return OrderSimulationResponse(
        tradeLifecycleId=result.tradeLifecycleId,
        status=result.status,
        signal=result.signal,
        riskDecision=result.riskDecision,
        orderRequest=result.orderRequest,
        orderAcknowledgement=result.orderAcknowledgement,
        position=result.position,
        message=result.message,
    )
