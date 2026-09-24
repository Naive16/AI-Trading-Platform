# AI Agent Handoff

## Purpose

This document allows future AI coding agents to enter the project without losing architectural context.

## Mandatory Reading

Before significant work, read:

1. `AI_CONTEXT.md`
2. `ARCHITECTURE.md`
3. `SECURITY.md`
4. `TRADING_RULES.md`
5. `DEVELOPMENT_RULES.md`
6. `PRODUCT_SPEC.md`

Then inspect the existing implementation before changing it.

## Agent Responsibilities

### Claude
Primary engineering/architecture agent.

Use for:
- system architecture
- backend implementation
- risk-engine implementation
- complex debugging
- security review
- code review
- testing strategy

### Freebuff
Rapid full-stack development and integrations.

Must follow repository contracts and security rules.

### Antigravity
Frontend/PWA/mobile UX implementation.

Must not introduce direct broker/MT5 access into the frontend.

### Google AI Studio
Initial repository/architecture assistance only.

## Rules for All Agents

- GitHub is the source of truth.
- Do not invent requirements.
- Do not expose secrets.
- Do not bypass risk controls.
- Do not connect live trading during development.
- Do not fabricate test or performance results.
- Do not rewrite unrelated systems unnecessarily.
- Update documentation when contracts change.
- Use feature branches and pull requests.
- Treat security-sensitive changes as high risk.

## Before Starting a Task

State internally:
- current architecture
- affected components
- security boundary
- tests required
- rollback/recovery considerations

## After Completing a Task

Verify:
- tests pass
- security checks pass
- documentation is consistent
- no secrets were introduced
- live trading remains disabled unless explicitly authorized

## Handoff Format

For significant work, record:
- objective
- implementation
- files changed
- tests
- unresolved issues
- next recommended step
