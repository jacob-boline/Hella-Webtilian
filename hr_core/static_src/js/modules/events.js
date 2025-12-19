// hr_core/static/hr_core/js/events.js
//
// App-level custom-events.

(function () {
    // ------------------------------
    // Helpers
    // ------------------------------
    function safeCall(fn, ...args) {
        try { return typeof fn === 'function' ? fn(...args) : undefined; }
        catch (e) { console.error('[events] handler error', e); }
    }

    function getDetail(event) {
        return event?.detail ?? {};
    }

    // ------------------------------
    // 1) showMessage -> global message bar
    // ------------------------------
    document.body.addEventListener('showMessage', (event) => {
        const detail = getDetail(event);

        // support both:
        //   {message: "hi", duration: 5000}
        //   "hi"
        const msg =
            (typeof detail === 'string' ? detail : null) ||
            detail.message ||
            detail.text ||
            '';

        const duration = detail.duration || 5000;
        if (!msg) return;

        safeCall(window.hrSite?.showGlobalMessage, msg, duration);
    });

    // ------------------------------
    // 2) closeModal -> close modal only
    // ------------------------------
    document.body.addEventListener('closeModal', () => {
        safeCall(window.hrSite?.hideModal);
    });


    // ------------------------------
    // 4) updateCart -> badge count
    // ------------------------------
    document.body.addEventListener('updateCart', (event) => {
        const detail = getDetail(event);
        const count = Number(detail.item_count ?? detail.count ?? 0);

        const badge = document.getElementById('cart-count');
        if (!badge) return;

        badge.textContent = String(count);
        badge.style.display = count > 0 ? 'inline-flex' : 'none';
    });

    // ------------------------------
    // 5) variantPreviewUpdated -> update modal image/price/buy button
    // ------------------------------
    document.body.addEventListener('variantPreviewUpdated', (event) => {
        const detail = getDetail(event);
        if (!detail) return;

        const modal = document.querySelector('.modal-product');
        if (!modal) return;

        const imgEl = modal.querySelector('.modal-image');
        const priceEl = modal.querySelector('[data-role="modal-price"]');
        const buyBtn = modal.querySelector('[data-role="buy-selected-variant"]');

        if (imgEl && detail.image_url) imgEl.src = detail.image_url;
        if (priceEl && detail.price) priceEl.textContent = `$${detail.price}`;
        if (buyBtn && detail.variant_slug) {
            buyBtn.setAttribute('hx-post', `/shop/cart/add/${detail.variant_slug}/`);
            buyBtn.setAttribute('hx-swap', 'none');
        }
    });

    // ------------------------------
    // 6) accessChanged -> refresh sidebar access panel (optional)
    // Requires an element like:
    //   <div id="sidebar-access" data-access-url="/access/sidebar/"></div>
    // ------------------------------
    document.body.addEventListener('accessChanged', () => {
        const el = document.getElementById('sidebar-access');
        if (!el) return;

        const url = el.dataset.accessUrl;
        if (!url) {
            console.warn('[events] #sidebar-access missing data-access-url');
            return;
        }

        if (!window.htmx) {
            console.warn('[events] htmx not found; cannot refresh sidebar access');
            return;
        }

        window.htmx.ajax('GET', url, { target: '#sidebar-access', swap: 'innerHTML' });
    });






    //  // ------------------------------
    // // 3) closeModalShowGlobalMessage -> close modal then show message
    // // (kept for backward compat, but you can stop using it)
    // // ------------------------------
    // document.body.addEventListener('closeModalShowGlobalMessage', (event) => {
    //     const detail = getDetail(event);
    //     const msg = detail.message || detail.text || 'Success.';
    //     const duration = detail.duration || 5000;
    //
    //     safeCall(window.hrSite?.hideModal);
    //     safeCall(window.hrSite?.showGlobalMessage, msg, duration);
    // });

})();
