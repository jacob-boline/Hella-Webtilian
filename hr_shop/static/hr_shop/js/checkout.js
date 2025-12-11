(function () {
    const form = document.getElementById('checkout-details-form');
    if (!form) return;

    const buildingSelect = form.querySelector('[name="{{ form.building_type.name }}"]');
    const unitGroup = document.getElementById('unit-number-group');

    if (!buildingSelect || !unitGroup) return;

    function updateUnitVisibility() {
      const val = buildingSelect.value;
      // show only for apartment / business / other
      const showFor = ['apartment', 'business', 'other'];

      if (showFor.indexOf(val) !== -1) {
        unitGroup.style.display = '';
      } else {
        unitGroup.style.display = 'none';
        const unitInput = unitGroup.querySelector('input');
        if (unitInput) unitInput.value = '';
      }
    }

    buildingSelect.addEventListener('change', updateUnitVisibility);
    updateUnitVisibility();
  })();