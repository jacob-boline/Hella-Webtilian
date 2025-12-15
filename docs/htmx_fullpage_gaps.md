# Full-page Responses to Eliminate (HTMX-only plan)

The views below still branch to full-page templates or redirects. To make the app HTMX-only, trim these non-HTMX paths so they return partials/fragments consistently.

## hr_access/views.py
- `signup` renders full-page registration templates and redirects to `hr_access:orders` on success when the request is not HTMX; switch to partial-only flows and HTMX triggers instead of redirects/messages.【F:hr_access/views.py†L43-L103】
- `user_login` uses full-page login templates and a redirect to `hr_site:index` when not HTMX; drop the non-HTMX render/redirect in favor of the sidebar partial/trigger path only.【F:hr_access/views.py†L112-L167】
- `login_success` chooses between `_login_success.html` and `login_success.html`; remove the full-page fallback template.【F:hr_access/views.py†L169-L174】
- The account orders endpoints (`orders`, `orders_page`, `order_detail_modal`) still serve full-page templates under `/account/...`; convert them to modal/partial-only responses so account order views rely solely on HTMX injections.【F:hr_shop/views/orders.py†L9-L43】

## hr_shop/views/cart.py
- `view_cart` returns `hr_shop/view_cart.html` for non-HTMX requests while HTMX gets `_view_cart.html`; remove the full-page branch and make cart views respond with partials only (the POST helpers reuse this view).【F:hr_shop/views/cart.py†L95-L124】

## hr_shop/views/checkout.py
- `_render_checkout_review` toggles between `_checkout_review.html` and `checkout_review.html`; drop the full-page template selection.【F:hr_shop/views/checkout.py†L188-L207】
- `checkout_details` and `checkout_details_submit` render `checkout_details.html` for non-HTMX requests and redirect users through multi-step full pages; collapse these to HTMX fragment responses only (including error paths).【F:hr_shop/views/checkout.py†L308-L370】
- `checkout_details_submit` also renders `checkout_awaiting_confirmation.html` on the non-HTMX path when emails are rate limited or pending; replace with partial-only handling.【F:hr_shop/views/checkout.py†L358-L379】
- `checkout_review_submit` clears carts and redirects to provider URLs for non-HTMX callers; align it with HTMX-only triggers instead of redirects/messages.【F:hr_shop/views/checkout.py†L639-L661】
- `order_thank_you` renders `order_thank_you.html` for non-HTMX requests; adjust to only emit the modal/fragment response used by HTMX flows.【F:hr_shop/views/checkout.py†L663-L673】
