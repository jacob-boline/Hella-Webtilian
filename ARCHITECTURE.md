# ARCHITECTURE.md

## 1) Overview
Hella Webtilian is a Django 5 modular monolith with domain apps (`hr_about`, `hr_access`, `hr_bulletin`, `hr_live`, `hr_payment`, `hr_shop`, etc.) and a Vite-based frontend asset pipeline.

The delivery model can be described along three complementary axes:

### Navigation model
**Server-routed navigation.**  
URLs map directly to Django views. Full-page renders remain valid entry points, while partial responses allow progressive enhancement without introducing a client-side router.

### UI structure
**Persistent server-rendered shell.**  
A stable base template provides shared UI surfaces and layout structure while content is composed through templates and partial responses.

### Interaction pattern
**HTMX-driven partial rendering with modal orchestration.**  
User interactions are primarily handled through server-rendered HTML fragments swapped into the DOM and coordinated via HTMX trigger events.

Architecturally, the project is a **server-rendered modular monolith with an HTMX-enhanced multi-page navigation model**.  
From a user interaction perspective, it behaves like a **continuous shell-based interface** where most actions update portions of the page rather than triggering full navigation.

Primary services are PostgreSQL (data) and Redis (background jobs when configured). Email and payment integrations are implemented via Mailjet/SMTP and Stripe.

### Implementation anchors
Core architectural entry points include:

- Shell template: `hr_common/templates/hr_common/base.html`
- HTMX helpers: `hr_common/utils/http/htmx.py`
- HTMX adapters: `hr_common/utils/htmx_responses.py`
- Client init hooks: `hr_core/static_src/js/meta-init.js`
- Main bundle entry: `hr_core/static_src/js/main.js`

---

## 2) Product Surface

### Shows / Live
- Home “Shows” content is rendered inside the parallax shell.
- Live domain data includes venues/bookers/musicians/acts/shows (`hr_live` models).
- Dedicated upcoming/past routes are present.
- Seed command exists for live domain data.

### Merch
- Home merch uses product/variant-driven cards.
- Add-to-cart and detail interactions are HTMX-driven.
- Admin-side product manager partial endpoints live under `hr_shop` routes.

### About
- About combines intro copy, carousel, and quotes.
- Carousel/quotes are modular partials and frontend modules (`initCarousel`, `initQuotes`).
- Backed by `CarouselSlide` and `PullQuote`.

### Bulletin
- Bulletin uses HTMX sentinel pagination for infinite loading.
- Data model includes `Post` and `Tag` with publish/pin behavior.
- Frontend includes tag overflow/expansion handling.

---

## 3) Core User Flows

### Cart → Checkout → Email Confirmation → Payment
- Checkout is staged as details → email confirmation wait/confirm → review/create order → pay → payment result/receipt.
- Stripe checkout session creation and webhook completion are handled in `hr_payment`.
- Email confirmation tokens gate guest checkout progression.
- Checkout resume restores context and can reopen modal state.

### Tab Handoff
- `hr_core/static_src/js/modules/tab-handoff.js` uses `BroadcastChannel` for handoff behavior.
- URL params (`handoff`, `modal`, `modal_url`, token params) bootstrap landing modal behavior and are cleaned afterward.

### Guest Checkout → Order Claiming
- Guest context uses signed `guest_checkout_token` (cookie/header).
- Post-purchase account create/claim flows are exposed in `hr_access`.
- Unclaimed order claiming exists in account flows.
- Order receipt token flow supports secure result/receipt access for non-owner contexts.

---

## 4) Front-End Model

### Shell ownership model
`hr_common/templates/hr_common/base.html` is the persistent shell and owns:

- intro overlay/startup animation surface
- global modal container + modal loader trigger point
- cart sidebar/drawer controls and floating cart affordance
- global message bar/notification surface
- top-level parallax section structure on the home shell

### Section presentation model
- Home sections (`shows`, `merch`, `about`, `bulletin`) use parallax sections and generated background/wipe CSS via `build_responsive_backgrounds`.
- Intro overlay behavior is coordinated with prepaint removal in `hr_core/static_src/js/main.js`.

### Bundle boundaries
Vite entrypoints:

- `hr_core/static_src/js/main.js`
- `hr_core/static_src/css/critical.css`
- `hr_core/static_src/css/noncritical.css`

### Performance loading strategy
Implemented patterns include:

- preloading key image/font assets
- immediate critical CSS
- deferred noncritical CSS via `media="print"` flip + noscript fallback
- lazy loading noncritical JS after first paint/idle
- responsive `srcset`/`sizes` usage for merch/about/bulletin media

---

## 5) Back-End Model

### Domain app model
The project is organized as domain apps with local `models/views/forms/services/queries/tokens/signals` patterns.

### Tokens and handoff
Signed-token based flows are used for email confirmation, account signup confirmation, guest checkout context, and order receipt access.

