# Risk Engine Authority

**Status:** Accepted

## Context

The platform handles trading logic and will eventually interact with real financial infrastructure. This decision establishes a controlled architectural boundary.

## Decision

A deterministic risk engine is the final authority before order execution.

## Consequences

Prevents AI or UI components from bypassing capital-protection controls.

## Security Considerations

Changes that affect this decision require review and, where appropriate, a new or amended ADR.
