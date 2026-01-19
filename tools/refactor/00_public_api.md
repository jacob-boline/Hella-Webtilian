# Public API & Modal Hooks Inventory (Baseline)

This report is a snapshot of CSS/HTML/JS hooks used for behavior/integration in the Django + HTMX SPA, with a focus on the modal system. It is intended as an auditable “do-not-rename without refactor” reference.

---

# 1) CSS Build Map

## Vite entrypoint(s)
- **Primary Rollup input:** `hr_core/static_src/js/main.js` configured as `main` in Vite’s build input map.【F:vite.config.js†L51-L59】
- **CSS entry loaded by JS:** `main.js` imports `../css/main.css` first, so `main.css` (and its imports) are the CSS load order on initial page load.【F:hr_core/static_src/js/main.js†L1-L16】

## CSS import/load order (from `main.css`)
1. `base/core.css`
2. `base/parallax.css`
3. `utilities/a11y.css`
4. `utilities/utilities.css`
5. `components/modal-ui.css`
6. `components/drawer.css`
7. `components/forms.css`
8. `components/buttons.css`
9. `sections/about.css`
10. `sections/banner.css`
11. `sections/bulletin.css`
12. `sections/merch.css`
13. `sections/shows.css`
14. `flows/auth.css`
15. `flows/cart.css`
16. `flows/checkout.css`
17. `flows/account.css`【F:hr_core/static_src/css/main.css†L1-L18】

---

# 2) Modal Inventory (partials that render into `#modal-content`)

## Shop / Merch
- Product detail modal partial: `hr_shop/templates/hr_shop/shop/_product_detail_modal.html` (uses modal UI and includes data-role hooks for variant updates).【F:hr_shop/templates/hr_shop/shop/_product_detail_modal.html†L1-L90】
- Cart modal: `hr_shop/templates/hr_shop/shop/_view_cart.html` (HTMX targets `#modal-content`).【F:hr_shop/templates/hr_shop/shop/_view_cart.html†L1-L78】

## Checkout flow (in-modal steps and state screens)
- Checkout details form: `hr_shop/templates/hr_shop/checkout/_checkout_details.html` (form swaps into `#modal-content`).【F:hr_shop/templates/hr_shop/checkout/_checkout_details.html†L1-L81】
- Checkout review: `hr_shop/templates/hr_shop/checkout/_checkout_review.html` (edit/review actions target `#modal-content`).【F:hr_shop/templates/hr_shop/checkout/_checkout_review.html†L1-L120】
- Checkout pay (Stripe embed): `hr_shop/templates/hr_shop/checkout/_checkout_pay.html` (contains `#checkout-pay-root` + `#embedded-checkout`).【F:hr_shop/templates/hr_shop/checkout/_checkout_pay.html†L1-L18】
- Awaiting email confirmation: `hr_shop/templates/hr_shop/checkout/_checkout_awaiting_confirmation.html` (polling updates `#modal-content`).【F:hr_shop/templates/hr_shop/checkout/_checkout_awaiting_confirmation.html†L1-L90】
- Session expired state: `hr_shop/templates/hr_shop/checkout/_checkout_session_expired.html` (actions swap into `#modal-content`).【F:hr_shop/templates/hr_shop/checkout/_checkout_session_expired.html†L1-L33】
- Email confirmation success state: `hr_shop/templates/hr_shop/checkout/_email_confirmation_success.html` (HTMX targets `#modal-content` + auto-advance).【F:hr_shop/templates/hr_shop/checkout/_email_confirmation_success.html†L1-L40】
- Order receipt modal: `hr_shop/templates/hr_shop/checkout/_order_receipt_modal.html` (post-order actions return to `#modal-content`).【F:hr_shop/templates/hr_shop/checkout/_order_receipt_modal.html†L1-L113】
- Order payment result: `hr_shop/templates/hr_shop/checkout/_order_payment_result.html` (post-purchase CTA swaps `#post-purchase-account`).【F:hr_shop/templates/hr_shop/checkout/_order_payment_result.html†L1-L218】

