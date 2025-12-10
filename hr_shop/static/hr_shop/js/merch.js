(function () {
    // -----------------------------
    // Stripe checkout buttons
    // -----------------------------
    const publishableKey = window.STRIPE_PUBLISHABLE_KEY || 'pk_test_XXXXYOUR_PUBLISHABLE_KEY';
    const stripe = window.Stripe ? Stripe(publishableKey) : null;

    function handleStripeResult (result) {
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
            lineItems: [{price: priceId, quantity: qty}],
            mode: 'payment',
            successUrl: window.location.origin +
                '/checkout/success?session_id={CHECKOUT_SESSION_ID}',
            cancelUrl: window.location.origin + '/checkout/cancel'
        }).then(handleStripeResult);
    });

    // -----------------------------
    // Variant → image resolver
    // -----------------------------
    function buildQueryFromForm (form) {
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

    // async function fetchImageForSelection (rootEl) {
    //     // rootEl can be either the .modal-product container or any child inside it
    //     const contentRoot =
    //         rootEl.classList.contains('modal-product')
    //             ? rootEl
    //             : rootEl.closest('.modal-product');
    //
    //     if (!contentRoot) return;
    //
    //     const form = contentRoot.querySelector('#product-options-form');
    //     const imgEl = contentRoot.querySelector('.modal-image');
    //
    //     if (!form || !imgEl) return;
    //
    //     const productSlug = contentRoot.getAttribute('data-product-slug');
    //     if (!productSlug) return;
    //
    //     const qs = buildQueryFromForm(form);
    //     const url = `/shop/product/${productSlug}/image-for-selection/?${qs}`;
    //
    //     try {
    //         const resp = await fetch(url, {
    //             headers: {'X-Requested-With': 'XMLHttpRequest'},
    //         });
    //         if (!resp.ok) return;
    //
    //         const data = await resp.json();
    //         if (data.url) {
    //             imgEl.src = data.url;
    //             if (data.alt) imgEl.alt = data.alt;
    //         }
    //     } catch (err) {
    //         console.error('Failed to update modal image', err);
    //     }
    // }

    // Mark the clicked thumbnail as active
    document.addEventListener('click', (event) => {
        const btn = event.target.closest('button.merch-img, .merch-actions .card-btn.outline');
        if (!btn) return;

        console.log('[merch] merch-img clicked', btn);

        const card = btn.closest('.merch-card');
        if (!card) {
            console.warn('[merch] clicked button not inside .merch-card');
            return;
        }

        // clear old active states
        document.querySelectorAll('.merch-thumb-img.is-active, .modal-image.is-active')
            .forEach(el => el.classList.remove('is-active'));

        const thumb = card.querySelector('.merch-thumb-img');
        if (thumb) {
            thumb.classList.add('is-active');
            console.log('[merch] thumb made active', thumb);
        }
    });

    function openModal () {
        const modal = document.getElementById('modal');
        if (!modal) return;
        modal.classList.remove('hidden');
    }

    // When HTMX swaps the modal content in:
    document.addEventListener('htmx:afterSwap', (event) => {
        const detail = event.detail;
        if (!detail || !detail.target) return;

        if (!detail.target.closest('#modal')) return;

        console.log('[merch] htmx:afterSwap in modal', detail.target);

        const modal = document.getElementById('modal');
        if (!modal) return;

        const thumb = document.querySelector('.merch-thumb-img.is-active');
        const modalImg = modal.querySelector('.modal-image');

        console.log('[merch] thumb active?', !!thumb, 'modalImg found?', !!modalImg);

        if (!document.startViewTransition || !thumb || !modalImg) {
            console.log('[merch] no view transition support or missing elements, opening modal normally');
            openModal();
            return;
        }

        document.startViewTransition(() => {
            // OLD snapshot happens *before* this callback runs

            // NEW snapshot: only modal image is the shared element
            thumb.classList.remove('is-active');
            modalImg.classList.add('is-active');
            console.log('[merch] thumb -> modal is-active swap', {thumb, modalImg});

            openModal();
        });
    });


    // // Fire whenever a product option changes inside the modal
    // document.addEventListener('change', async (e) => {
    //     const select = e.target.closest('select[name^="opt_"]');
    //     if (!select) return;
    //
    //     const modalRoot = select.closest('.modal-product');
    //     if (!modalRoot) return;
    //
    //     await fetchImageForSelection(modalRoot);
    // });


    document.body.addEventListener('updateCart', function (event) {
        console.log('updateCart event received:', event);
        const count = event.detail.item_count;
        const badge = document.getElementById('cart-count');
        if (!badge) return;

        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-flex' : 'none';
    });

    document.body.addEventListener('variantPreviewUpdated', function (event) {
        console.log('detected variantPreviewUpdated event');
        const detail = event.detail;
        if (!detail) return;

        const modal = document.querySelector('.modal-product');
        if (!modal) return;

        const imgEl = modal.querySelector('.modal-image');
        const priceEl = modal.querySelector('[data-role="modal-price"]');
        const buyBtn = modal.querySelector('[data-role="buy-selected-variant"]');

        // Image
        if (imgEl && detail.image_url) {
            imgEl.src = detail.image_url;
        }

        // Price
        if (priceEl && detail.price) {
            priceEl.textContent = `$${detail.price}`;
        }

        // Buy button → direct add_to_cart for this variant
        if (buyBtn && detail.variant_slug) {
            buyBtn.setAttribute('hx-post', `/shop/cart/add/${detail.variant_slug}/`);
            buyBtn.setAttribute('hx-swap', 'none');
        }
    });


    // Optional: expose helper
    window.hrShop = window.hrShop || {};
    // window.hrShop.updateModalImageForSelection = fetchImageForSelection;
})();
