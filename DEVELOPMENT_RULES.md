# Development Rules

## 1. Read Before Coding

Agents must read the project context and architecture before making significant changes.

Required:
- AI_CONTEXT.md
- ARCHITECTURE.md
- SECURITY.md
- TRADING_RULES.md
- PRODUCT_SPEC.md
- AI_AGENT_HANDOFF.md

## 2. Security First

Never weaken security to make development easier.

Never commit secrets.

Never add live credentials.

Never expose broker credentials to frontend code.

## 3. Branching

Use feature branches.

Do not directly develop on protected `main`.

Recommended:
`feature/<name>`
`fix/<name>`
`security/<name>`

## 4. Pull Requests

Changes should be submitted through pull requests.

PRs should describe:
- what changed
- why
- tests run
- security implications
- migration/configuration requirements

## 5. Tests

New functionality must include appropriate tests.

Run:
- unit tests
- integration tests where relevant
- schema validation
- type checking
- linting
- security checks

## 6. Trading Safety

Never bypass the risk engine.

Never enable live trading as part of ordinary development.

Never create a deployment path that silently enables live trading.

## 7. Documentation

Update documentation when architecture, API contracts, security controls, or trading rules change.

Major architectural decisions require an ADR.

## 8. AI Agents

AI agents must:
- inspect existing code before editing
- preserve existing security controls
- avoid unnecessary rewrites
- explain consequential changes
- avoid fabricated test results
- never claim live trading works without actual validation

## 9. CI/CD

CI may validate and deploy non-trading components according to approved workflows.

Live trading activation must require explicit human approval.

## 10. Dependencies

Use maintained dependencies.

Review security advisories before introducing important dependencies.

## 11. Error Handling

Do not swallow trading-critical exceptions.

Trading failures must be observable and must fail safely.

## 12. Database Changes

Schema changes require migration planning and backwards-compatibility consideration where applicable.
