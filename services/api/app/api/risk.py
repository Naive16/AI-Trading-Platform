"""Risk evaluation endpoint."""
from fastapi import APIRouter, Depends

from services.trading_engine.app.main import engine_instance
from services.trading_engine.app.models.risk_decision import RiskDecision
from services.trading_engine.app.models.signal import Signal

from ..dependencies import reject_broker_credentials, verify_dev_authorization

router = APIRouter(prefix="/api/v1/risk", tags=["Risk"])


@router.post(
    "/evaluate",
    response_model=RiskDecision,
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def evaluate_risk(signal: Signal) -> RiskDecision:
    """
    Direct deterministic risk engine evaluation of a trade proposal.
    Returns structured decision (APPROVED, REJECTED, HALTED) conforming to
    shared/schemas/risk-decision.schema.json.
    """
    account = engine_instance.portfolio.get_account_snapshot()
    positions = engine_instance.portfolio.get_positions()
    quote = engine_instance.market_quotes.get(signal.symbol)
    spec = engine_instance.instrument_specs.get(signal.symbol)

    return engine_instance.risk_engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=positions,
        market_quote=quote,
        instrument_spec=spec,
        system_state=engine_instance.system_state,
        daily_loss_amount=abs(min(0.0, engine_instance.portfolio.daily_pnl)),
        consecutive_losses=engine_instance.portfolio.consecutive_losses,
    )
