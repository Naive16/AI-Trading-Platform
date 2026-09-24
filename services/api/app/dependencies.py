"""API dependencies: Security boundary, Correlation ID, and Broker Credential guard."""
from uuid import uuid4

from fastapi import Header, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from .config import api_settings

# DEVELOPMENT ONLY - NOT PRODUCTION READY
# A lightweight header-based verification for development and local testing.
api_key_header = APIKeyHeader(name=api_settings.auth_header_name, auto_error=False)

FORBIDDEN_BROKER_FIELDS = [
    "brokerpassword",
    "brokerlogin",
    "brokerkey",
    "investorpassword",
    "broker_password",
    "broker_login",
    "broker_server",
    "mt5_password",
    "mt5_login",
]


async def verify_dev_authorization(
    request: Request,
    api_key: str | None = Security(api_key_header),
    auth_header: str | None = Header(None, alias="Authorization"),
) -> str:
    """
    DEVELOPMENT ONLY - NOT PRODUCTION READY.
    Enforces authorization abstraction for development and test phases.
    """
    # Accept either X-API-Key or Authorization: Bearer <token>
    provided_token = api_key
    if not provided_token and auth_header:
        if auth_header.startswith("Bearer "):
            provided_token = auth_header[7:].strip()
        else:
            provided_token = auth_header.strip()

    if not provided_token or provided_token != api_settings.dev_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Valid API key or Bearer token is required. (DEVELOPMENT ONLY)",
                }
            },
        )
    return "dev-operator"


async def reject_broker_credentials(request: Request) -> None:
    """
    SECURITY BOUNDARY:
    Strictly reject any request that attempts to supply broker credentials.
    Broker credentials must never touch the API or frontend.
    """
    # Check headers
    for header_name in request.headers:
        if any(forbidden in header_name.lower().replace("-", "").replace("_", "") for forbidden in FORBIDDEN_BROKER_FIELDS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "BROKER_CREDENTIALS_FORBIDDEN",
                        "message": "Broker credentials are never accepted through the API layer.",
                    }
                },
            )

    # Check query params
    for param_name in request.query_params:
        if any(forbidden in param_name.lower().replace("_", "") for forbidden in FORBIDDEN_BROKER_FIELDS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "BROKER_CREDENTIALS_FORBIDDEN",
                        "message": "Broker credentials are never accepted through the API layer.",
                    }
                },
            )


def get_correlation_id(request: Request) -> str:
    """Extract or generate unique correlation ID for request tracing."""
    corr_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
    return corr_id if corr_id else str(uuid4())
