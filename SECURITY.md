# Security Model

## Security Objective

Protect user accounts, credentials, trading infrastructure, and capital.

Security is a prerequisite for trading functionality, not a later enhancement.

## Secrets

Never commit:
- broker passwords
- broker login credentials
- API keys
- access tokens
- private keys
- Cloudflare production secrets
- database credentials
- session secrets

Use environment variables and appropriate secret-management mechanisms.

`.env` files must never be committed. `.env.example` contains placeholders only.

## Authentication

The production system must support strong authentication.

Planned controls:
- secure sessions/tokens
- MFA
- account lockout/rate limiting where appropriate
- secure password handling
- session expiration/revocation
- device/session visibility

## Authorization

Use least privilege.

At minimum, distinguish:
- normal user
- operator
- administrator

Authorization must be enforced server-side.

Frontend visibility is not authorization.

## Trading Authorization

AI output is never sufficient authorization for execution.

Every trade proposal must pass the deterministic risk engine.

Production/live activation requires explicit human authorization.

## Risk Engine Protection

No AI agent, UI request, strategy, or API caller may:
- disable risk checks
- modify risk limits without authorization
- bypass validation
- force execution after rejection

Changes to critical risk controls require elevated authorization and audit logging.

## Emergency Controls

Required controls:
- STOP BOT: prevents new trades
- EMERGENCY CLOSE: initiates emergency position handling according to configured safeguards

System states:
- RUNNING
- PAUSED
- STOPPED
- ERROR
- EMERGENCY_STOP
- DISCONNECTED

## Fail Closed

When critical safety information is unavailable, the system must not create new exposure.

Examples:
- stale market data
- missing account equity
- unknown open positions
- risk engine failure
- MT5 disconnect
- uncertain order state

## Audit Logging

Audit important events including:
- authentication
- authorization changes
- configuration changes
- risk changes
- bot start/stop/pause
- emergency controls
- generated signals
- risk decisions
- order requests
- order responses
- position changes
- errors
- system state transitions

Every trade lifecycle should have a correlation/trade lifecycle ID.

## Infrastructure

Production services should use:
- private network boundaries where possible
- firewall rules
- minimum exposed ports
- TLS
- secure remote administration
- patching
- backups
- monitoring
- alerting

The Windows VPS should not expose MT5 administration publicly.

## AI-Agent Security

AI coding agents:
- must not receive broker credentials
- must not create secret files with real values
- must not weaken security controls to make tests pass
- must not deploy live trading automatically
- must not push directly to protected main
- must document security-sensitive changes

## Incident Response

If compromise or unexpected trading behavior is suspected:
1. Stop new trading.
2. Preserve logs.
3. Isolate affected credentials/services.
4. Review active positions.
5. Rotate compromised secrets.
6. Investigate the event.
7. Restore from known-good configuration.
8. Document the incident.
