<a id="top"></a>

<h1 align="center">Hella Webtilian</h1>

<p align="center">
  Django + HTMX SPA-style band website with parallax UX, embedded Stripe checkout, and high-parity Docker environments.
</p>

<p align="center">
  <a href="https://hellareptilian.com">Live Demo</a> •
  <a href="#guided-tour">Guided Tour</a> •
  <a href="#documentation-map">Documentation Map</a> •
  <a href="ARCHITECTURE.md">Architecture</a> •
  <a href="AGENTS.md">Contributor Guide</a>
</p>

<p align="center">
  <img alt="Django" src="https://img.shields.io/badge/Django-5.x-0C4B33?style=flat&logo=django&logoColor=white">
  <img alt="HTMX" src="https://img.shields.io/badge/HTMX-Driven-3366CC?style=flat">
  <img alt="Docker" src="https://img.shields.io/badge/Dockerized-2496ED?style=flat&logo=docker&logoColor=white">
  <img alt="Stripe" src="https://img.shields.io/badge/Stripe-Embedded-635BFF?style=flat&logo=stripe&logoColor=white">
  <img alt="Postgres" src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white">
</p>

---

## Demo

Live site: https://hellareptilian.com

![App Preview](docs/screenshots/preview.webp)

<details>
<summary>Visual walkthrough</summary>

![Walkthrough](docs/screenshots/walkthrough.gif)

</details>

<p align="right"><a href="#top">↑ Back to top</a></p>


---

<a id="guided-tour"></a>
## Guided Tour

Suggested exploration path through the live app:

1. Home shell + parallax sections  
   https://hellareptilian.com/

2. Merch flow (variant selection → cart)  
   https://hellareptilian.com/

3. Guest checkout → embedded Stripe flow  
   https://hellareptilian.com/

4. Bulletin infinite scroll + tagging  
   https://hellareptilian.com/

<p align="right"><a href="#top">↑ Back to top</a></p>

---

<a id="overview"></a>
## Overview

Hella Webtilian is a Django + HTMX modular monolith designed to deliver a continuous, SPA-like interface without introducing a client-side router.

Django templates remain canonical entry points while HTMX powers modal orchestration, partial rendering, and progressive enhancement across the application shell.

Key ideas:

• Server-rendered navigation with persistent UI shell  
• Event-driven UX through HX-Trigger headers  
• High-parity Dockerized dev/prod environments  
• Performance-first media and animation strategy  

<p align="right"><a href="#top">↑ Back to top</a></p>

---

<a id="documentation-map"></a>
## Documentation Map

### Start Here
- Contributor Orientation (AGENTS) → AGENTS.md
- Architecture Guide → ARCHITECTURE.md

### Architecture (ARCHITECTURE.md)
- Overview
- Product Surface
- Core User Flows
- Front-End Model
- Back-End Model
- Cross-Cutting Primitives
- Dev vs Prod Differences
- Operational Tooling
- Architectural Guardrails

### Dev Workflow & Guardrails (AGENTS.md)
- Start Here
- Architectural Guardrails
- Shell Ownership Model
- HTMX Response Contract
- Where New Code Goes
- Commands (Source of Truth)
- Dev vs Prod Quick Orientation
- Non-Goals

### Operations
- S3 Media Configuration (Production)
- Background/Wipe Media Pipeline
- Fly.io Deployment Checklist

### Feature Deep Dives
- HTMX SPA-like UX (parallax/wipes/intro)
- Guest checkout + CheckoutDraft persistence
- Stripe embedded checkout + webhook idempotency
- Session cart + idempotency keys
- Variant option system + conditional image resolution
- HTMX response utility layer
- Structured logging
- Dev/prod static parity
- Responsive background pipeline
- Seed/init command system
- Content-addressed Address model

<p align="right"><a href="#top">↑ Back to top</a></p>

---

<a id="architecture"></a>
## Architecture

Hella Webtilian is a server-rendered modular monolith composed of domain apps such as:

• hr_about  
• hr_access  
• hr_bulletin  
• hr_live  
• hr_payment  
• hr_shop  

The application behaves like a continuous interface while remaining rooted in Django’s view and template system.

Navigation model: server-routed pages with progressive HTMX enhancement  
UI structure: persistent shell defined in hr_common/templates/hr_common/base.html  
Interaction pattern: modal orchestration and fragment swapping through HTMX triggers

For full structural detail, see ARCHITECTURE.md.

<p align="right"><a href="#top">↑ Back to top</a></p>

---

<a id="deep-feature-details"></a>
## Deep Feature Details

<details>
<summary>HTMX-Driven SPA-Like Experience</summary>

A server-first architecture enhanced by parallax scrolling, section wipes, and intro animation sequencing. Layout reads and writes are batched through requestAnimationFrame and gated by IntersectionObserver for performance stability.

</details>

<details>
<summary>Guest Checkout + Persistent Draft State</summary>

Guest checkout uses signed tokens and CheckoutDraft persistence to maintain state across tab handoffs and email verification flows.

</details>

<details>
<summary>Stripe Embedded Checkout + Webhook Idempotency</summary>

Embedded Stripe UI with atomic session creation and webhook audit logging ensures safe handling of duplicate payment events.

</details>

<details>
<summary>Session Cart with Idempotency Keys</summary>

Session-backed cart operations include TTL-based idempotency keys to prevent double-add behavior without external infrastructure.

</details>

<details>
<summary>Dynamic Variant Option System</summary>

Product variants resolve through option-set equality rather than hardcoded dimension logic, with conditional image resolution driven by model metadata.

</details>

<details>
<summary>HTMX Response Utility Layer</summary>

Shared utilities centralize HX-Trigger and HX-Trigger-After-Settle handling to ensure consistent modal and message timing.

</details>

<details>
<summary>Structured Logging</summary>

Event-based structured logging using namespaced identifiers provides traceable operational insight across flows.

</details>

<details>
<summary>DevOps & Infrastructure Highlights</summary>

Dev/prod static parity, responsive background media pipelines, orchestration commands for seeding/reset, and a content-addressed Address model.

</details>

<p align="right"><a href="#top">↑ Back to top</a></p>
