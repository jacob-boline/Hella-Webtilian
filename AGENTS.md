# AGENTS.md

## Start Here
- Read `ARCHITECTURE.md` before making structural or flow-level changes.
- Treat this file as the enforcement/orientation layer; details live in `ARCHITECTURE.md`.

## Architectural Guardrails
Agents should avoid introducing, unless explicitly requested:
- client-side routing frameworks
- JSON API layers for flows currently implemented as HTMX partials
- React/Vue islands for features already served by Django templates + HTMX
- duplicate modal systems outside the global shell

Rationale: the current architecture is intentionally server-rendered with HTMX-driven partial interactions, not a client-routed SPA.

## Shell Ownership Model
`hr_common/templates/hr_common/base.html` is the shell owner for:
- intro overlay
- global modal container/loader flow
- cart sidebar/drawer + floating cart affordance
- global message bar
- top-level parallax shell structure

## HTMX Response Contract
Use the existing helper/adapter layers:
- `hr_common/utils/http/htmx.py`
- `hr_common/utils/htmx_responses.py`

Contract notes:
- Use `HX-Trigger` / `HX-Trigger-After-Settle` response headers for event-driven UX.
- Prefer `hx_load_modal(...)`, `hx_trigger(...)`, and merge helpers for modal/message timing.
- Keep auth/csrf/permission edge handling in `htmx_responses` primitives.

## Where New Code Goes
- Domain behavior belongs in the owning app (`hr_about`, `hr_access`, `hr_bulletin`, `hr_live`, `hr_payment`, `hr_shop`, etc.).
- Shared cross-cutting behavior belongs in `hr_common` or `hr_core`.
- HTMX response/event utilities belong in shared HTTP utility layers, not duplicated per-view.
- Reusable UI data plumbing belongs in context processors / template tags / mixins when already patterned there.
- Follow existing extension points before creating new primitives:
  - middleware: `hr_core/middleware/*`, `hr_common/middleware/*`
  - context processors: `hr_shop/context_processors.py`, `hr_common/context_processors.py`
  - template tags: `hr_common/templatetags/*`, `hr_core/templatetags/*`, `hr_shop/templatetags/*`
  - model fields: `hr_common/db/fields.py`, `hr_storage/fields.py`
  - mixins: `hr_core/mixins.py`

## Commands (Source of Truth)
NPM (`package.json`):
- `npm run dev`
- `npm run dev:tunnel`
- `npm run build` / `npm run vite:build`
- `npm run django:run`
- `npm run vite:dev`
- `npm run lint:css` / `npm run lint:css:fix`

Docker / Compose / Scripts:
- `./scripts/setup.sh`
- `./scripts/start-dev.sh`
- `docker compose -f docker-compose.dev.yml build`
- `docker compose -f docker-compose.dev.yml up -d`
- `docker compose -f docker-compose.dev.yml exec web python manage.py <command>`

Manage.py commands (grouped):
- Environment/bootstrap and seeding:
  - `python manage.py init`
  - `python manage.py seed_data`
  - `python manage.py seed_hr_about`
  - `python manage.py seed_hr_live`
  - `python manage.py seed_hr_bulletin`
  - `python manage.py seed_hr_shop`
- Static/media pipeline:
  - `python manage.py seed_media_assets`
  - `python manage.py media_sweep`
  - `python manage.py build_responsive_backgrounds`
  - `python manage.py regen_media_variants [--recipe ... --limit ... --since ...]`
  - `python manage.py imgbatch`
- Access/email/shop operations:
  - `python manage.py setup_roles`
  - `python manage.py send_email_healthcheck --to <email> [--provider default|mailjet|zoho]`
  - `python manage.py cleanup_checkout_drafts`

## Dev vs Prod Quick Orientation
- Settings modules:
  - dev: `hr_config.settings.dev`
  - production Docker: `hr_config.settings.prod_docker`
- Dev adds `debug_toolbar`, `django_browser_reload`, and `django_rq`.
- Current dev Docker flow intentionally builds Vite assets and runs `collectstatic`.

## Non-Goals
- Do not introduce testing guidance here yet.
