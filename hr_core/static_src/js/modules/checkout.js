// hr_core/static_src/js/modules/checkout.js
//
// Checkout UI helpers (single-provider Stripe Embedded Checkout):
//  - checkout details form: show/hide unit field based on building type
//  - checkout pay: mount Stripe Embedded Checkout when #checkout-pay-root exists
//
// Notes:
//  - Safe to call repeatedly (idempotent guards).
//  - Stripe.js is loaded on-demand.

/* global Stripe */

function getCookie(name) {
  const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return m ? decodeURIComponent(m[2]) : "";
}

function loadStripeJs() {
  return new Promise((resolve, reject) => {
    if (window.Stripe) return resolve();
    const s = document.createElement("script");
    s.src = "https://js.stripe.com/v3/";
    s.async = true;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

/**
 * Initialize the Checkout Details modal/page behavior.
 * Call this after HTMX swaps in the checkout details content, or on DOMContentLoaded for SSR.
 */
export function initCheckout(root = document) {
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

  function updateUnitVisibility() {
    const val = (buildingSelect.value || "").trim();

    if (showFor.has(val)) {
      unitGroup.classList.remove("hidden");
    } else {
      unitGroup.classList.add("hidden");
      unitInput.value = "";
      unitInput.dispatchEvent(new Event("input", { bubbles: true }));
      unitInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  buildingSelect.addEventListener("change", updateUnitVisibility);
  updateUnitVisibility();
}

/**
 * Initialize Stripe Embedded Checkout (if the pay root exists).
 *
 * Expected markup (SSR or HTMX partial):
 *   <div id="checkout-pay-root"
 *        data-stripe-publishable-key="pk_..."
 *        data-client-secret=""  (optional)
 *        data-session-endpoint="/payment/checkout/stripe/session/<order_id>/">
 *     <div id="embedded-checkout" data-embedded-checkout></div>
 *   </div>
 *
 * Safe to call repeatedly; mounts once per pay root.
 */
export async function initCheckoutPay(root = document) {
  const container = root || document;

  const payRoot =
    container.getElementById?.("checkout-pay-root") ||
    container.querySelector?.("#checkout-pay-root");

  if (!payRoot) return;

  // idempotent guard per pay root
  if (payRoot._checkoutPayInitDone) return;
  payRoot._checkoutPayInitDone = true;

  const pk = payRoot.dataset.stripePublishableKey || "";
  const existingClientSecret = payRoot.dataset.clientSecret || "";
  const endpoint = payRoot.dataset.sessionEndpoint || "";

  if (!pk || !endpoint) {
    console.warn("checkout-pay: missing publishable key or session endpoint");
    return;
  }

  // Ensure mount node exists inside this root (avoid mounting into stale/global nodes)
  const mountEl =
    payRoot.querySelector?.("[data-embedded-checkout]") ||
    payRoot.querySelector?.("#embedded-checkout");

  if (!mountEl) {
    console.warn("checkout-pay: missing embedded checkout mount element");
    return;
  }

  // If we already mounted into this element, stop.
  if (mountEl.dataset.stripeMounted === "1") return;

  try {
    await loadStripeJs();
  } catch (e) {
    console.error("checkout-pay: failed to load Stripe.js", e);
    mountEl.innerHTML = "<p class='muted'>Payment UI failed to load. Please refresh.</p>";
    return;
  }

  const StripeCtor = window.Stripe;
  if (typeof StripeCtor !== "function") {
    console.warn("checkout-pay: Stripe.js loaded but window.Stripe is not a function");
    mountEl.innerHTML = "<p class='muted'>Payment UI failed to load. Please refresh.</p>";
    return;
  }

  const stripe = StripeCtor(pk);

  // Stripe recommends fetchClientSecret so it can refetch when needed.
  const fetchClientSecret = async () => {
    if (existingClientSecret) return existingClientSecret;

    const resp = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({}),
      credentials: "same-origin",
    });

    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(`checkout-pay: failed to create session (${resp.status}) ${text}`);
    }

    const data = await resp.json().catch(() => ({}));
    if (!data || !data.clientSecret) {
      throw new Error("checkout-pay: no clientSecret returned");
    }
    return data.clientSecret;
  };

  try {
    const embeddedCheckout = await stripe.initEmbeddedCheckout({ fetchClientSecret });
    embeddedCheckout.mount(mountEl);
    mountEl.dataset.stripeMounted = "1";
  } catch (e) {
    console.error("checkout-pay: initEmbeddedCheckout failed", e);
    mountEl.innerHTML =
      "<p class='muted'>Payment UI failed to initialize. Please refresh or try again.</p>";
  }
}

/**
 * Convenience init for meta-init: runs BOTH checkout details + checkout pay behavior.
 * Safe to call repeatedly; each sub-init has its own guards.
 */
export function initCheckoutModule(root = document) {
  initCheckout(root);
  // don't await; it is internally guarded and will self-handle load timing
  initCheckoutPay(root);
}
