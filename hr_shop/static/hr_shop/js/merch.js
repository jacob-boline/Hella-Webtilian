(function () {
    // -----------------------------
    // Stripe checkout buttons
    // -----------------------------
    const publishableKey = window.STRIPE_PUBLISHABLE_KEY || 'pk_test_XXXXYOUR_PUBLISHABLE_KEY';
    const stripe = window.Stripe ? Stripe(publishableKey) : null;

    function handleStripeResult(result) {
        if (result && result.error) {
            console.error(result.error.message);
            alert(result.error.message);
        }
    }

    document.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-buy]');
        if (!btn || !stripe) return;

        const priceId = btn.dataset.priceId;
        const qty = parseInt(btn.dataset.qty || '1', 10);

        if (!priceId) {
            console.warn('Missing data-price-id on buy button');
            return;
        }

        stripe.redirectToCheckout({
            lineItems: [{ price: priceId, quantity: qty }],
            mode: 'payment',
            successUrl: window.location.origin +
                '/checkout/success?session_id={CHECKOUT_SESSION_ID}',
            cancelUrl: window.location.origin + '/checkout/cancel'
        }).then(handleStripeResult);
    });

    // -----------------------------
    // Variant → image resolver
    // -----------------------------
    function buildQueryFromForm(form) {
        const params = new URLSearchParams();
        const selects = form.querySelectorAll('select[name^="opt_"]');

        selects.forEach((sel) => {
            const val = sel.value;
            if (val) {
                // ov=id1&ov=id2&...
                params.append('ov', val);
            }
        });

        return params.toString();
    }

    async function fetchImageForSelection(rootEl) {
        // rootEl can be either the .modal-product container or any child inside it
        const contentRoot =
            rootEl.classList.contains('modal-product')
                ? rootEl
                : rootEl.closest('.modal-product');

        if (!contentRoot) return;

        const form = contentRoot.querySelector('#product-options-form');
        const imgEl = contentRoot.querySelector('.modal-image');

        if (!form || !imgEl) return;

        const productSlug = contentRoot.getAttribute('data-product-slug');
        if (!productSlug) return;

        const qs = buildQueryFromForm(form);
        const url = `/shop/product/${productSlug}/image-for-selection/?${qs}`;

        try {
            const resp = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!resp.ok) return;

            const data = await resp.json();
            if (data.url) {
                imgEl.src = data.url;
                if (data.alt) imgEl.alt = data.alt;
            }
        } catch (err) {
            console.error('Failed to update modal image', err);
        }
    }

    // Fire whenever a product option changes inside the modal
    document.addEventListener('change', async (e) => {
        const select = e.target.closest('select[name^="opt_"]');
        if (!select) return;

        const modalRoot = select.closest('.modal-product');
        if (!modalRoot) return;

        await fetchImageForSelection(modalRoot);
    });

    // Optional: expose helper
    window.hrShop = window.hrShop || {};
    window.hrShop.updateModalImageForSelection = fetchImageForSelection;
})();
