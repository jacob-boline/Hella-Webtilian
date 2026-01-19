# CSS Selector Specificity & Maintainability Audit

Scope: project-authored CSS imported by `hr_core/static_src/css/main.css` (Vite build).

---

## 1) Specificity hot spots (Top 30)
- `.change-password-modal #password-change-form input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"])` — specificity 1,17,1 (score 271) — hr_core/static_src/css/flows/account.css:38
- `#modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"])` — specificity 1,16,1 (score 261) — hr_core/static_src/css/base/core.css:360
- `#modal:has(#modal-content .checkout-review-modal:not(.order-payment-result)) .modal-panel` — specificity 2,4,2 (score 242) — hr_core/static_src/css/flows/checkout.css:7
- `#modal:has(#modal-content .change-password-modal) .modal-panel` — specificity 2,3,2 (score 232) — hr_core/static_src/css/flows/account.css:8
- `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"])` — specificity 0,17,1 (score 171) — hr_core/static_src/css/components/modal-ui.css:244
- `.checkout-details-form input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"])` — specificity 0,17,1 (score 171) — hr_core/static_src/css/flows/checkout.css:76
- `#modal-content:has(.unclaimed-orders-modal) .unclaimed-orders-modal .order-claim-list` — specificity 1,4,0 (score 140) — hr_core/static_src/css/flows/account.css:657
- `#modal-content:has(.unclaimed-orders-modal) .unclaimed-orders-modal .modal-actions` — specificity 1,4,0 (score 140) — hr_core/static_src/css/flows/account.css:669
- `#modal-content:has(.unclaimed-orders-modal) .unclaimed-orders-modal form` — specificity 1,3,1 (score 131) — hr_core/static_src/css/flows/account.css:648
- `#parallax-section-about .about-quote-rotator .quote-text.is-visible` — specificity 1,3,0 (score 130) — hr_core/static_src/css/sections/about.css:457
- `#modal:not(.hidden) .modal-panel` — specificity 1,3,0 (score 130) — hr_core/static_src/css/sections/merch.css:487
- `.change-password-modal #password-change-form .m-actions > .card-btn` — specificity 1,3,0 (score 130) — hr_core/static_src/css/flows/account.css:55
- `#modal-content:has(.unclaimed-orders-modal) .unclaimed-orders-modal` — specificity 1,3,0 (score 130) — hr_core/static_src/css/flows/account.css:648
- `#modal-content:has(.unclaimed-orders-modal) .unclaimed-orders-layout` — specificity 1,3,0 (score 130) — hr_core/static_src/css/flows/account.css:648
- `#parallax-section-about .about-intro p::after` — specificity 1,2,2 (score 122) — hr_core/static_src/css/sections/about.css:70
- `.modal.is-swapping #modal-content` — specificity 1,2,0 (score 120) — hr_core/static_src/css/base/core.css:439
- `#about-carousel.quote-overlay .about-quote` — specificity 1,2,0 (score 120) — hr_core/static_src/css/sections/about.css:193
- `#parallax-section-about .about-quote-rotator .quote-text` — specificity 1,2,0 (score 120) — hr_core/static_src/css/sections/about.css:422
- `#parallax-section-about .about-quote-rotator .quote-text` — specificity 1,2,0 (score 120) — hr_core/static_src/css/sections/about.css:446
- `#parallax-section-about .about-quote-rotator .quote-source` — specificity 1,2,0 (score 120) — hr_core/static_src/css/sections/about.css:446
- `#banner .row .banner-row` — specificity 1,2,0 (score 120) — hr_core/static_src/css/sections/banner.css:22
- `.change-password-modal #password-change-form.m-body` — specificity 1,2,0 (score 120) — hr_core/static_src/css/flows/account.css:25
- `.change-password-modal #password-change-form > .field-row--neutral` — specificity 1,2,0 (score 120) — hr_core/static_src/css/flows/account.css:30
- `.change-password-modal #password-change-form > .field-row--error` — specificity 1,2,0 (score 120) — hr_core/static_src/css/flows/account.css:30
- `.change-password-modal #password-change-form > .field-row--valid` — specificity 1,2,0 (score 120) — hr_core/static_src/css/flows/account.css:30
- `.change-password-modal #password-change-form .m-actions` — specificity 1,2,0 (score 120) — hr_core/static_src/css/flows/account.css:45
- `#modal-content:has(.unclaimed-orders-modal)` — specificity 1,2,0 (score 120) — hr_core/static_src/css/flows/account.css:641
- `#password-change-form .field-row:first-of-type` — specificity 1,2,0 (score 120) — hr_core/static_src/css/flows/account.css:731
- `#parallax-section-about .about-intro p` — specificity 1,1,1 (score 111) — hr_core/static_src/css/sections/about.css:56
- `.change-password-modal #password-change-form select` — specificity 1,1,1 (score 111) — hr_core/static_src/css/flows/account.css:38

