# Product Specification

## Product

Security-first AI-assisted trading platform.

## Primary User Experience

A mobile-first web/PWA dashboard controls and monitors a backend trading runtime.

The phone does not run the MT5/Python trading engine.

## Dashboard

Planned areas:

- Dashboard
- Market Overview
- AI Signals
- Open Positions
- Trade History
- Performance
- Risk
- Bot Controls
- Notifications
- System Health
- Settings

## Bot Controls

Primary controls:
- START BOT
- PAUSE BOT
- STOP BOT
- EMERGENCY CLOSE

These controls require server-side authorization and audit logging.

## Market Overview

Potential information:
- symbols
- prices
- charts
- volatility
- spread
- market status
- timeframe
- signal context

## AI Signals

Display:
- symbol
- timeframe
- action
- confidence
- entry
- stop loss
- take profit
- risk
- strategy
- timestamp
- risk decision

## Positions

Display:
- symbol
- side
- volume
- entry
- current price
- stop loss
- take profit
- unrealized P/L
- lifecycle ID

## Risk

Display:
- equity
- balance
- margin
- available margin
- daily loss
- drawdown
- exposure
- current risk state
- active limits

## System Health

Display:
- API health
- trading engine health
- risk engine health
- MT5 connection state
- market-data freshness
- last heartbeat
- current runtime state

## Notifications

Potential notifications:
- bot state changes
- rejected trades
- execution errors
- risk-limit events
- MT5 disconnects
- emergency events
- security events

## Multi-User Direction

The architecture should support future SaaS/multi-user operation, with strict tenant isolation and role-based authorization.

## Demo-First

All initial product functionality should operate without real-money trading.

The demo environment must be clearly identified.

## Non-Goals

At the current stage:
- no guaranteed profitability
- no automatic live trading
- no broker credential collection in frontend
- no forced trading
