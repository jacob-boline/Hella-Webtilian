// hr_core/static_src/js/modules/checkout.js
//
// Checkout UI helpers:
//  - checkout details form: show/hide unit field based on building type
//  - checkout pay page: mount Stripe Embedded Checkout (when present)
//
// Notes:
//  - Safe to call repeatedly (idempotent guards).
//  - Stripe globals are loaded on-demand if needed.

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
 *     <div id="embedded-checkout"></div>
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

  // If we've already mounted once, don't do it again.
  if (payRoot._checkoutPayInitDone) return;
  payRoot._checkoutPayInitDone = true;

  const pk = payRoot.dataset.stripePublishableKey || "";
  const existingClientSecret = payRoot.dataset.clientSecret || "";
  const endpoint = payRoot.dataset.sessionEndpoint || "";

  if (!pk || !endpoint) {
    console.warn("checkout-pay: missing publishable key or session endpoint");
    return;
  }

  const mountEl =
    payRoot.querySelector?.("#embedded-checkout") ||
    payRoot.querySelector?.("[data-embedded-checkout]");

  if (!mountEl) {
    console.warn("checkout-pay: missing #embedded-checkout mount element");
    return;
  }

  // If we already mounted UI into this element somehow, stop.
  // (Prevents weird remounts when modal open/close does not swap content.)
  if (mountEl.dataset.stripeMounted === "1") return;

  try {
    await loadStripeJs();
  } catch (e) {
    console.error("checkout-pay: failed to load Stripe.js", e);
    mountEl.innerHTML =
      "<p class='muted'>Payment UI failed to load. Please refresh.</p>";
    return;
  }

  const StripeCtor = window.Stripe;
  if (typeof StripeCtor !== "function") {
    console.warn("checkout-pay: Stripe.js loaded but window.Stripe is not a function");
    mountEl.innerHTML =
      "<p class='muted'>Payment UI failed to load. Please refresh.</p>";
    return;
  }

  const stripe = StripeCtor(pk);

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
 */
export function initCheckoutModule(root = document) {
  initCheckout(root);
  initCheckoutPay(root);

  // Optional: if ui-global exposes hrModal.close, clear mount guards on modal close.
  // This helps if you close the modal without swapping (some flows do).
  // Safe no-op if hrSite/hrModal isn't present.
  if (!window.hrSite) window.hrSite = {};
  if (!window.hrSite._checkoutModalHooked) {
    window.hrSite._checkoutModalHooked = true;

    document.addEventListener("click", (e) => {
      const closer = e.target.closest?.("[data-modal-close], .modal-backdrop");
      if (!closer) return;

      const pr = document.getElementById("checkout-pay-root");
      if (pr) {
        // allow re-init if reopened without fresh swap
        delete pr._checkoutPayInitDone;
        const mount = pr.querySelector?.("#embedded-checkout");
        if (mount) mount.dataset.stripeMounted = "0";
      }
    });
  }
}
