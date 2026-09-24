# Architecture

## High-Level Architecture

```text
USER
  |
  v
MOBILE / PWA FRONTEND
  |
  v
CLOUDFLARE PUBLIC PLATFORM
  |
  v
SECURE API
  |
  v
PYTHON TRADING ENGINE
  |
  v
DETERMINISTIC RISK ENGINE
  |
  v
MQL5 EXECUTION ADAPTER / EA
  |
  v
METATRADER 5
  |
  v
BROKER
```

## Core Components

### 1. Frontend
React + TypeScript + PWA, designed mobile-first.

The frontend displays system state and requests authorized actions through the API.

It must never contain broker credentials.

It must never connect directly to MT5.

### 2. Cloudflare Layer
Public application and API/security layer.

Potential responsibilities:
- routing
- WAF
- rate limiting
- authentication integration
- API exposure
- database/application data services
- observability

Cloudflare does not run the MT5 desktop terminal.

### 3. API
The API is the controlled boundary between the user interface and private trading services.

It must enforce:
- authentication
- authorization
- input validation
- rate limits
- audit logging
- request IDs
- safe error handling

### 4. Python Trading Engine
Responsibilities:
- market-data processing
- strategy analysis
- signal generation
- portfolio state
- backtesting
- monitoring
- communication with execution adapter

It proposes trades; it does not override the risk engine.

### 5. Risk Engine
The final deterministic authority before execution.

It evaluates:
- account equity
- available margin
- position size
- risk per trade
- stop loss
- take profit
- exposure
- drawdown
- daily/weekly loss
- spread
- slippage
- market-data freshness
- system health
- trading session
- existing positions
- consecutive losses

Output should be an explicit decision such as:
`APPROVED`, `REJECTED`, or `HALTED`.

### 6. MQL5 / MT5
MQL5 is the execution-side adapter/EA.

MT5 communicates with the broker.

MT5 is not a public API and is not directly exposed to the frontend.

### 7. Windows VPS
Runs the private trading runtime:
- MT5
- MQL5 EA
- Python services
- risk engine
- monitoring

## Data Flow

1. Market data enters the trading engine.
2. Strategy/analysis produces a signal proposal.
3. Signal is validated.
4. Risk engine evaluates the proposal.
5. Rejected proposals terminate without execution.
6. Approved proposals are passed to the execution layer.
7. Execution result is recorded.
8. Positions/account state are synchronized.
9. Audit events are emitted.

## Failure Behavior

If any critical dependency is unavailable or inconsistent:
- no new trade
- fail closed
- preserve logs
- alert operator
- attempt safe recovery

Examples:
- stale market data
- MT5 disconnected
- account data unavailable
- risk calculation failure
- inconsistent position state
- API authorization failure
- execution acknowledgement missing

## Runtime States

- `RUNNING`
- `PAUSED`
- `STOPPED`
- `ERROR`
- `EMERGENCY_STOP`
- `DISCONNECTED`

## Security Boundary

No public component should have direct broker credentials.

The path to execution is intentionally layered:

Frontend → API → Trading Engine → Risk Engine → Execution Layer → MT5 → Broker.

No component may skip a layer merely for convenience.
