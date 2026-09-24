# AI Context

## Mission

Build a security-first AI-assisted trading platform that can analyze markets, generate trade proposals, apply deterministic risk controls, and eventually execute approved trades through MetaTrader 5.

## Source of Truth

GitHub is the single source of truth.

Before making significant changes, AI agents must read:

- `AI_CONTEXT.md`
- `ARCHITECTURE.md`
- `SECURITY.md`
- `TRADING_RULES.md`
- `DEVELOPMENT_RULES.md`
- `PRODUCT_SPEC.md`
- `AI_AGENT_HANDOFF.md`

If code and documentation conflict, stop and resolve the conflict rather than silently choosing an interpretation.

## Architecture

User
→ Mobile/PWA Frontend
→ Cloudflare
→ Secure API
→ Python Trading Engine
→ Deterministic Risk Engine
→ MQL5/MT5
→ Broker

The frontend must never communicate directly with MT5.

## Runtime Boundaries

### Cloudflare
Public application/API/security layer.

Responsibilities may include:
- routing
- API gateway
- authentication integration
- WAF/rate limiting
- public web application
- application data services

### Windows VPS
Private trading runtime.

Responsibilities:
- MetaTrader 5 desktop terminal
- MQL5 EA
- Python trading engine
- risk engine
- local monitoring/health services

### MetaTrader 5
Broker-facing execution infrastructure, not the user-facing application.

## AI Responsibilities

AI may:
- analyze structured market data
- propose signals
- explain signals
- summarize performance
- assist with research
- interpret non-authoritative information
- help operators understand system state

AI must not:
- bypass the risk engine
- directly access broker credentials
- directly authorize a rejected trade
- disable safety controls
- invent market/account data
- claim profitability that has not been demonstrated

The deterministic risk engine is the final authority on whether an order proposal may proceed.

## Signal States

The only initial signal actions are:

- `BUY`
- `SELL`
- `WAIT`

`WAIT` is a first-class outcome. No trade is preferable to an unsafe or unsupported trade.

## Performance Objective

A target such as `$500/day` may be used as a research/performance objective. It is not a guarantee, mandatory daily return, or reason to force trades or increase risk.

The system must be allowed to make zero trades.

## Safety Defaults

- Demo/simulation first
- Live trading off
- No real broker credentials during development
- No secrets in Git
- Fail closed
- Human approval for production/live activation
- Full audit trail
- Emergency stop available

## Agent Roles

### Claude
Primary architecture and engineering agent; complex implementation, review, testing, and security work.

### Freebuff
Rapid full-stack implementation and integrations, while following the same repository rules.

### Antigravity
Frontend, PWA, mobile UX, and interface implementation.

### Google AI Studio
Initial repository/architecture assistance only. It is not the authoritative project owner.

All agents must follow this repository's documentation.