## Access / Account / Auth
- Account overview modal: `hr_access/templates/hr_access/account/_account_settings_modal.html`.【F:hr_access/templates/hr_access/account/_account_settings_modal.html†L1-L112】
- Change email form: `hr_access/templates/hr_access/account/_account_email_change_form.html`.【F:hr_access/templates/hr_access/account/_account_email_change_form.html†L1-L31】
- Change email “check your email” state: `hr_access/templates/hr_access/account/_account_email_change_check_email.html`.【F:hr_access/templates/hr_access/account/_account_email_change_check_email.html†L1-L24】
- Change email success: `hr_access/templates/hr_access/account/_account_email_change_success.html`.【F:hr_access/templates/hr_access/account/_account_email_change_success.html†L1-L19】
- Log out all sessions confirm: `hr_access/templates/hr_access/account/_logout_all_confirm.html`.【F:hr_access/templates/hr_access/account/_logout_all_confirm.html†L1-L27】
- Delete account confirm: `hr_access/templates/hr_access/account/_delete_account_confirm.html`.【F:hr_access/templates/hr_access/account/_delete_account_confirm.html†L1-L23】
- Password change form: `hr_access/templates/hr_access/registration/_password_change_form.html`.【F:hr_access/templates/hr_access/registration/_password_change_form.html†L1-L33】
- Password change done state: `hr_access/templates/hr_access/registration/_password_change_done.html`.【F:hr_access/templates/hr_access/registration/_password_change_done.html†L1-L18】
- Signup form: `hr_access/templates/hr_access/registration/_signup.html`.【F:hr_access/templates/hr_access/registration/_signup.html†L1-L33】
- Signup success: `hr_access/templates/hr_access/registration/_signup_success.html`.【F:hr_access/templates/hr_access/registration/_signup_success.html†L1-L23】
- Signup check email: `hr_access/templates/hr_access/registration/_signup_check_email.html`.【F:hr_access/templates/hr_access/registration/_signup_check_email.html†L1-L33】
- Password reset form: `hr_access/templates/hr_access/password_reset/_password_reset_form.html`.【F:hr_access/templates/hr_access/password_reset/_password_reset_form.html†L1-L41】
- Password reset confirm: `hr_access/templates/hr_access/password_reset/_password_reset_confirm.html`.【F:hr_access/templates/hr_access/password_reset/_password_reset_confirm.html†L1-L55】
- Password reset done: `hr_access/templates/hr_access/password_reset/_password_reset_done.html`.【F:hr_access/templates/hr_access/password_reset/_password_reset_done.html†L1-L42】
- Password reset complete: `hr_access/templates/hr_access/password_reset/_password_reset_complete.html`.【F:hr_access/templates/hr_access/password_reset/_password_reset_complete.html†L1-L26】
- Orders list modal: `hr_access/templates/hr_access/orders/_orders_modal.html`.【F:hr_access/templates/hr_access/orders/_orders_modal.html†L1-L71】
- Orders list (alt layout): `hr_access/templates/hr_access/orders/_orders_modal_body.html`.【F:hr_access/templates/hr_access/orders/_orders_modal_body.html†L1-L75】
- Order detail modal: `hr_access/templates/hr_access/orders/_order_detail_modal.html`.【F:hr_access/templates/hr_access/orders/_order_detail_modal.html†L1-L166】
- Unclaimed orders modal: `hr_access/templates/hr_access/orders/_unclaimed_orders_modal.html`.【F:hr_access/templates/hr_access/orders/_unclaimed_orders_modal.html†L1-L91】

## Post-purchase account flow (swapped in modal)
- Create account form: `hr_access/templates/hr_access/post_purchase/_post_purchase_account_form.html`.【F:hr_access/templates/hr_access/post_purchase/_post_purchase_account_form.html†L1-L40】
- Post-purchase success/claim flow: `hr_access/templates/hr_access/post_purchase/_post_purchase_account_success.html`.【F:hr_access/templates/hr_access/post_purchase/_post_purchase_account_success.html†L1-L60】
- Post-purchase already-signed-in: `hr_access/templates/hr_access/post_purchase/_post_purchase_account_done.html`.【F:hr_access/templates/hr_access/post_purchase/_post_purchase_account_done.html†L1-L13】

---

# 3) Public API List (selectors/hooks that are behavior/integration-critical)

## A) JavaScript hooks (selectors, classes, dataset keys)

### Modal + global UI
- `#modal`, `#modal-content`, `#modal-message-box`, `#modal-loader` (modal shell and loader references).【F:hr_core/static_src/js/modules/ui-global.js†L37-L39】【F:hr_core/static_src/js/modules/ui-global.js†L294-L325】
- `.modal-backdrop` and `[data-modal-close]` used to close modal via click delegation.【F:hr_core/static_src/js/modules/ui-global.js†L130-L137】
- `body.modal-open`, `.hidden`, `.is-swapping` toggled for modal open/close and swap state.【F:hr_core/static_src/js/modules/ui-global.js†L91-L112】【F:hr_core/static_src/js/modules/ui-global.js†L188-L196】
- `#global-message-bar`, `#global-message-content`, `.is-visible` used for global messages.【F:hr_core/static_src/js/modules/ui-global.js†L41-L66】
- `.floating-cart-btn`, `.is-hidden` used to show/hide floating cart button while modal is open.【F:hr_core/static_src/js/modules/ui-global.js†L44-L55】
- Post‑purchase CTA: `[data-cta-dismiss]`, `#post-purchase-account`, `.is-dismissing`, `data-cta-dismiss-bypass` dataset key (bypass flag).【F:hr_core/static_src/js/modules/ui-global.js†L204-L227】

