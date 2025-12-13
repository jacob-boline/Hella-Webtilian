(function () {
    const form = document.getElementById('checkout-details-form');
    if (!form) return;

    // const buildingSelect = form.querySelector('[name="building_type"]');
    const buildingSelect = document.getElementById('id_building_type');
    const unitGroup = document.getElementById('unit-group');

    if (!buildingSelect || !unitGroup) return;

    function updateUnitVisibility () {
        const val = buildingSelect.value;
        // show only for apartment / business / other
        const showFor = ['apartment', 'business', 'other'];

        if (showFor.indexOf(val) >= 0) {
            unitGroup.style.visibility = 'visible';
        } else {
            unitGroup.style.visibility = 'hidden';
            const unitInput = unitGroup.querySelector('input');
            if (unitInput) unitInput.value = '';
        }
    }

    buildingSelect.addEventListener('change', updateUnitVisibility);
    updateUnitVisibility();
})();