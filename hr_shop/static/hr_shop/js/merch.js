// hr_site/static/hr_site/js/merch.js

(function () {
    // -----------------------------
    // HTMX merch modal hook
    // -----------------------------
    document.addEventListener('htmx:afterSwap', (e) => {
        if (e.target && e.target.id === 'merch-modal-body') {
            const modal = document.getElementById('merch-modal');
            if (modal) {
                modal.classList.remove('hidden');
            }
        }
    });

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
})();
