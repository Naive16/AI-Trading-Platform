"""Signals endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from services.trading_engine.app.main import engine_instance
from services.trading_engine.app.models.risk_decision import RiskDecision
from services.trading_engine.app.models.signal import Signal
from services.trading_engine.app.signals.validator import SignalValidator

from ..dependencies import reject_broker_credentials, verify_dev_authorization

router = APIRouter(prefix="/api/v1/signals", tags=["Signals"])


class SignalEvaluationResponse(BaseModel):
    """Signal validation and risk evaluation response."""
    signalId: str
    isValid: bool
    validationErrors: list[str]
    riskDecision: RiskDecision


@router.post(
    "/evaluate",
    response_model=SignalEvaluationResponse,
    dependencies=[Depends(reject_broker_credentials), Depends(verify_dev_authorization)],
)
async def evaluate_signal(signal: Signal) -> SignalEvaluationResponse:
    """Validate signal and evaluate risk without executing."""
    is_valid, errors = SignalValidator.validate_signal(signal)

    account = engine_instance.portfolio.get_account_snapshot()
    positions = engine_instance.portfolio.get_positions()
    quote = engine_instance.market_quotes.get(signal.symbol)
    spec = engine_instance.instrument_specs.get(signal.symbol)

    risk_decision = engine_instance.risk_engine.evaluate(
        signal=signal,
        account=account,
        portfolio_positions=positions,
        market_quote=quote,
        instrument_spec=spec,
        system_state=engine_instance.system_state,
        daily_loss_amount=abs(min(0.0, engine_instance.portfolio.daily_pnl)),
        consecutive_losses=engine_instance.portfolio.consecutive_losses,
    )

    return SignalEvaluationResponse(
        signalId=signal.signalId,
        isValid=is_valid,
        validationErrors=errors,
        riskDecision=risk_decision,
    )
