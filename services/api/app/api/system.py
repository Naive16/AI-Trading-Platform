"""System status endpoint."""
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from services.trading_engine.app.main import engine_instance
from services.trading_engine.app.models.system_state import SystemState

from ..dependencies import reject_broker_credentials, verify_dev_authorization

router = APIRouter(prefix="/api/v1/system", tags=["System"])


class SystemStatusResponse(BaseModel):
    """System status model."""
    state: SystemState
    environment: str
    liveTrading: bool
    mt5Connected: bool
    brokerConnected: bool
    executionAllowed: bool
    limits: dict[str, Any]
    account: dict[str, Any]


@router.get(
    "/status",
    response_model=SystemStatusResponse,
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def get_system_status() -> SystemStatusResponse:
    """Return comprehensive system health and risk limits status."""
    acc = engine_instance.portfolio.get_account_snapshot()
    settings = engine_instance.settings

    return SystemStatusResponse(
        state=engine_instance.system_state,
        environment=settings.environment,
        liveTrading=settings.live_trading,
        mt5Connected=settings.mt5_connected,
        brokerConnected=settings.broker_connected,
        executionAllowed=engine_instance.system_state.is_execution_allowed,
        limits={
            "maxRiskPerTradePercent": settings.max_risk_per_trade_percent,
            "maxDailyLossPercent": settings.max_daily_loss_percent,
            "maxDrawdownPercent": settings.max_drawdown_percent,
            "maxConsecutiveLosses": settings.max_consecutive_losses,
            "maxConcurrentTrades": settings.max_concurrent_trades,
            "maxSymbolExposureVolume": settings.max_symbol_exposure_volume,
            "maxPortfolioExposureVolume": settings.max_portfolio_exposure_volume,
            "maxSpread": settings.max_spread,
            "maxQuoteAgeSeconds": settings.max_quote_age_seconds,
        },
        account={
            "accountId": acc.accountId,
            "currency": acc.currency,
            "balance": acc.balance,
            "equity": acc.equity,
            "margin": acc.margin,
            "freeMargin": acc.freeMargin,
            "drawdownPercent": acc.drawdownPercent,
        },
    )