### Auto-advance/HTMX automation (modal state transitions)
- `[data-hr-auto-advance]` and dataset keys: `data-delay-ms`, `data-next-url`, `data-target`, `data-swap`, `data-cancel-on`.【F:hr_core/static_src/js/modules/auto-advance.js†L33-L47】
- `#modal` + `.hidden` + `aria-hidden` used to prevent resurrecting closed modals in auto-advance logic.【F:hr_core/static_src/js/modules/auto-advance.js†L23-L26】【F:hr_core/static_src/js/modules/auto-advance.js†L74-L75】

### Checkout forms + Stripe embed
- `#checkout-details-form`, `#id_building_type`, `#id_unit`, `.field-group`, `.hidden` used for building type/unit field toggle.【F:hr_core/static_src/js/modules/checkout.js†L37-L70】
- `#checkout-pay-root`, `#embedded-checkout`, `[data-embedded-checkout]` and dataset keys `data-stripe-publishable-key`, `data-client-secret`, `data-session-endpoint` for embedded Stripe checkout init.【F:hr_core/static_src/js/modules/checkout.js†L96-L118】【F:hr_shop/templates/hr_shop/checkout/_checkout_pay.html†L1-L8】

### Product modal updates
- `.modal-product`, `.modal-image`, `[data-role="modal-price"]`, `[data-role="buy-selected-variant"]` used to update modal image/price and buy button target via HTMX events.【F:hr_core/static_src/js/modules/events.js†L233-L246】【F:hr_shop/templates/hr_shop/shop/_product_detail_modal.html†L6-L86】

### Cart/Sidebar integration
- `#floating-cart-count` badge updated via `updateCart` event.【F:hr_core/static_src/js/modules/events.js†L217-L223】
- `#sidebar-access` and optional `data-access-url` dataset key used to refresh the sidebar access panel on `accessChanged`.【F:hr_core/static_src/js/modules/events.js†L252-L270】

### Modal in merch flow (HTMX swap & view transition)
- `#modal`, `.merch-card`, `button.merch-img`, `.merch-actions .card-btn.btn-blue`, `.merch-thumb-img.is-active`, `.modal-image.is-active` for merch modal behavior and transition state.【F:hr_core/static_src/js/modules/merch.js†L9-L49】

### HTMX module re-init and modal targeting
- `#modal-content`, `#modal-message-box`, `#modal` are used to decide when to re-run modules after HTMX swaps and to apply a “settle” pass after modal swaps.【F:hr_core/static_src/js/meta-init.js†L64-L83】【F:hr_core/static_src/js/meta-init.js†L108-L118】

### Deep‑link / handoff integrations
- `#modal-loader` used by tab handoff logic to load modal content in another tab via HTMX (`hr:loadModal`).【F:hr_core/static_src/js/modules/tab-handoff.js†L44-L54】【F:hr_core/static_src/js/modules/tab-handoff.js†L71-L78】

## B) HTMX swap containers/targets

### Modal shell & loader
- `#modal` + `#modal-content` as primary modal swap target; modal loader uses `hx-trigger="hr:loadModal"` and targets `#modal-content`.【F:hr_common/templates/hr_common/base.html†L115-L131】
- `#modal-loader` configured for `hr:loadModal`, also set dynamically by JS for landing-modal bootstraps and handoffs.【F:hr_core/static_src/js/modules/ui-global.js†L294-L325】【F:hr_core/static_src/js/modules/tab-handoff.js†L44-L54】

### In-modal swap targets
- `#modal-content` is the consistent target for in-modal step transitions (example: checkout details/review/cart).【F:hr_shop/templates/hr_shop/shop/_view_cart.html†L39-L69】【F:hr_shop/templates/hr_shop/checkout/_checkout_review.html†L41-L117】
- `#post-purchase-account` swaps for post-purchase CTA (outerHTML swaps).【F:hr_shop/templates/hr_shop/checkout/_order_payment_result.html†L71-L96】

### Other HTMX containers used in modal-adjacent flows
- `#sidebar-access` is loaded via HTMX from base shell; login form targets this container for auth updates (sidebar flow).【F:hr_common/templates/hr_common/base.html†L83-L96】【F:hr_access/templates/hr_access/registration/_login.html†L10-L13】
- `#message-box-modal` used as an HTMX target for the reusable message box partial.【F:hr_common/templates/hr_common/display_message_box_modal.html†L14-L47】
- Legacy modal system (not `#modal-content`): `#modal` is an HTMX target in `hr_shop/_orders_modal.html` (older dialog-based modal).【F:hr_shop/templates/hr_shop/_orders_modal.html†L6-L29】

