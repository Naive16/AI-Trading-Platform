# Hybrid Architecture

**Status:** Accepted

## Context

The platform handles trading logic and will eventually interact with real financial infrastructure. This decision establishes a controlled architectural boundary.

## Decision

Use a mobile/PWA frontend, Cloudflare public layer, Python trading engine, deterministic risk engine, and MQL5/MT5 execution layer.

## Consequences

Separates user experience, orchestration, risk authority, and broker execution.

## Security Considerations

Changes that affect this decision require review and, where appropriate, a new or amended ADR.
