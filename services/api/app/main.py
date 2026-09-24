"""FastAPI Main Application."""
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    bot_router,
    health_router,
    orders_router,
    positions_router,
    risk_router,
    signals_router,
    system_router,
)
from .config import api_settings

app = FastAPI(
    title=api_settings.app_name,
    version="1.0.0",
    description="Deterministic Risk Engine & Simulation Trading Platform Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_and_security_middleware(request: Request, call_next):
    """Enforce correlation ID and broker credential prevention."""
    corr_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID") or str(uuid4())
    request.state.correlation_id = corr_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = corr_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Structured HTTP error response."""
    corr_id = getattr(request.state, "correlation_id", str(uuid4()))
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return JSONResponse(
            status_code=exc.status_code,
            content={**detail, "correlationId": corr_id},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": str(detail),
            },
            "correlationId": corr_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Structured validation error response."""
    corr_id = getattr(request.state, "correlation_id", str(uuid4()))
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg', 'validation error')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request body or parameters failed validation schema.",
                "details": errors,
            },
            "correlationId": corr_id,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all structured error response."""
    corr_id = getattr(request.state, "correlation_id", str(uuid4()))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Trading pipeline fails safe.",
            },
            "correlationId": corr_id,
        },
    )


# Register all endpoints
app.include_router(health_router)
app.include_router(system_router)
app.include_router(signals_router)
app.include_router(risk_router)
app.include_router(orders_router)
app.include_router(positions_router)
app.include_router(bot_router)