## 2) Nesting depth and fragility
### Deepest selectors (by combinators)
- `@container modal (min-width: 420px) and (max-width: 599.98px)` — combinators: 6 — hr_core/static_src/css/components/modal-ui.css:108
- `@container modal (min-width: 420px) and (max-width: 599.98px)` — combinators: 6 — hr_core/static_src/css/sections/merch.css:328
- `@container modal (min-width: 768px) and (max-width: 1099.98px)` — combinators: 6 — hr_core/static_src/css/sections/merch.css:355
- `@container modal (min-width: 840px) and (max-width: 1099.98px)` — combinators: 6 — hr_core/static_src/css/sections/merch.css:380
- `@media (min-width: 720px) and (max-width: 1023.98px)` — combinators: 5 — hr_core/static_src/css/sections/shows.css:915
- `.order-payment-result .order-details > :not(summary) *` — combinators: 5 — hr_core/static_src/css/flows/checkout.css:593
- `.account-status-layout .account-status-panel:first-of-type .account-status-panel-text > p.modal-kicker` — combinators: 5 — hr_core/static_src/css/flows/checkout.css:756
- `.account-status-layout section.account-status-panel:nth-of-type(2) .account-status-panel-text > p.modal-kicker` — combinators: 5 — hr_core/static_src/css/flows/checkout.css:760
- `.change-password-modal #password-change-form .m-actions > .card-btn` — combinators: 5 — hr_core/static_src/css/flows/account.css:55
- `@media (min-width: 768px) and (max-width: 1199.98px)` — combinators: 5 — hr_core/static_src/css/flows/account.css:788
- `.checkout-review-modal .review-section.shipping-review + .review-section` — combinators: 4 — hr_core/static_src/css/flows/checkout.css:259
- `.checkout-review-modal .review-actions > .card-btn` — combinators: 4 — hr_core/static_src/css/flows/checkout.css:420
- `.checkout-review-modal .review-actions > .card-btn` — combinators: 4 — hr_core/static_src/css/flows/checkout.css:428
- `.order-payment-result .order-details > :not(summary)` — combinators: 4 — hr_core/static_src/css/flows/checkout.css:593
- `.order-payment-result .order-details > summary` — combinators: 4 — hr_core/static_src/css/flows/checkout.css:618
- `.order-payment-result details[open] > summary.order-details-toggle::after` — combinators: 4 — hr_core/static_src/css/flows/checkout.css:701
- `.change-password-modal #password-change-form > .field-row--neutral` — combinators: 4 — hr_core/static_src/css/flows/account.css:30
- `.change-password-modal #password-change-form > .field-row--error` — combinators: 4 — hr_core/static_src/css/flows/account.css:30
- `.change-password-modal #password-change-form > .field-row--valid` — combinators: 4 — hr_core/static_src/css/flows/account.css:30
- `.m-shell > *` — combinators: 3 — hr_core/static_src/css/components/modal-ui.css:20
- `.m-actions > *` — combinators: 3 — hr_core/static_src/css/components/modal-ui.css:89
- `@container modal (max-width: 419.98px)` — combinators: 3 — hr_core/static_src/css/components/modal-ui.css:102
- `@container modal (min-width: 600px)` — combinators: 3 — hr_core/static_src/css/components/modal-ui.css:114
- `@container modal (min-width: 840px)` — combinators: 3 — hr_core/static_src/css/components/modal-ui.css:120
- `@container modal (min-width: 1100px)` — combinators: 3 — hr_core/static_src/css/components/modal-ui.css:137
- `@container modal (min-width: 600px)` — combinators: 3 — hr_core/static_src/css/components/modal-ui.css:231
- `@container modal (max-width: 599.98px)` — combinators: 3 — hr_core/static_src/css/components/modal-ui.css:365
- `#sidebar-access > *` — combinators: 3 — hr_core/static_src/css/components/drawer.css:28
- `.inline.uniform > *` — combinators: 3 — hr_core/static_src/css/components/buttons.css:55
- `.about-thumbs-wrap > button` — combinators: 3 — hr_core/static_src/css/sections/about.css:264

### Structure-dependent selectors (DOM-fragile)
- `@container modal (min-width: 420px) and (max-width: 599.98px)` — hr_core/static_src/css/components/modal-ui.css:108
- `@container modal (min-width: 420px) and (max-width: 599.98px)` — hr_core/static_src/css/sections/merch.css:328
- `@container modal (min-width: 768px) and (max-width: 1099.98px)` — hr_core/static_src/css/sections/merch.css:355
- `@container modal (min-width: 840px) and (max-width: 1099.98px)` — hr_core/static_src/css/sections/merch.css:380
- `@media (min-width: 720px) and (max-width: 1023.98px)` — hr_core/static_src/css/sections/shows.css:915
- `.order-payment-result .order-details > :not(summary) *` — hr_core/static_src/css/flows/checkout.css:593
- `.account-status-layout .account-status-panel:first-of-type .account-status-panel-text > p.modal-kicker` — hr_core/static_src/css/flows/checkout.css:756
- `.account-status-layout section.account-status-panel:nth-of-type(2) .account-status-panel-text > p.modal-kicker` — hr_core/static_src/css/flows/checkout.css:760
- `.change-password-modal #password-change-form .m-actions > .card-btn` — hr_core/static_src/css/flows/account.css:55
- `@media (min-width: 768px) and (max-width: 1199.98px)` — hr_core/static_src/css/flows/account.css:788
- `.checkout-review-modal .review-section.shipping-review + .review-section` — hr_core/static_src/css/flows/checkout.css:259
- `.checkout-review-modal .review-actions > .card-btn` — hr_core/static_src/css/flows/checkout.css:420
- `.checkout-review-modal .review-actions > .card-btn` — hr_core/static_src/css/flows/checkout.css:428
- `.order-payment-result .order-details > :not(summary)` — hr_core/static_src/css/flows/checkout.css:593
- `.order-payment-result .order-details > summary` — hr_core/static_src/css/flows/checkout.css:618
- `.order-payment-result details[open] > summary.order-details-toggle::after` — hr_core/static_src/css/flows/checkout.css:701
- `.change-password-modal #password-change-form > .field-row--neutral` — hr_core/static_src/css/flows/account.css:30
- `.change-password-modal #password-change-form > .field-row--error` — hr_core/static_src/css/flows/account.css:30
- `.change-password-modal #password-change-form > .field-row--valid` — hr_core/static_src/css/flows/account.css:30

