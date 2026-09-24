# Phase 1 Security Implementation

## Security Boundary & Posture

Phase 1 establishes a security-first foundation based on the non-negotiable principle: **Capital protection comes before returns.**

### 1. Fail-Closed Design
- If any critical data point is missing, corrupt, or stale (such as account equity, account balance, free margin, or market quote age), the risk engine evaluates to `HALTED`. No orders can be placed.
- If the system is in any state other than `RUNNING` (`STOPPED`, `PAUSED`, `ERROR`, `EMERGENCY_STOP`, `DISCONNECTED`), order approval is impossible.

### 2. Elimination of Bypass Paths
- The only route to order creation in the platform is:
  `Signal -> Signal Validation -> Risk Engine -> APPROVED -> Mock Execution`.
- There is no direct execution interface. Every proposed trade must be validated and approved by the deterministic `RiskEngine`.
- A `WAIT` signal is an explicit, first-class outcome that immediately halts the pipeline with `WAIT_SIGNAL`.

### 3. Broker Credential Prevention
- The API explicitly rejects any request carrying broker credentials in headers, query parameters, or body (`broker_password`, `mt5_login`, `brokerkey`, etc.) with `400 Bad Request`.
- Broker credentials are strictly prohibited from entering source control, the API layer, or the frontend.

### 4. Development Authentication Abstraction
- The API includes an authentication dependency marked:
  `DEVELOPMENT ONLY - NOT PRODUCTION READY`.
- It validates `X-API-Key` or `Authorization: Bearer` against `dev_api_key`.
- It serves as a clear boundary without creating false production security claims.

### 5. Audit Logging & Sanitization
- Every stage of the trade lifecycle (signal creation, risk evaluation, risk approval, risk rejection, order request, order acknowledgement, position opened, bot state transitions, emergency stops) generates a structured `AuditEvent`.
- The `AuditLogger` automatically sanitizes metadata to redact sensitive values before logging.

### 6. Correlation & Tracing
- All requests are tagged with a unique `X-Correlation-ID` across middleware, responses, and error handlers to enable end-to-end auditability.

### 7. Explicit Safe Defaults
- `ENVIRONMENT=simulation`
- `LIVE_TRADING=false`
- `MT5_CONNECTED=false`
- `BROKER_CONNECTED=false`
- `DEFAULT_SYSTEM_STATE=STOPPED`
