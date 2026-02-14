// hr_core/static_src/js/modules/account.js

function initUnclaimedOrders (root = document) {
    const list = root.querySelector(".order-claim-list");
    if (!list) return;

    // guard: don't double-bind
    if (list.dataset.bound === "1") return;
    list.dataset.bound = "1";

    const selectAll = list.querySelector("#select-all-unclaimed");
    if (!selectAll) return;

    const getBoxes = () =>
        Array.from(list.querySelectorAll('input[type="checkbox"][name="order_ids"]'));


    const syncSelectAll = () => {
        const boxes = getBoxes();
        const total = boxes.length;
        const checked = boxes.filter(b => b.checked).length;

        if (total === 0) {
            selectAll.checked = false;
            selectAll.indeterminate = false;
            return;
        }

        selectAll.checked = checked === total;
        selectAll.indeterminate = checked > 0 && checked < total;
    };

    selectAll.addEventListener("change", () => {
        const boxes = getBoxes();
        boxes.forEach(b => (b.checked = selectAll.checked));
        selectAll.indeterminate = false;
    });

    list.addEventListener("change", (e) => {
        const t = e.target;
        if (!t?.classList?.contains("unclaimed-order-checkbox")) return;
        syncSelectAll();
    });

    const mo = new MutationObserver(syncSelectAll);
    mo.observe(list, {childList: true, subtree: true});

    syncSelectAll();
}

export function initAccountUI (root = document) {
    initUnclaimedOrders(root);
}