### Background jobs
`django-rq` + Redis are used for async/media jobs; production can disable RQ app when Redis is absent (`hr_config/settings/prod_docker.py`).

### Storage strategy
- Static files use WhiteNoise compressed manifest storage.
- Media defaults to filesystem and can switch to S3 media backend when enabled.

---

## 6) Cross-Cutting Primitives

### HTMX HTTP utilities
`hr_common/utils/http/htmx.py` provides:

- `merge_hx_trigger(resp, extra)`
- `merge_hx_trigger_after_settle(resp, extra)`
- `hx_trigger(payload, status=204)`
- `hx_load_modal(url, after_settle=None, status=204)`
- `is_htmx(request)`

These utilities define the response-header event contract around `HX-Trigger` and `HX-Trigger-After-Settle`.

### HTMX response adapters
`hr_common/utils/htmx_responses.py` provides:

- `hx_login_required`
- `hx_superuser_required`
- `csrf_failure`

### Messaging infrastructure
- Server-side structured logging helpers/middleware live in shared layers (`hr_common`/`hr_core`).
- UI messaging uses the shell message/modal flow and HTMX trigger events (for example `showMessage`).
- `hr_common/utils/http/messages.py` provides `show_message(...)` payload shaping.

### Middleware
- `hr_core/middleware/request_id.py`
- `hr_common/middleware/logging_context.py`
- `hr_core/middleware/htmx_exception.py`
- `hr_core/middleware/media_cache.py`

### Context processors
- `hr_shop/context_processors.py` (`cart_item_count`)
- `hr_common/context_processors.py` (`debug` flag)

### Template tags / filters
- `hr_core/templatetags/responsive_images.py`
- `hr_shop/templatetags/shop_tags.py`
- `hr_shop/templatetags/shop_images.py`
- `hr_common/templatetags/*`

### Custom model fields
- `hr_common/db/fields.py` → `NormalizedEmailField`
- `hr_storage/fields.py` → `PrivateFileField`

### Mixins
- `hr_core/mixins.py` → `HtmxTemplateMixin`

---

## 7) Dev vs Prod Differences
- Settings modules:
  - dev: `hr_config.settings.dev`
  - production Docker: `hr_config.settings.prod_docker`
- Dev adds `debug_toolbar`, `django_browser_reload`, and `django_rq`; production disables debug tooling.
- Dev can fallback to SQLite when `DATABASE_URL` is absent; production requires PostgreSQL URL.
- Current dev Docker flow intentionally builds Vite assets + runs `collectstatic` for prod-like static serving through nginx.
- Optional HMR path exists but is commented/guarded.
- Production enables secure redirect/cookie posture; dev remains local-friendly.

---

## 8) Operational Tooling

### Manage.py commands

Environment/bootstrap and seeding:
- `python manage.py init`
- `python manage.py seed_data`
- `python manage.py seed_hr_about`
- `python manage.py seed_hr_live`
- `python manage.py seed_hr_bulletin`
- `python manage.py seed_hr_shop`

Static/media pipeline:
- `python manage.py seed_media_assets`
- `python manage.py media_sweep`
- `python manage.py build_responsive_backgrounds`
- `python manage.py regen_media_variants [--recipe ... --limit ... --since ...]`
- `python manage.py imgbatch`

Access/email/shop operations:
- `python manage.py setup_roles`
- `python manage.py send_email_healthcheck --to <email> [--provider default|mailjet|zoho]`
- `python manage.py cleanup_checkout_drafts`

### Docker and Compose
- Docker targets include `py-builder`, `node-builder`, `prod`, and `dev`.
- Entrypoints:
  - `docker/entrypoint.sh`
  - `docker/entrypoint.dev.sh`
- Development compose file: `docker-compose.dev.yml` (`db`, `redis`, `web`, `rq_worker`, `nginx`).

### Command sources of truth
NPM (`package.json`):

- `npm run dev`
- `npm run dev:tunnel`
- `npm run build` / `npm run vite:build`
- `npm run django:run`
- `npm run vite:dev`
- `npm run lint:css` / `npm run lint:css:fix`

Scripts and compose:

- `./scripts/setup.sh`
- `./scripts/start-dev.sh`
- `docker compose -f docker-compose.dev.yml build`
- `docker compose -f docker-compose.dev.yml up -d`
- `docker compose -f docker-compose.dev.yml exec web python manage.py <command>`

---

## 9) Architectural Guardrails
Agents should avoid introducing, unless explicitly requested:

- client-side routing frameworks
- JSON API layers for flows currently implemented as HTMX partials
- React/Vue islands for features already served by Django templates + HTMX
- duplicate modal systems outside the global shell

These guardrails preserve a server-driven interaction model centered around HTML fragment rendering and shared shell orchestration.