## 3) Global element styling risks
### `a`
- hr_core/static_src/css/sections/bulletin.css:109 — `.bulletin-title a` sets color, text-decoration
- hr_core/static_src/css/sections/bulletin.css:114 — `.bulletin-title a:hover` sets text-shadow
### `article`
- hr_core/static_src/css/components/drawer.css:448 — `article button` sets width
### `body`
- hr_core/static_src/css/base/core.css:201 — `html,
body,
.section-wipe,
.parallax-section` sets overflow-anchor
- hr_core/static_src/css/base/core.css:208 — `html.modal-open,
body.modal-open` sets overflow
- hr_core/static_src/css/base/core.css:213 — `body` sets background-color, color, font-family
- hr_core/static_src/css/base/core.css:219 — `body.modal-open` sets left, position, right, width
### `button`
- hr_core/static_src/css/components/drawer.css:448 — `article button` sets width
- hr_core/static_src/css/sections/about.css:211 — `.about-gallery figure.about-stage button.about-nav` sets background, border, border-radius, color, cursor, display, font-size, height, line-height, place-items, position, top, transform, transition, width, z-index
- hr_core/static_src/css/sections/about.css:231 — `.about-gallery figure.about-stage button.about-nav:hover` sets background, transform
- hr_core/static_src/css/sections/about.css:258 — `.about-thumbs-wrap button.thumbs-prev:hover,
.about-thumbs-wrap button.thumbs-next:hover` sets background, transform
- hr_core/static_src/css/sections/about.css:264 — `.about-thumbs-wrap > button` sets background, border, border-radius, color, cursor, display, height, place-items, transition, width
- ... and 5 more
### `details`
- hr_core/static_src/css/flows/checkout.css:701 — `.order-payment-result details[open] > summary.order-details-toggle::after` sets transform
### `div`
- hr_core/static_src/css/base/parallax.css:30 — `div.parallax-content p` sets color, position, z-index
- hr_core/static_src/css/components/drawer.css:368 — `form.login-form div.form-control` sets margin
### `figure`
- hr_core/static_src/css/sections/about.css:211 — `.about-gallery figure.about-stage button.about-nav` sets background, border, border-radius, color, cursor, display, font-size, height, line-height, place-items, position, top, transform, transition, width, z-index
- hr_core/static_src/css/sections/about.css:231 — `.about-gallery figure.about-stage button.about-nav:hover` sets background, transform
### `form`
- hr_core/static_src/css/components/drawer.css:368 — `form.login-form div.form-control` sets margin
- hr_core/static_src/css/flows/checkout.css:407 — `.checkout-review-modal .review-actions form` sets display
- hr_core/static_src/css/flows/account.css:583 — `.unclaimed-orders-modal form` sets display, flex, flex-direction, min-height
- hr_core/static_src/css/flows/account.css:648 — `#modal-content:has(.unclaimed-orders-modal) .unclaimed-orders-modal,
#modal-content:has(.unclaimed-orders-modal) .unclaimed-orders-layout,
#modal-content:has(.unclaimed-orders-modal) .unclaimed-orders-modal form` sets display, flex, flex-direction, min-height
### `h1`
- hr_core/static_src/css/base/core.css:312 — `.parallax-section h1` sets animation, color, font-family, font-size, font-weight, letter-spacing, line-height, margin, text-align, text-shadow, text-transform
### `h2`
- hr_core/static_src/css/components/modal-ui.css:388 — `.modal h2.sub-header.modal-title:hover` sets color, text-shadow
- hr_core/static_src/css/components/drawer.css:24 — `#sidebar-access h2` sets margin-bottom
### `hr`
- hr_core/static_src/css/components/drawer.css:107 — `.user-panel hr` sets border-color, margin-bottom, margin-top, width
### `html`
- hr_core/static_src/css/base/core.css:197 — `html` sets scrollbar-gutter
- hr_core/static_src/css/base/core.css:201 — `html,
body,
.section-wipe,
.parallax-section` sets overflow-anchor
- hr_core/static_src/css/base/core.css:208 — `html.modal-open,
body.modal-open` sets overflow
### `i`
- hr_core/static_src/css/sections/shows.css:851 — `.date-panel .directions-btn--inline i` sets font-size, margin-right
### `iframe`
- hr_core/static_src/css/components/drawer.css:89 — `#drawer-navigation iframe` sets align-self, background-color, border, border-radius, box-shadow, display, flex, height, margin, margin-inline, max-width, width
### `img`
- hr_core/static_src/css/sections/about.css:315 — `.about-thumbs button img` sets height, object-fit, object-position, width
- hr_core/static_src/css/sections/bulletin.css:60 — `.bulletin-hero img` sets display, filter, height, object-fit, transform, transition, width
- hr_core/static_src/css/sections/bulletin.css:72 — `.bulletin-post:hover .bulletin-hero img` sets filter, transform
- hr_core/static_src/css/sections/merch.css:49 — `.merch-img img` sets height, object-fit, transition, width
- hr_core/static_src/css/sections/merch.css:56 — `.merch-img:hover img` sets transform
### `input`
- hr_core/static_src/css/base/core.css:360 — `#modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
#modal select,
#modal textarea` sets font-size
- hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` sets background-color, border, border-radius, color, font-family, font-size, outline, padding, transition, width
- hr_core/static_src/css/components/modal-ui.css:261 — `.modal input:not([type="checkbox"]):not([type="radio"]):focus,
.modal select:focus,
.modal textarea:focus` sets background-color, border-color, box-shadow
- hr_core/static_src/css/components/modal-ui.css:269 — `.modal input.control-compact,
.modal select.control-compact,
.modal textarea.control-compact` sets border-radius, font-size, padding, width
- hr_core/static_src/css/components/drawer.css:324 — `.form-control input[type="text"],
.form-control input[type="password"]` sets background-color, color, height, margin, width
- ... and 9 more
### `label`
- hr_core/static_src/css/components/drawer.css:364 — `.field-group:focus-within label` sets color
- hr_core/static_src/css/sections/merch.css:244 — `.modal-variant-group label` sets color, font-family, font-size, letter-spacing, text-transform
- hr_core/static_src/css/flows/cart.css:77 — `.item-quantity label` sets opacity
- hr_core/static_src/css/flows/checkout.css:138 — `.checkout-details-modal label` sets align-items, color, display, font-size, gap, letter-spacing, line-height, margin-bottom, margin-top, text-transform
### `li`
- hr_core/static_src/css/components/modal-ui.css:324 — `.modal-helpbox li` sets margin-bottom
- hr_core/static_src/css/sections/about.css:290 — `.about-thumbs li` sets display
- hr_core/static_src/css/sections/about.css:294 — `.about-thumbs li.is-visible` sets display
- hr_core/static_src/css/flows/auth.css:100 — `.auth-modal .modal-helpbox li,
.auth-state-success .modal-helpbox li` sets margin-bottom
### `nav`
- hr_core/static_src/css/base/core.css:228 — `nav.navbar` sets position
### `p`
- hr_core/static_src/css/base/parallax.css:30 — `div.parallax-content p` sets color, position, z-index
- hr_core/static_src/css/components/modal-ui.css:290 — `.modal .form-errors p` sets margin
- hr_core/static_src/css/sections/about.css:40 — `.about-card,
.about-card p,
.about-card .about-quote` sets color, text-align, text-shadow
- hr_core/static_src/css/sections/about.css:56 — `#parallax-section-about .about-intro p` sets font-family, font-size, font-weight, letter-spacing, line-height, margin, max-width, opacity, padding-bottom, position
- hr_core/static_src/css/sections/about.css:70 — `#parallax-section-about .about-intro p::after` sets background, bottom, box-shadow, content, height, left, opacity, position, transform, width
- ... and 7 more
### `section`
- hr_core/static_src/css/flows/checkout.css:760 — `.account-status-layout section.account-status-panel:nth-of-type(2) .account-status-panel-text > p.modal-kicker` sets color
### `select`
- hr_core/static_src/css/base/core.css:360 — `#modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
#modal select,
#modal textarea` sets font-size
- hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` sets background-color, border, border-radius, color, font-family, font-size, outline, padding, transition, width
- hr_core/static_src/css/components/modal-ui.css:261 — `.modal input:not([type="checkbox"]):not([type="radio"]):focus,
.modal select:focus,
.modal textarea:focus` sets background-color, border-color, box-shadow
- hr_core/static_src/css/components/modal-ui.css:269 — `.modal input.control-compact,
.modal select.control-compact,
.modal textarea.control-compact` sets border-radius, font-size, padding, width
- hr_core/static_src/css/flows/checkout.css:76 — `.checkout-details-form input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.checkout-details-form select,
.checkout-details-form textarea` sets font-size
- ... and 1 more
### `span`
- hr_core/static_src/css/sections/banner.css:39 — `.banner-row > span` sets color, display, font-family, font-size, opacity, transition
- hr_core/static_src/css/sections/banner.css:49 — `.banner-row > span.blink,
.banner-row > span.is-visible` sets opacity
- hr_core/static_src/css/sections/banner.css:55 — `.banner-row > span.burn` sets animation
- hr_core/static_src/css/sections/banner.css:59 — `.banner-row > span:hover` sets color, text-shadow, transition
- hr_core/static_src/css/sections/banner.css:66 — `.banner-row > span.is-fading` sets opacity, transition
- ... and 2 more
### `strong`
- hr_core/static_src/css/flows/checkout.css:59 — `.checkout-awaiting-confirmation .email-sent-to strong` sets color
### `summary`
- hr_core/static_src/css/components/modal-ui.css:305 — `.modal-helpbox summary` sets color, cursor, font-size, font-weight
- hr_core/static_src/css/components/modal-ui.css:312 — `.modal-helpbox summary:hover` sets text-decoration
- hr_core/static_src/css/flows/auth.css:78 — `.auth-modal .modal-helpbox summary,
.auth-state-success .modal-helpbox summary` sets color, cursor, font-size, font-weight
- hr_core/static_src/css/flows/auth.css:86 — `.auth-modal .modal-helpbox summary:hover,
.auth-state-success .modal-helpbox summary:hover` sets text-decoration
- hr_core/static_src/css/flows/checkout.css:618 — `.order-payment-result .order-details > summary` sets text-align
- ... and 4 more
### `table`
- hr_core/static_src/css/components/modal-ui.css:98 — `.m-tablewrap table` sets min-width
### `textarea`
- hr_core/static_src/css/base/core.css:360 — `#modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
#modal select,
#modal textarea` sets font-size
- hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` sets background-color, border, border-radius, color, font-family, font-size, outline, padding, transition, width
- hr_core/static_src/css/components/modal-ui.css:261 — `.modal input:not([type="checkbox"]):not([type="radio"]):focus,
.modal select:focus,
.modal textarea:focus` sets background-color, border-color, box-shadow
- hr_core/static_src/css/components/modal-ui.css:269 — `.modal input.control-compact,
.modal select.control-compact,
.modal textarea.control-compact` sets border-radius, font-size, padding, width
- hr_core/static_src/css/components/forms.css:69 — `textarea.form-control` sets min-height, resize
- ... and 3 more
### `time`
- hr_core/static_src/css/sections/bulletin.css:131 — `.bulletin-meta time` sets white-space
### `ul`
- hr_core/static_src/css/components/modal-ui.css:316 — `.modal-helpbox ul` sets color, font-size, line-height, margin, padding-left
- hr_core/static_src/css/flows/auth.css:91 — `.auth-modal .modal-helpbox ul,
.auth-state-success .modal-helpbox ul` sets color, font-size, line-height, margin, padding-left
- hr_core/static_src/css/flows/auth.css:132 — `.auth-modal .password-requirements ul` sets margin, padding-left

## 4) !important usage
- Total `!important` count: **11**
- hr_core/static_src/css/base/parallax.css:30 — `div.parallax-content p` → `position: relative !important`
- hr_core/static_src/css/base/parallax.css:30 — `div.parallax-content p` → `z-index: 10 !important`
- hr_core/static_src/css/base/parallax.css:30 — `div.parallax-content p` → `color: var(--text) !important`
- hr_core/static_src/css/base/parallax.css:106 — `@media (prefers-reduced-motion: reduce)` → `.parallax-background,
    .section-wipe {
        transform: none !important`
- hr_core/static_src/css/base/parallax.css:106 — `@media (prefers-reduced-motion: reduce)` → `transition: none !important`
- hr_core/static_src/css/base/parallax.css:106 — `@media (prefers-reduced-motion: reduce)` → `animation: none !important`
- hr_core/static_src/css/components/drawer.css:333 — `input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus` → `-webkit-text-fill-color: var(--neon-blue) !important`
- hr_core/static_src/css/components/drawer.css:333 — `input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus` → `caret-color: var(--neon-blue) !important`
- hr_core/static_src/css/components/drawer.css:333 — `input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus` → `-webkit-box-shadow: 0 0 0 1000px black inset !important`
- hr_core/static_src/css/components/drawer.css:333 — `input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus` → `box-shadow: 0 0 0 1000px black inset !important`
- hr_core/static_src/css/flows/account.css:255 — `@media (max-width: 1199.98px)` → `}

    .account-status-grid .review-section .shipping-address.customer-field {
        white-space: normal !important`

**Likely purposes:** force overrides in components with shared base styles (e.g., modal/buttons) and ensure utilities win. These are candidates for refactor into layered component scopes or stronger base selectors.

## 5) Override chains ("who wins" map)
### modal
- **overflow**
  - hr_core/static_src/css/base/core.css:208 — `html.modal-open,
body.modal-open` → `hidden`
  - hr_core/static_src/css/base/core.css:382 — `.modal-panel` → `hidden`
  - hr_core/static_src/css/base/core.css:398 — `#modal-content` → `auto`
  - hr_core/static_src/css/components/modal-ui.css:30 — `.m-body,
.modal-scroll` → `auto`
  - hr_core/static_src/css/flows/account.css:641 — `#modal-content:has(.unclaimed-orders-modal)` → `hidden`
- **width**
  - hr_core/static_src/css/base/core.css:219 — `body.modal-open` → `100%`
  - hr_core/static_src/css/base/core.css:398 — `#modal-content` → `100%`
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `100%`
  - hr_core/static_src/css/components/modal-ui.css:269 — `.modal input.control-compact,
.modal select.control-compact,
.modal textarea.control-compact` → `64px`
  - hr_core/static_src/css/sections/merch.css:144 — `.merch-modal .modal-image` → `100%`
  - hr_core/static_src/css/sections/merch.css:186 — `.modal-product .modal-image` → `100%`
  - ... and 2 more
- **position**
  - hr_core/static_src/css/base/core.css:219 — `body.modal-open` → `fixed`
  - hr_core/static_src/css/base/core.css:346 — `.modal` → `fixed`
  - hr_core/static_src/css/base/core.css:366 — `.modal-backdrop` → `absolute`
  - hr_core/static_src/css/base/core.css:382 — `.modal-panel` → `relative`
  - hr_core/static_src/css/base/core.css:448 — `.modal-close-btn` → `sticky`
  - hr_core/static_src/css/components/modal-ui.css:330 — `.modal-summary-row` → `relative`
  - ... and 2 more
- **font-family**
  - hr_core/static_src/css/base/core.css:346 — `.modal` → `Quantico, sans-serif`
  - hr_core/static_src/css/components/modal-ui.css:147 — `.modal-title` → `"Megrim", cursive`
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `inherit`
  - hr_core/static_src/css/sections/merch.css:76 — `.merch-title,
.modal-title,
.product-modal-price` → `"Megrim", cursive`
  - hr_core/static_src/css/sections/merch.css:229 — `.modal-product .modal-description` → `"Exo 2", sans-serif`
  - hr_core/static_src/css/sections/merch.css:244 — `.modal-variant-group label` → `"Quantico", sans-serif`
- **z-index**
  - hr_core/static_src/css/base/core.css:346 — `.modal` → `1600`
  - hr_core/static_src/css/base/core.css:382 — `.modal-panel` → `1001`
  - hr_core/static_src/css/flows/account.css:669 — `#modal-content:has(.unclaimed-orders-modal) .unclaimed-orders-modal .modal-actions` → `3`
- **font-size**
  - hr_core/static_src/css/base/core.css:346 — `.modal` → `0.75rem`
  - hr_core/static_src/css/base/core.css:360 — `#modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
#modal select,
#modal textarea` → `0.75rem`
  - hr_core/static_src/css/base/core.css:448 — `.modal-close-btn` → `1.75rem`
  - hr_core/static_src/css/components/modal-ui.css:10 — `.m-shell,
.modal-content` → `var(--m-text)`
  - hr_core/static_src/css/components/modal-ui.css:147 — `.modal-title` → `var(--m-title)`
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `0.75rem`
  - ... and 12 more
- **display**
  - hr_core/static_src/css/base/core.css:346 — `.modal` → `flex`
  - hr_core/static_src/css/base/core.css:382 — `.modal-panel` → `flex`
  - hr_core/static_src/css/base/core.css:398 — `#modal-content` → `flex`
  - hr_core/static_src/css/base/core.css:443 — `.modal.hidden` → `none`
  - hr_core/static_src/css/components/modal-ui.css:10 — `.m-shell,
.modal-content` → `flex`
  - hr_core/static_src/css/components/modal-ui.css:189 — `.modal-actions` → `flex`
  - ... and 14 more
- **align-items**
  - hr_core/static_src/css/base/core.css:346 — `.modal` → `center`
  - hr_core/static_src/css/components/modal-ui.css:202 — `.modal-actions.stack` → `stretch`
  - hr_core/static_src/css/components/modal-ui.css:330 — `.modal-summary-row` → `baseline`
  - hr_core/static_src/css/components/modal-ui.css:348 — `.modal-summary-block` → `baseline`
  - hr_core/static_src/css/sections/merch.css:175 — `.modal-product-media` → `center`
- **justify-content**
  - hr_core/static_src/css/base/core.css:346 — `.modal` → `center`
  - hr_core/static_src/css/components/modal-ui.css:189 — `.modal-actions` → `center`
  - hr_core/static_src/css/sections/merch.css:175 — `.modal-product-media` → `center`
- **padding**
  - hr_core/static_src/css/base/core.css:346 — `.modal` → `calc(var(--modal-gutter) + env(safe-area-inset-top, 0px)) var(--modal-gutter) calc(var(--modal-gutter) + env(safe-area-inset-bottom, 0px))`
  - hr_core/static_src/css/base/core.css:382 — `.modal-panel` → `var(--m-pad)`
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `0.25rem`
  - hr_core/static_src/css/components/modal-ui.css:269 — `.modal input.control-compact,
.modal select.control-compact,
.modal textarea.control-compact` → `0.15rem 0.4rem`
  - hr_core/static_src/css/components/modal-ui.css:280 — `.modal .form-errors` → `0.75rem 1rem`
  - hr_core/static_src/css/components/modal-ui.css:296 — `.modal-helpbox` → `1.5rem`
  - ... and 4 more
### button
- **font-size**
  - hr_core/static_src/css/base/core.css:360 — `#modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
#modal select,
#modal textarea` → `0.75rem`
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `0.75rem`
  - hr_core/static_src/css/components/buttons.css:37 — `.card-btn` → `0.7rem`
  - hr_core/static_src/css/components/buttons.css:63 — `.btn-neon` → `0.7rem`
  - hr_core/static_src/css/components/buttons.css:155 — `.btn-sm` → `0.62rem`
  - hr_core/static_src/css/sections/about.css:211 — `.about-gallery figure.about-stage button.about-nav` → `1.5rem`
  - ... and 1 more
- **width**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `100%`
  - hr_core/static_src/css/components/drawer.css:448 — `article button` → `100%`
  - hr_core/static_src/css/sections/about.css:211 — `.about-gallery figure.about-stage button.about-nav` → `3rem`
  - hr_core/static_src/css/sections/about.css:264 — `.about-thumbs-wrap > button` → `2rem`
  - hr_core/static_src/css/sections/about.css:298 — `.about-thumbs button` → `100%`
  - hr_core/static_src/css/sections/about.css:315 — `.about-thumbs button img` → `100%`
  - ... and 4 more
- **padding**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `0.25rem`
  - hr_core/static_src/css/components/buttons.css:37 — `.card-btn` → `0.45rem 0.7rem`
  - hr_core/static_src/css/components/buttons.css:63 — `.btn-neon` → `0.5rem 1rem`
  - hr_core/static_src/css/components/buttons.css:155 — `.btn-sm` → `0.35rem 0.7rem`
  - hr_core/static_src/css/sections/about.css:298 — `.about-thumbs button` → `0`
- **border-radius**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `8px`
  - hr_core/static_src/css/components/buttons.css:63 — `.btn-neon` → `0.75rem`
  - hr_core/static_src/css/components/buttons.css:105 — `.btn-neon::after` → `inherit`
  - hr_core/static_src/css/components/buttons.css:155 — `.btn-sm` → `0.65rem`
  - hr_core/static_src/css/sections/about.css:211 — `.about-gallery figure.about-stage button.about-nav` → `100vmax`
  - hr_core/static_src/css/sections/about.css:264 — `.about-thumbs-wrap > button` → `100vmax`
  - ... and 1 more
- **border**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `1px solid var(--white-alpha-45)`
  - hr_core/static_src/css/components/buttons.css:63 — `.btn-neon` → `1px solid var(--btn-border-base)`
  - hr_core/static_src/css/sections/about.css:211 — `.about-gallery figure.about-stage button.about-nav` → `1px solid var(--white-alpha-30)`
  - hr_core/static_src/css/sections/about.css:264 — `.about-thumbs-wrap > button` → `1px solid var(--white-alpha-15)`
  - hr_core/static_src/css/sections/about.css:298 — `.about-thumbs button` → `1px solid var(--white-alpha-15)`
- **color**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `var(--text)`
  - hr_core/static_src/css/components/buttons.css:27 — `.btn-char` → `#BFBFBF`
  - hr_core/static_src/css/components/buttons.css:63 — `.btn-neon` → `var(--btn-text)`
  - hr_core/static_src/css/components/buttons.css:115 — `.btn-neon:hover` → `var(--btn-hover-text)`
  - hr_core/static_src/css/sections/about.css:211 — `.about-gallery figure.about-stage button.about-nav` → `var(--text)`
  - hr_core/static_src/css/sections/about.css:264 — `.about-thumbs-wrap > button` → `white`
- **font-family**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `inherit`
  - hr_core/static_src/css/components/buttons.css:27 — `.btn-char` → `"Bungee Hairline", sans-serif`
  - hr_core/static_src/css/components/buttons.css:63 — `.btn-neon` → `"Quantico", sans-serif`
  - hr_core/static_src/css/sections/shows.css:817 — `.card-btn.directions-btn` → `"Bungee Hairline", sans-serif`
- **outline**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `none`
  - hr_core/static_src/css/components/buttons.css:146 — `.btn-neon:focus-visible` → `none`
  - hr_core/static_src/css/sections/about.css:323 — `.about-thumbs button.about-thumb.is-active` → `2px solid var(--text)`
- **transition**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `border-color     .2s ease,
                      box-shadow       .2s ease,
                      background-color .2s ease`
  - hr_core/static_src/css/components/buttons.css:63 — `.btn-neon` → `transform 0.125s ease,
        filter 0.125s ease,
        box-shadow 0.125s ease,
        background 0.125s ease,
        color 0.125s ease`
  - hr_core/static_src/css/components/buttons.css:105 — `.btn-neon::after` → `box-shadow 0.125s ease`
  - hr_core/static_src/css/sections/about.css:211 — `.about-gallery figure.about-stage button.about-nav` → `background .2s ease,
                   transform  .2s ease`
  - hr_core/static_src/css/sections/about.css:264 — `.about-thumbs-wrap > button` → `background .2s ease,
                   transform  .2s ease`
  - hr_core/static_src/css/sections/about.css:298 — `.about-thumbs button` → `transform    .2s ease,
                     box-shadow   .2s ease,
                     border-color .2s ease`
  - ... and 1 more
- **display**
  - hr_core/static_src/css/components/buttons.css:27 — `.btn-char` → `inline-block`
  - hr_core/static_src/css/components/buttons.css:37 — `.card-btn` → `inline-flex`
  - hr_core/static_src/css/components/buttons.css:63 — `.btn-neon` → `flex`
  - hr_core/static_src/css/sections/about.css:211 — `.about-gallery figure.about-stage button.about-nav` → `grid`
  - hr_core/static_src/css/sections/about.css:264 — `.about-thumbs-wrap > button` → `grid`
  - hr_core/static_src/css/sections/about.css:298 — `.about-thumbs button` → `block`
  - ... and 3 more
### input
- **font-size**
  - hr_core/static_src/css/base/core.css:360 — `#modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
#modal select,
#modal textarea` → `0.75rem`
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `0.75rem`
  - hr_core/static_src/css/components/modal-ui.css:269 — `.modal input.control-compact,
.modal select.control-compact,
.modal textarea.control-compact` → `1rem`
  - hr_core/static_src/css/components/modal-ui.css:280 — `.modal .form-errors` → `0.85rem`
  - hr_core/static_src/css/components/forms.css:5 — `.form` → `0.85rem`
  - hr_core/static_src/css/components/forms.css:32 — `.form-label` → `0.7rem`
  - ... and 10 more
- **display**
  - hr_core/static_src/css/components/modal-ui.css:212 — `.modal-panel .field-row` → `grid`
  - hr_core/static_src/css/components/modal-ui.css:225 — `.modal-panel .field-col-left,
.modal-panel .field-col-right` → `grid`
  - hr_core/static_src/css/components/forms.css:10 — `.form-row` → `flex`
  - hr_core/static_src/css/components/forms.css:25 — `.form-group` → `flex`
  - hr_core/static_src/css/components/forms.css:98 — `.form-group.is-hidden` → `none`
  - hr_core/static_src/css/flows/checkout.css:111 — `.checkout-details-modal .field-row` → `flex`
  - ... and 3 more
- **gap**
  - hr_core/static_src/css/components/modal-ui.css:212 — `.modal-panel .field-row` → `var(--m-gap)`
  - hr_core/static_src/css/components/modal-ui.css:225 — `.modal-panel .field-col-left,
.modal-panel .field-col-right` → `0`
  - hr_core/static_src/css/components/forms.css:10 — `.form-row` → `0.85rem`
  - hr_core/static_src/css/flows/checkout.css:111 — `.checkout-details-modal .field-row` → `0`
- **grid-template-columns**
  - hr_core/static_src/css/components/modal-ui.css:217 — `.modal-panel .field-row-two-cols` → `minmax(0, 1fr)`
  - hr_core/static_src/css/components/modal-ui.css:221 — `.modal-panel .field-row-bottom-block` → `minmax(0, 1fr)`
  - hr_core/static_src/css/flows/checkout.css:177 — `.checkout-details-modal .field-row.m-grid` → `repeat(2, minmax(0, 1fr))`
  - hr_core/static_src/css/flows/checkout.css:185 — `.checkout-details-modal .field-row.field-row-full` → `1fr`
  - hr_core/static_src/css/flows/checkout.css:192 — `.checkout-details-modal .field-row-bottom-block.m-grid` → `minmax(0, 1fr) minmax(0, 1fr)`
- **width**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `100%`
  - hr_core/static_src/css/components/modal-ui.css:269 — `.modal input.control-compact,
.modal select.control-compact,
.modal textarea.control-compact` → `64px`
  - hr_core/static_src/css/components/drawer.css:324 — `.form-control input[type="text"],
.form-control input[type="password"]` → `100%`
  - hr_core/static_src/css/components/forms.css:48 — `.form-control` → `100%`
  - hr_core/static_src/css/flows/cart.css:81 — `.item-quantity input[type="number"]` → `64px`
  - hr_core/static_src/css/flows/account.css:30 — `.change-password-modal #password-change-form > .field-row--neutral,
.change-password-modal #password-change-form > .field-row--error,
.change-password-modal #password-change-form > .field-row--valid` → `100%`
  - ... and 1 more
- **padding**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `0.25rem`
  - hr_core/static_src/css/components/modal-ui.css:269 — `.modal input.control-compact,
.modal select.control-compact,
.modal textarea.control-compact` → `0.15rem 0.4rem`
  - hr_core/static_src/css/components/modal-ui.css:280 — `.modal .form-errors` → `0.75rem 1rem`
  - hr_core/static_src/css/components/forms.css:48 — `.form-control` → `0.25rem`
  - hr_core/static_src/css/sections/merch.css:252 — `.modal-select` → `0.25rem 0.5rem`
  - hr_core/static_src/css/flows/auth.css:105 — `.auth-modal .form-errors` → `0.75rem 1rem`
- **border-radius**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `8px`
  - hr_core/static_src/css/components/modal-ui.css:269 — `.modal input.control-compact,
.modal select.control-compact,
.modal textarea.control-compact` → `6px`
  - hr_core/static_src/css/components/modal-ui.css:280 — `.modal .form-errors` → `8px`
  - hr_core/static_src/css/components/forms.css:48 — `.form-control` → `8px`
  - hr_core/static_src/css/sections/merch.css:252 — `.modal-select` → `0.5rem`
  - hr_core/static_src/css/flows/auth.css:105 — `.auth-modal .form-errors` → `8px`
- **border**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `1px solid var(--white-alpha-45)`
  - hr_core/static_src/css/components/modal-ui.css:280 — `.modal .form-errors` → `1px solid var(--neon-red)`
  - hr_core/static_src/css/components/drawer.css:333 — `input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus` → `none`
  - hr_core/static_src/css/components/forms.css:48 — `.form-control` → `1px solid var(--white-alpha-45)`
  - hr_core/static_src/css/sections/merch.css:252 — `.modal-select` → `1px solid rgb(var(--gray1) / 0.7)`
  - hr_core/static_src/css/flows/auth.css:105 — `.auth-modal .form-errors` → `1px solid var(--neon-red)`
- **background-color**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `var(--black-alpha-60)`
  - hr_core/static_src/css/components/modal-ui.css:261 — `.modal input:not([type="checkbox"]):not([type="radio"]):focus,
.modal select:focus,
.modal textarea:focus` → `var(--black-alpha-90)`
  - hr_core/static_src/css/components/drawer.css:324 — `.form-control input[type="text"],
.form-control input[type="password"]` → `transparent`
  - hr_core/static_src/css/components/drawer.css:351 — `.form-control input[type="text"]:focus,
.form-control input[type="password"]:focus` → `transparent`
  - hr_core/static_src/css/components/forms.css:48 — `.form-control` → `var(--black-alpha-60)`
  - hr_core/static_src/css/components/forms.css:63 — `.form-control:focus` → `var(--black-alpha-90)`
- **color**
  - hr_core/static_src/css/components/modal-ui.css:244 — `.modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.modal select,
.modal textarea` → `var(--text)`
  - hr_core/static_src/css/components/modal-ui.css:280 — `.modal .form-errors` → `#FECACA`
  - hr_core/static_src/css/components/drawer.css:324 — `.form-control input[type="text"],
.form-control input[type="password"]` → `var(--neon-blue)`
  - hr_core/static_src/css/components/drawer.css:345 — `.form-control input[type="text"]::placeholder,
.form-control input[type="password"]::placeholder` → `var(--text)`
  - hr_core/static_src/css/components/drawer.css:351 — `.form-control input[type="text"]:focus,
.form-control input[type="password"]:focus` → `var(--neon-blue)`
  - hr_core/static_src/css/components/drawer.css:364 — `.field-group:focus-within label` → `var(--neon-blue)`
  - ... and 9 more

## 6) Duplicate definitions
### Same selector defined in multiple places
- `@font-face` → hr_core/static_src/css/base/core.css:5, hr_core/static_src/css/base/core.css:11, hr_core/static_src/css/base/core.css:17, hr_core/static_src/css/base/core.css:25, hr_core/static_src/css/base/core.css:33, hr_core/static_src/css/base/core.css:41, hr_core/static_src/css/base/core.css:49, hr_core/static_src/css/base/core.css:55, hr_core/static_src/css/base/core.css:61, hr_core/static_src/css/base/core.css:67, hr_core/static_src/css/sections/banner.css:2
- `:root` → hr_core/static_src/css/base/core.css:75, hr_core/static_src/css/components/buttons.css:6
- `.modal-panel` → hr_core/static_src/css/base/core.css:382, hr_core/static_src/css/components/modal-ui.css:6
- `@media (prefers-reduced-motion: reduce)` → hr_core/static_src/css/base/core.css:432, hr_core/static_src/css/base/parallax.css:106, hr_core/static_src/css/utilities/utilities.css:280, hr_core/static_src/css/sections/about.css:507, hr_core/static_src/css/sections/merch.css:480, hr_core/static_src/css/sections/shows.css:935, hr_core/static_src/css/flows/account.css:618
- `@media (max-width: 767.98px)` → hr_core/static_src/css/base/core.css:582, hr_core/static_src/css/flows/account.css:773
- `.sr-only` → hr_core/static_src/css/utilities/a11y.css:2, hr_core/static_src/css/utilities/utilities.css:182
- `.text-center` → hr_core/static_src/css/utilities/utilities.css:153, hr_core/static_src/css/components/modal-ui.css:183
- `@keyframes claimFlashFade` → hr_core/static_src/css/utilities/utilities.css:271, hr_core/static_src/css/flows/account.css:610
- `@container modal (max-width: 419.98px)` → hr_core/static_src/css/components/modal-ui.css:102, hr_core/static_src/css/sections/merch.css:288
- `@container modal (min-width: 420px) and (max-width: 599.98px)` → hr_core/static_src/css/components/modal-ui.css:108, hr_core/static_src/css/sections/merch.css:328
- `@container modal (min-width: 600px)` → hr_core/static_src/css/components/modal-ui.css:114, hr_core/static_src/css/components/modal-ui.css:231
- `@container modal (min-width: 1100px)` → hr_core/static_src/css/components/modal-ui.css:137, hr_core/static_src/css/sections/merch.css:415
- `.modal-title` → hr_core/static_src/css/components/modal-ui.css:147, hr_core/static_src/css/sections/merch.css:207
- `@container modal (max-width: 599.98px)` → hr_core/static_src/css/components/modal-ui.css:365, hr_core/static_src/css/flows/checkout.css:197, hr_core/static_src/css/flows/checkout.css:433, hr_core/static_src/css/flows/checkout.css:649
- `@media (min-width: 1280px)` → hr_core/static_src/css/components/drawer.css:77, hr_core/static_src/css/sections/merch.css:110
- `@media (max-width: 640px)` → hr_core/static_src/css/components/forms.css:104, hr_core/static_src/css/sections/about.css:468
- `@media (max-width: 768px)` → hr_core/static_src/css/sections/bulletin.css:172, hr_core/static_src/css/sections/bulletin.css:300
- `@media (min-width: 1024px)` → hr_core/static_src/css/sections/merch.css:102, hr_core/static_src/css/sections/shows.css:885
- `@media (min-width: 1440px)` → hr_core/static_src/css/sections/merch.css:121, hr_core/static_src/css/sections/shows.css:908
- `@container modal (max-width: 1099.98px)` → hr_core/static_src/css/sections/merch.css:401, hr_core/static_src/css/flows/checkout.css:723
- ... and 19 more

### Repeated declaration blocks (near-duplicates)
- Declarations:
  - `position:fixed`
  - Occurrences:
    - hr_core/static_src/css/base/core.css:228 — `nav.navbar`
    - hr_core/static_src/css/utilities/utilities.css:51 — `.fixed`
- Declarations:
  - `font-size:0.75rem`
  - Occurrences:
    - hr_core/static_src/css/base/core.css:360 — `#modal input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
#modal select,
#modal textarea`
    - hr_core/static_src/css/flows/checkout.css:76 — `.checkout-details-form input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.checkout-details-form select,
.checkout-details-form textarea`
- Declarations:
  - `color:var(--neon-red)`
  - Occurrences:
    - hr_core/static_src/css/base/core.css:460 — `.modal-close-btn:hover`
    - hr_core/static_src/css/flows/auth.css:64 — `.auth-state-error .checkout-state-icon`
    - hr_core/static_src/css/flows/checkout.css:24 — `.checkout-awaiting-confirmation .confirmation-icon .fa-times-circle`
    - hr_core/static_src/css/flows/checkout.css:760 — `.account-status-layout section.account-status-panel:nth-of-type(2) .account-status-panel-text > p.modal-kicker`
- Declarations:
  - `color:var(--neon-green)`
  - Occurrences:
    - hr_core/static_src/css/base/core.css:576 — `.text-success`
    - hr_core/static_src/css/flows/auth.css:60 — `.auth-state-success .checkout-state-icon`
    - hr_core/static_src/css/flows/checkout.css:756 — `.account-status-layout .account-status-panel:first-of-type .account-status-panel-text > p.modal-kicker`
- Declarations:
  - `display:block`
  - Occurrences:
    - hr_core/static_src/css/utilities/utilities.css:30 — `.block`
    - hr_core/static_src/css/sections/about.css:294 — `.about-thumbs li.is-visible`
- Declarations:
  - `display:inline`
  - Occurrences:
    - hr_core/static_src/css/utilities/utilities.css:34 — `.inline`
    - hr_core/static_src/css/flows/checkout.css:88 — `.checkout-awaiting-confirmation .htmx-request .htmx-indicator`
- Declarations:
  - `width:100%`
  - Occurrences:
    - hr_core/static_src/css/utilities/utilities.css:77 — `.w-full`
    - hr_core/static_src/css/components/modal-ui.css:89 — `.m-actions > *`
    - hr_core/static_src/css/components/drawer.css:448 — `article button`
    - hr_core/static_src/css/sections/bulletin.css:10 — `.bulletin-root`
    - hr_core/static_src/css/flows/account.css:38 — `.change-password-modal #password-change-form input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"]):not([type="button"]):not([type="submit"]):not([type="reset"]),
.change-password-modal #password-change-form select,
.change-password-modal #password-change-form textarea`
    - ... and 1 more
- Declarations:
  - `align-items:center`
  - Occurrences:
    - hr_core/static_src/css/utilities/utilities.css:90 — `.items-center`
    - hr_core/static_src/css/flows/checkout.css:543 — `.order-item-row`
    - hr_core/static_src/css/flows/account.css:402 — `.account-status-actions--inline`
- Declarations:
  - `margin-top:0.75rem`
  - Occurrences:
    - hr_core/static_src/css/utilities/utilities.css:115 — `.mt-3`
    - hr_core/static_src/css/flows/checkout.css:229 — `.modal-actions.stack.uniform`
    - hr_core/static_src/css/flows/checkout.css:780 — `.order-payment-msg .form-errors`
- Declarations:
  - `left:0`
  - Occurrences:
    - hr_core/static_src/css/utilities/utilities.css:143 — `.left-0`
    - hr_core/static_src/css/sections/about.css:370 — `.about-quote-wrap::before`

## 7) Risks / recommendations (prioritized)
1. **Modal-related collisions**: selectors scoped by `.modal` and `#modal` appear alongside global element rules and utility classes; consider a dedicated modal layer and component-specific classes to reduce cross-component overrides.
2. **Button/input duplication**: `.card-btn`, `.btn`, `button`, `input`, and form-related selectors are defined in multiple files; consolidate base styles and define modifiers to avoid repeated overrides.
3. **Layout overrides**: deep descendant selectors and file-order overrides in flows (`flows/*`) can mask base component rules; consider component-level tokens or @layer ordering to surface intent.