## C) Data attribute hooks (behavioral)

- `data-modal-close` (close modal buttons/backdrop).【F:hr_common/templates/hr_common/base.html†L116-L118】
- `data-cta-dismiss` (post-purchase CTA dismiss interception).【F:hr_shop/templates/hr_shop/checkout/_order_payment_result.html†L88-L96】【F:hr_core/static_src/js/modules/ui-global.js†L204-L227】
- `data-hr-auto-advance` + `data-delay-ms` + `data-next-url` + `data-target` + `data-swap` + `data-cancel-on` (auto-advance hook for modal step transitions).【F:hr_shop/templates/hr_shop/checkout/_email_confirmation_success.html†L32-L40】【F:hr_core/static_src/js/modules/auto-advance.js†L33-L47】
- `data-embedded-checkout`, `data-stripe-publishable-key`, `data-session-endpoint`, `data-client-secret` (Stripe embedded checkout mount + config).【F:hr_shop/templates/hr_shop/checkout/_checkout_pay.html†L3-L7】【F:hr_core/static_src/js/modules/checkout.js†L96-L118】
- `data-role="modal-price"` and `data-role="buy-selected-variant"` (variant preview updates in product modal).【F:hr_shop/templates/hr_shop/shop/_product_detail_modal.html†L66-L83】【F:hr_core/static_src/js/modules/events.js†L236-L238】

## D) ARIA + state semantics (interaction-critical)

- `#modal` uses `aria-hidden` toggled by JS for open/close state (must remain consistent with `.hidden` and `body.modal-open`).【F:hr_common/templates/hr_common/base.html†L115-L121】【F:hr_core/static_src/js/modules/ui-global.js†L91-L112】
- Legacy dialog modal uses `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `tabindex="-1"` (older modal pattern).【F:hr_shop/templates/hr_shop/_orders_modal.html†L3-L18】
- Live-region status used in checkout awaiting confirmation (`role="status"`, `aria-live="polite"`).【F:hr_shop/templates/hr_shop/checkout/_checkout_awaiting_confirmation.html†L88-L89】
- Live region in unclaimed orders modal (`aria-live`, `aria-atomic`, `role="status"`).【F:hr_access/templates/hr_access/orders/_unclaimed_orders_modal.html†L7-L9】

---

# 4) Risks / Notes (renaming hazards)

- **`#modal-content` is a critical integration point**: it is a primary HTMX swap target, referenced by JS (modal open/close and auto-advance), and tied to view-transition and layout styles. Renaming it requires updates in JS, templates, and CSS selectors (e.g., `#modal-content` view-transition and `:has()` rules).【F:hr_common/templates/hr_common/base.html†L115-L131】【F:hr_core/static_src/js/modules/ui-global.js†L37-L196】【F:hr_core/static_src/js/modules/auto-advance.js†L33-L75】【F:hr_core/static_src/css/base/core.css†L414-L457】
- **Modal state classes are behaviorally coupled** (`.hidden`, `.modal-open`, `.is-swapping`), and CSS uses them for visual/interaction behavior; changing these names without coordinated updates breaks modal state handling and transitions.【F:hr_core/static_src/js/modules/ui-global.js†L91-L112】【F:hr_core/static_src/js/modules/ui-global.js†L188-L196】【F:hr_core/static_src/css/base/core.css†L455-L462】
- **Post-purchase CTA flow depends on `#post-purchase-account` and `[data-cta-dismiss]`** for animation + HTMX swap flow; renaming requires synchronizing both templates and JS hooks.【F:hr_shop/templates/hr_shop/checkout/_order_payment_result.html†L71-L96】【F:hr_core/static_src/js/modules/ui-global.js†L204-L227】
- **Stripe Embedded Checkout depends on dataset keys** in `#checkout-pay-root` and the presence of `[data-embedded-checkout]` / `#embedded-checkout`. Renames or changes require updates in both template and JS module.【F:hr_shop/templates/hr_shop/checkout/_checkout_pay.html†L3-L8】【F:hr_core/static_src/js/modules/checkout.js†L96-L118】
- **CSS `:has()` selectors target modal content class names** (e.g., `.unclaimed-orders-modal`, `.checkout-review-modal`); renaming those classes requires CSS updates to keep modal layout behavior consistent.【F:hr_core/static_src/css/flows/account.css†L663-L705】【F:hr_core/static_src/css/flows/checkout.css†L8-L13】
