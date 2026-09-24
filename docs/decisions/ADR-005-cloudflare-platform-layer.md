# Cloudflare Platform Layer

**Status:** Accepted

## Context

The platform handles trading logic and will eventually interact with real financial infrastructure. This decision establishes a controlled architectural boundary.

## Decision

Use Cloudflare for the public application/API/security layer, not as the MT5 runtime.

## Consequences

Improves public security and availability while preserving the private trading runtime boundary.

## Security Considerations

Changes that affect this decision require review and, where appropriate, a new or amended ADR.
