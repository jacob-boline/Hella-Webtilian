// hr_shop/static/hr_shop/js/checkout.js

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

  // unit input rendered by Django form_group -> wrapper is the field-group div
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
      // optional: keep any browser validation happy if you ever add required rules
      unitInput.dispatchEvent(new Event("input", { bubbles: true }));
      unitInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  buildingSelect.addEventListener("change", updateUnitVisibility);
  updateUnitVisibility();
}
