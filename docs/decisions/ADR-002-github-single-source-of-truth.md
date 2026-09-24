# GitHub Single Source of Truth

**Status:** Accepted

## Context

The platform handles trading logic and will eventually interact with real financial infrastructure. This decision establishes a controlled architectural boundary.

## Decision

Keep architecture, security, contracts, agent instructions, tests, and implementation in the controlled GitHub repository.

## Consequences

Agents can work consistently and changes are auditable.

## Security Considerations

Changes that affect this decision require review and, where appropriate, a new or amended ADR.
