# Contributing

## Workflow

1. Create a feature/fix/security branch.
2. Read project documentation.
3. Make the smallest safe change.
4. Add/update tests.
5. Run validation locally.
6. Update documentation if needed.
7. Open a pull request.
8. Review CI results.
9. Obtain appropriate human review.
10. Merge into protected main.

## Commit Style

Use clear, focused commits.

Examples:
- `feat: add risk decision schema`
- `fix: reject stale market data`
- `security: harden API authorization`
- `docs: update MT5 architecture`

## Pull Request Requirements

Include:
- summary
- motivation
- files/components changed
- tests run
- security considerations
- database/config changes
- deployment considerations

## Trading Changes

Any change affecting:
- risk
- order execution
- position sizing
- broker communication
- authentication
- emergency controls

requires explicit review.

## AI-Generated Code

AI-generated code is treated like any other code.

It must:
- be reviewed
- be tested
- follow security rules
- follow architecture
- not be merged blindly
