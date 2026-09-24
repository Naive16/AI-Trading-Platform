"""Configuration and risk control settings."""
import os

from pydantic import BaseModel, Field


class TradingEngineSettings(BaseModel):
    """Trading engine configuration with safe defaults."""
    # Environment and safety defaults
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "simulation"))
    live_trading: bool = False
    mt5_connected: bool = False
    broker_connected: bool = False
    default_system_state: str = "STOPPED"

    # Risk parameters
    max_risk_per_trade_percent: float = 2.0  # max 2% per trade
    max_daily_loss_percent: float = 5.0      # max 5% daily loss
    max_daily_loss_amount: float | None = None
    max_drawdown_percent: float = 10.0       # max 10% drawdown
    max_consecutive_losses: int = 3          # halt after 3 consecutive losses
    max_concurrent_trades: int = 3           # max 3 open positions
    max_symbol_exposure_volume: float = 5.0  # max 5 lots per symbol
    max_portfolio_exposure_volume: float = 10.0 # max 10 lots across portfolio

    # Market data checks
    max_spread: float = 5.0                  # max allowable spread in price units
    max_quote_age_seconds: float = 30.0      # stale quote threshold
    max_slippage: float = 2.0

    # Trade requirements
    require_stop_loss: bool = True
    require_take_profit: bool = False
    min_risk_reward_ratio: float = 1.0


def get_default_settings() -> TradingEngineSettings:
    """Return default trading engine settings instance."""
    return TradingEngineSettings()
