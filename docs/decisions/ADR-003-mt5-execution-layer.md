# MT5 Execution Layer

**Status:** Accepted

## Context

The platform handles trading logic and will eventually interact with real financial infrastructure. This decision establishes a controlled architectural boundary.

## Decision

Use MQL5/MetaTrader 5 as the broker-facing execution infrastructure.

## Consequences

Preserves compatibility with MT5 brokers while keeping it out of the public application.

## Security Considerations

Changes that affect this decision require review and, where appropriate, a new or amended ADR.
