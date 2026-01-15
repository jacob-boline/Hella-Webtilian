// hr_core/static/hr_core/js/events.js
//
// App-level custom-events.

(function () {
    // ------------------------------
    // Helpers
    // ------------------------------

    let lastIntent = null;
    let pendingIntent = null;
    let _authRequiredLockUntil = 0;

    function safeCall(fn, ...args) {
        try { return typeof fn === 'function' ? fn(...args) : undefined; }
        catch (e) {
            console.error('[events] handler error', e);
            return undefined;
        }
    }

    function getDetail(event) {
        return event?.detail ?? {};
    }

    function isHtmxUnauthorized(event) {
        const xhr = event?.detail?.xhr;
        return !!xhr && Number(xhr.status) === 401;
    }

    function triggerAuthRequired(payload) {
        if (!window.htmx) return;
        window.htmx.trigger(document.body, 'authRequired', payload || {});
    }

    function buildIntentFromHtmxConfig(evt) {
        const d = evt.detail || {};
        const xhr = d.xhr;
        if (!xhr) return null;

        // htmx provides these on configRequest:
        // - d.verb (GET/POST/etc.)
        // - d.path
        // - d.parameters (object)
        // - d.headers (object)
        // - d.target (element)

        const elt = d.elt;
        const targetSel = elt?.getAttribute('hx-target') || elt?.dataset?.hxTarget || null;
        const swap = (elt?.getAttribute('hx-swap') || elt?.dataset?.hxSwap || null);

        return {
            verb: (d.verb || 'GET').toUpperCase(),
            path: d.path || '',
            parameters: d.parameters || {},
            headers: d.headers || {},
            target: targetSel || null,
            swap: swap || null
        };
    }

    function replayPendingIntent() {
        if (!pendingIntent || !window.htmx) return;

        const intent = pendingIntent;
        pendingIntent = null;

        // Avoiding doubling actions such as payments for now by restricting this to GET/HEAD 401s
        if (!['GET', 'HEAD'].includes(intent.verb)) {
            safeCall(window.hrSite?.showGlobalMessage,
                'Signed in. Please retry your last action.',
                5000
            );
            return;
        }

        const opts = {};
        if (intent.target) opts.target = intent.target;
        if (intent.swap) opts.swap = intent.swap;

        // Re-run the request
        window.htmx.ajax(intent.verb, intent.path, {
            ...opts,
            values: intent.parameters
        });
    }

    document.body.addEventListener('authSuccess', () => {
        requestAnimationFrame(() => {
            requestAnimationFrame(replayPendingIntent);
        });
    });

    // ------------------------------
    // 0) Global HTMX 401 handler -> authRequired
    // ------------------------------
    // Converts any HTMX 401 response into a single, app-level event.
    document.body.addEventListener('htmx:responseError', (event) => {
        if (!isHtmxUnauthorized(event)) return;

        const xhr = event?.detail?.xhr;
        pendingIntent = xhr._hrIntent || lastIntent || null;

        triggerAuthRequired({
            message: 'Please sign in.',
            open_drawer: true,
            focus: '#id_username',
            close_modal: true,
            will_retry: pendingIntent && ['GET', 'HEAD'].includes(pendingIntent.verb)
        });
    });

    document.body.addEventListener('htmx:configRequest', (event) => {
        const intent = buildIntentFromHtmxConfig(event);
        if (!intent) return;

        // attach to xhr for retrieval from responseError
        event.detail.xhr._hrIntent = intent;

        // rolling 'last intent' for debugging
        lastIntent = intent;
    });

    // ------------------------------
    // 0b) authRequired -> close modal, open drawer, focus username
    // ------------------------------
    document.body.addEventListener('authRequired', (event) => {
        const now = Date.now();
        if (now < _authRequiredLockUntil) return;
        _authRequiredLockUntil = now + 400;

        const detail = getDetail(event);

        // 1) Close modal
        if (detail.close_modal) {
            safeCall(window.hrSite?.hideModal);
        }

        // 2) Message (optional)
        const msg =
            (typeof detail === 'string' ? detail : null) ||
            detail.message ||
            detail.text ||
            '';
        if (msg) safeCall(window.hrSite?.showGlobalMessage, msg, detail.duration || 5000);

        // 3) Open drawer/sidebar
        if (detail.open_drawer) {
            if (typeof window.hrSite?.openDrawer === 'function') {
                safeCall(window.hrSite?.openDrawer);
            } else {
                document.body.classList.add('drawer-open');
            }
        }

        // 4) Focus username (after drawer anim / layout)
        const selector = detail.focus || '#id_username';

        const shouldAvoidStealingFocus = () => {
            const a = document.activeElement;
            if (!a) return false;
            const tag = (a.tagName || '').toLowerCase();
            return tag === 'input' || tag === 'textarea' || a .isContentEditable === true;
        };

        const focusNow = () => {
            if (shouldAvoidStealingFocus()) return;

            const el =
                document.querySelector(selector) ||
                document.getElementById(selector.replace(/^#/, ''));

            if (el && typeof el.focus === 'function') el.focus();
        };

        requestAnimationFrame(() => {
            requestAnimationFrame(focusNow);
        });
    });

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
    // 4) updateCart -> badge count(s)
    // ------------------------------
    document.body.addEventListener('updateCart', (event) => {
        const detail = getDetail(event);
        const count = Number(detail.item_count ?? detail.count ?? 0);

        // // Sidebar badge (authenticated panel)
        // const sidebarBadge = document.getElementById('cart-count');
        // if (sidebarBadge) {
        //     sidebarBadge.textContent = String(count);
        //     sidebarBadge.style.display = count > 0 ? 'inline-flex' : 'none';
        // }

        const floatingBadge = document.getElementById('floating-cart-count');
        if (floatingBadge) floatingBadge.textContent = String(count);
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
