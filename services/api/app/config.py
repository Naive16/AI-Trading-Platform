"""API service configuration with non-negotiable safe defaults."""
import os

from pydantic import BaseModel


class APISettings(BaseModel):
    """API configuration settings."""
    app_name: str = "AI Trading Platform API"
    environment: str = os.getenv("ENVIRONMENT", "simulation")
    live_trading: bool = False
    mt5_connected: bool = False
    broker_connected: bool = False
    default_system_state: str = "STOPPED"

    # Development authentication key (marked clearly as non-production)
    # DEVELOPMENT ONLY - NOT PRODUCTION READY
    dev_api_key: str = os.getenv("API_KEY", "dev-trading-secret-key")
    auth_header_name: str = "X-API-Key"


api_settings = APISettings()
