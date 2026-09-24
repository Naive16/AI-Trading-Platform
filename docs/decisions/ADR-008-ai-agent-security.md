# AI Agent Security

**Status:** Accepted

## Context

The platform handles trading logic and will eventually interact with real financial infrastructure. This decision establishes a controlled architectural boundary.

## Decision

All coding agents must follow repository security and architecture rules and must not receive live broker credentials.

## Consequences

Reduces accidental security and operational failures caused by automated development.

## Security Considerations

Changes that affect this decision require review and, where appropriate, a new or amended ADR.
