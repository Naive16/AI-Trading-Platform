# Trading Rules

## Purpose

Define non-negotiable trading safety constraints.

Final numeric parameters are configuration decisions and should not be invented prematurely.

## Core Rules

1. No trade without a valid signal.
2. No trade without a valid stop loss.
3. No trade without passing the risk engine.
4. No trade when critical market/account data is stale or unavailable.
5. No trade when the system is not in an execution-enabled state.
6. No trade solely to meet a daily profit target.
7. The system may always choose `WAIT`.

## Configurable Risk Controls

The following must be configurable and explicitly validated:

- risk per trade: TBD
- maximum daily loss: TBD
- maximum weekly loss: TBD
- maximum account drawdown: TBD
- maximum concurrent trades: TBD
- maximum exposure per symbol: TBD
- maximum portfolio exposure: TBD
- maximum consecutive losses: TBD
- maximum spread: TBD
- maximum slippage: TBD
- permitted trading sessions: TBD

## Position Sizing

Position sizing must be derived from:
- account equity
- configured risk percentage
- entry price
- stop-loss distance
- instrument specifications
- contract size
- broker constraints

The system must reject invalid or zero/negative sizing.

## Stop Loss

Every executable trade must have a valid protective stop according to the strategy and instrument constraints.

## Take Profit

Take profit must satisfy configured strategy/risk constraints.

Risk/reward requirements must be validated before execution.

## Exposure

Before approving an order, calculate the effect on:
- existing positions
- symbol exposure
- correlated exposure where supported
- total account risk
- margin requirements

## Market Conditions

Reject or halt execution when:
- market data is stale
- spread exceeds configured maximum
- slippage conditions are unacceptable
- account state is unavailable
- MT5 connection is unhealthy

## Consecutive Losses

A configurable loss-streak protection mechanism must be supported.

Exact thresholds are TBD.

## Drawdown Protection

The platform must track:
- current drawdown
- daily loss
- weekly loss
- peak equity
- equity floor

Configured limits must halt new trading when breached.

## Emergency Stop

Emergency stop must prevent new exposure and trigger the configured emergency workflow.

## Backtesting

Backtests must not be treated as proof of future profitability.

Validation should include:
- in-sample/out-of-sample separation
- walk-forward testing
- parameter sensitivity
- drawdown analysis
- Monte Carlo or equivalent robustness analysis where appropriate

## Profit Objective

A target such as `$500/day` is a research objective only.

It must never override:
- risk limits
- market conditions
- signal quality
- capital protection
