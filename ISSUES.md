# Backlog

## Testing and typing
- Add `pytest` + `pytest-django` scaffolding and seed tests for auth, cart, and checkout flows.
- Introduce `mypy` (with Django plugin) to enforce typing across apps; annotate models/services for critical paths.

## Python linting/formatting
- Adopt `ruff` for fast linting and `black` for formatting, with CI gates.

## Payments hardening
- Add Stripe webhook signature verification and idempotency handling around `WebhookEvent`.
- Improve retry/backoff and error surfacing in Stripe checkout session creation.

## Observability
- Add structured logging (e.g., `structlog`) and request tracing (OpenTelemetry) across Django views/services/payments.

## Frontend quality
- Add JavaScript linting (`eslint` + `prettier`) for `hr_core/static_src`.
- Add component/unit tests for frontend modules (e.g., Vitest) to cover interactive behaviors.

## Developer experience
- Containerize dev/CI (Dockerfile + docker-compose) to standardize Django + Vite + Stripe webhook environments.
- Add CI workflows (GitHub Actions) running lint, type, and test suites.

## Admin/ops tooling
- Extend Django admin for shop/payment models to aid operations and support staff.
- Add database constraints/tests around inventory and order state transitions to ensure consistency.

## Security and abuse prevention
- Add rate limiting/bot protection to auth and checkout flows.

## API/UX
- Expose a limited public API (e.g., DRF/htmx endpoints) for product/catalog data to enable integrations and caching.
