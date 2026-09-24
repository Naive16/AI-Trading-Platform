"""Health endpoint."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response strictly reporting safety defaults."""
    status: str = "healthy"
    environment: str = "simulation"
    liveTrading: bool = False
    mt5Connected: bool = False
    brokerConnected: bool = False


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """
    Public health status reporting safety boundaries:
    - environment = simulation
    - liveTrading = false
    - mt5Connected = false
    - brokerConnected = false
    """
    return HealthResponse(
        status="healthy",
        environment="simulation",
        liveTrading=False,
        mt5Connected=False,
        brokerConnected=False,
    )
