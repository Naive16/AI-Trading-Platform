# Phase 1 Architecture: Backend & Deterministic Risk Engine

## Overview

Phase 1 establishes the core backend foundation and deterministic risk engine for the AI Trading Platform. It implements a non-bypassable, 5-stage sequential execution pipeline operating purely in a simulated in-memory environment.

```
SIGNAL
   ↓
SIGNAL VALIDATION
   ↓
RISK ENGINE (Deterministic 13-point audit)
   ↓
APPROVED / REJECTED / HALTED Gate
   ↓
MOCK EXECUTION (Simulation Only)
```

## Implemented Components

### 1. Trading Engine (`services/trading-engine/`)
- **Models (`app/models/`)**:
  - `Signal`: Strict adherence to `shared/schemas/signal.schema.json`.
  - `Account`: Strict adherence to `shared/schemas/account.schema.json`.
  - `OrderRequest` & `OrderAcknowledgement`: Strict adherence to `shared/schemas/order.schema.json`.
  - `Position`: Strict adherence to `shared/schemas/position.schema.json`.
  - `RiskDecision`: Strict adherence to `shared/schemas/risk-decision.schema.json`.
  - `SystemState`: `RUNNING`, `PAUSED`, `STOPPED`, `ERROR`, `EMERGENCY_STOP`, `DISCONNECTED`.
  - `MarketQuote` & `InstrumentSpec`: Abstraction of symbol specifications without broker-hardcoded constants.
  - `AuditEvent`: Structured event records for audit logging.
- **Signals (`app/signals/`)**:
  - `SignalValidator`: Validates structure, prices, stop loss geometry (BUY stop loss below entry, SELL stop loss above entry), and timeframe conventions.
- **Deterministic Risk Engine (`app/risk/`)**:
  - `RiskEngine`: Ordinary deterministic Python code. **Zero LLM / AI dependencies.**
  - Implements all 13 core checks:
    1. Signal validity (structure, price positive, timeframe)
    2. WAIT signal handling (first-class rejection with reason code `WAIT_SIGNAL`)
    3. Account data integrity (fails safe with `HALTED` if balance, equity, or free margin is missing/corrupted)
    4. Mandatory protective stop loss
    5. Take profit and risk/reward validation
    6. Position sizing derivation based on equity, risk percentage, and stop loss distance
    7. Maximum risk per trade limit (`maxRiskPerTrade`)
    8. Symbol and portfolio exposure limits, plus concurrent trades limit
    9. Daily loss protection (halts new trading if breached)
    10. Maximum account drawdown protection (halts if breached)
    11. Consecutive losses streak protection (halts after configured consecutive losses)
    12. Market data integrity (freshness check within configured age threshold, spread validation, market open check)
    13. System state gating (only permits approval when state is `RUNNING`; rejects if `STOPPED`, `PAUSED`, `EMERGENCY_STOP`; halts if `ERROR` or `DISCONNECTED`)
  - `PositionSizer`: Derives volume from risk budget and distance to stop loss.
- **Simulation Execution Adapter (`app/execution/`)**:
  - `ExecutionAdapter`: Abstract base interface.
  - `MockExecutionAdapter`: In-memory simulated execution. Simulates fills, rejections, slippage, and position tracking. **No external network or MT5 connection.**
- **Portfolio & Account State (`app/portfolio/`)**:
  - `PortfolioManager`: In-memory tracking of balance, equity, margin, free margin, drawdown, open positions, daily PnL, and loss streaks.
- **Observability (`app/monitoring/`)**:
  - `AuditLogger`: Thread-safe, sanitized event recorder. Redacts credentials and secret patterns.

### 2. FastAPI API (`services/api/`)
- Public endpoints:
  - `GET /health`: Reports `{ status: "healthy", environment: "simulation", liveTrading: false, mt5Connected: false, brokerConnected: false }`.
- Protected endpoints (via development token abstraction):
  - `GET /api/v1/system/status`: Full system status and active risk limits.
  - `POST /api/v1/signals/evaluate`: Signal validation and risk evaluation.
  - `POST /api/v1/risk/evaluate`: Standalone risk engine decision evaluation.
  - `POST /api/v1/orders/simulate`: End-to-end simulation execution pipeline.
  - `GET /api/v1/positions`: Open simulated positions.
  - `GET /api/v1/bot/status`: Execution state and portfolio summary.
  - `POST /api/v1/bot/start`: Transition to `RUNNING`.
  - `POST /api/v1/bot/pause`: Transition to `PAUSED`.
  - `POST /api/v1/bot/stop`: Transition to `STOPPED`.
  - `POST /api/v1/emergency/stop`: Transition to `EMERGENCY_STOP`.

## Intentionally NOT Implemented (Out of Scope for Phase 1)

1. **Frontend / UI**:
   - Zero React components, zero HTML dashboards, zero CSS. Frontend is completely untouched.
2. **MetaTrader 5 & Broker Connectivity**:
   - Zero MT5 connections, zero MQL5 EAs, zero broker accounts.
3. **Live Trading**:
   - Strictly disabled (`LIVE_TRADING=false`).
4. **Cloud / Infrastructure Deployment**:
   - No Cloudflare Workers, Windows VPS setups, or cloud database provisioning.
5. **AI / LLM Integrations**:
   - No OpenAI, Gemini, or Claude API calls inside the execution pipeline. The risk engine is strictly deterministic code.
6. **Strategy Profitability / Backtesting Engine**:
   - No strategy parameter optimization or historical backtesting engine.
