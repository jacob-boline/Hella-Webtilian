// hr_core/static_src/js/modules/checkout.js

// Checkout UI helpers (single-provider Stripe Embedded Checkout):
//  - checkout details form: show/hide unit field based on building type
//  - checkout pay: mount Stripe Embedded Checkout when #checkout-pay-root exists
//
// Notes:
//  - Safe to call repeatedly (idempotent guards).
//  - Stripe.js is loaded on-demand.


import {getCsrfToken} from '../utils/htmx-csrf.js';

// ------------------------------
// Safe DOM messaging helpers
// ------------------------------
function renderMountMessage (mountEl, message) {
    if (!mountEl) return;
    const p = document.createElement("p");
    p.className = "muted";
    p.textContent = message;
    mountEl.replaceChildren(p);
}

// ------------------------------
// Stripe.js loader
// ------------------------------
async function loadStripeJs () {
    if (typeof window.Stripe === "function") return;

    await new Promise((resolve, reject) => {
        const s = document.createElement("script");
        s.src = "https://js.stripe.com/v3/";
        s.async = true;
        s.onload = () => resolve();
        s.onerror = (e) => reject(e);
        document.head.appendChild(s);
    });

    if (typeof window.Stripe !== "function") {
        throw new Error("Stripe.js loaded but window.Stripe is not a function");
    }
}

/**
 * Initialize the Checkout Details modal/page behavior.
 */
export function initCheckout (root = document) {
    const container = root || document;

    const form =
        container.getElementById?.("checkout-details-form") ||
        container.querySelector?.("#checkout-details-form");

    if (!form) return;

    // idempotent guard per-form
    if (form._checkoutInitDone) return;
    form._checkoutInitDone = true;

    const buildingSelect =
        form.querySelector("#id_building_type") ||
        form.querySelector('[name="building_type"]');

    const unitInput =
        form.querySelector("#id_unit") ||
        form.querySelector('[name="unit"]');

    if (!buildingSelect || !unitInput) return;

    // unit input rendered by Django form_group -> wrapper is the field-group div
    const unitGroup = unitInput.closest(".field-group");
    if (!unitGroup) return;

    const showFor = new Set(["apartment", "business", "other"]);

    function updateUnitVisibility () {
        const val = (buildingSelect.value || "").trim();

        if (showFor.has(val)) {
            unitGroup.classList.remove("hidden");
        } else {
            unitGroup.classList.add("hidden");
            unitInput.value = "";
            unitInput.dispatchEvent(new Event("input", {bubbles: true}));
            unitInput.dispatchEvent(new Event("change", {bubbles: true}));
        }
    }

    buildingSelect.addEventListener("change", updateUnitVisibility);
    updateUnitVisibility();
}

// ------------------------------
// Checkout Pay helpers
// ------------------------------

function buildSessionHeaders ({checkoutToken}) {
    const headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
        "X-Requested-With": "XMLHttpRequest",
    };
    if (checkoutToken) {
        headers["X-Checkout-Token"] = checkoutToken;
    }
    return headers;
}

function createFetchClientSecret ({endpoint, existingClientSecret, checkoutToken}) {
    return async () => {
        if (existingClientSecret) return existingClientSecret;

        const resp = await fetch(endpoint, {
            method: "POST",
            headers: buildSessionHeaders({checkoutToken}),
            body: JSON.stringify({}),
            credentials: "same-origin"
        });

        if (!resp.ok) {
            if (resp.status === 401 || resp.status === 403 || resp.status === 404) {
                throw new Error(
                    "Session expired or not authorized. Please return to checkout and try again."
                );
            }
            const text = await resp.text().catch(() => "");
            throw new Error(`Failed to create payment session (${resp.status}) ${text}`);
        }

        /** @type {StripeSessionResponse} */
        const data = await resp.json().catch(() => ({}));
        if (!data || !data.clientSecret) {
            throw new Error("No clientSecret returned from server");
        }
        return data.clientSecret;
    };
}

/**
 * Initialize Stripe Embedded Checkout (if the pay root exists).
 * Safe to call repeatedly; mounts once per mount element.
 *
 * Dataset state machine on mount element:
 *   - stripeInitState="init"     => in-flight init, block reentry
 *   - stripeInitState="mounted"  => mounted, block reentry
 *   - stripeInitState="error"    => previous failure, allow retry
 */
export async function initCheckoutPay (root = document) {
    const container = root || document;

    const payRoot =
        container.getElementById?.("checkout-pay-root") ||
        container.querySelector?.("#checkout-pay-root");

    if (!payRoot) return;

    const mountEl =
        payRoot.querySelector?.("[data-embedded-checkout]") ||
        payRoot.querySelector?.("#embedded-checkout");

    if (!mountEl) {
        console.warn("checkout-pay: missing embedded checkout mount element");
        return;
    }

    // ------------------------------
    // Dataset state machine guard
    // ------------------------------
    const state = (mountEl.dataset.stripeInitState || "").trim();
    if (state === 'mounted') {
        if (document.body.contains(mountEl)) return;
        else mountEl.dataset.stripeInitState = 'error';
    }
    if (state === "init") return;

    // Mark init in-flight immediately to prevent parallel calls racing.
    mountEl.dataset.stripeInitState = "init";

    const pk                   = (payRoot.dataset.stripePublishableKey || "").trim();
    const existingClientSecret = (payRoot.dataset.clientSecret         || "").trim();
    const endpoint             = (payRoot.dataset.sessionEndpoint      || "").trim();
    const checkoutToken        = (payRoot.dataset.checkoutToken        || "").trim();

    if (!pk || !endpoint) {
        console.warn("checkout-pay: missing publishable key or session endpoint");
        mountEl.dataset.stripeInitState = "error";
        return;
    }

    try {
        await loadStripeJs();
    } catch (e) {
        console.error("checkout-pay: failed to load Stripe.js", e);
        renderMountMessage(mountEl, "Payment UI failed to load. Please refresh.");
        mountEl.dataset.stripeInitState = "error";
        return;
    }

    const StripeCtor = window.Stripe;
    if (typeof StripeCtor !== "function") {
        console.warn("checkout-pay: Stripe.js loaded but window.Stripe is not a function");
        renderMountMessage(mountEl, "Payment UI failed to load. Please refresh.");
        mountEl.dataset.stripeInitState = "error";
        return;
    }

    const stripe = StripeCtor(pk);

    const fetchClientSecret = createFetchClientSecret({endpoint, existingClientSecret, checkoutToken});

    if (window.__hrEmbeddedCheckout) {
        try { window.__hrEmbeddedCheckout.destroy(); }
        catch (_) {}
        window.__hrEmbeddedCheckout = null;
    }

    try {
        const embeddedCheckout = await stripe.initEmbeddedCheckout({fetchClientSecret});
        window.__hrEmbeddedCheckout = embeddedCheckout;
        embeddedCheckout.mount(mountEl);
        mountEl.dataset.stripeInitState = "mounted";
    } catch (e) {
        console.error("checkout-pay: initEmbeddedCheckout failed", e);
        renderMountMessage(mountEl, "Payment UI failed to initialize. Please refresh or try again.");
        mountEl.dataset.stripeInitState = "error";
    }

}

/**
 * Convenience init for meta-init: runs BOTH checkout details + checkout pay behavior.
 * Safe to call repeatedly; each sub-init has its own guards.
 */
export function initCheckoutModule (root = document) {
    initCheckout(root);
    initCheckoutPay(root).catch((e) => console.error("checkout-pay init failed", e));
}
