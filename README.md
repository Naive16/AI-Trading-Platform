# AI Trading Platform

## Project Status

**Stage:** Architecture and development foundation  
**Live trading:** Disabled  
**Broker connection:** None  
**Purpose:** Security-first AI-assisted trading platform with a mobile-first dashboard, Python trading engine, deterministic risk engine, and MetaTrader 5 execution layer.

This repository is the single source of truth for the project's architecture, security model, trading rules, development workflow, API contracts, and AI-agent instructions.

## Target Architecture

User → Mobile/PWA → Cloudflare → Secure API → Python Trading Engine → Risk Engine → MQL5/MT5 → Broker

The eventual trading runtime will run on a Windows VPS. Cloudflare is the public application/API and security layer; it does not replace the Windows VPS required for the MT5 desktop terminal.

## Technology Direction

- Frontend: React + TypeScript + PWA
- Public platform/API: Cloudflare
- Trading engine: Python
- Execution: MQL5 + MetaTrader 5
- Runtime: Windows VPS
- Source control: GitHub
- Shared contracts: JSON Schema + TypeScript/Python types

## Security Principles

1. Capital protection comes before returns.
2. Live trading is disabled by default.
3. Broker credentials never belong in source control or the frontend.
4. AI-generated trade proposals cannot bypass the deterministic risk engine.
5. Critical failures fail closed: no new trades.
6. All important trading actions must be auditable.
7. Production trading requires explicit human authorization.

## Development Philosophy

The project will be built in controlled stages:

1. Repository and architecture foundation
2. Secure backend/API foundation
3. Deterministic risk engine
4. Simulated trading/execution adapter
5. Mobile-first dashboard
6. Backtesting and validation
7. MT5 demo integration
8. Windows VPS deployment
9. Extended demo validation
10. Only then consider controlled live trading

The platform must never trade merely to satisfy a daily profit target.

## Important

This repository is currently an architecture and development foundation. **Live trading is disabled.**
