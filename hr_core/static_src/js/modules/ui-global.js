// hr_core/static_src/js/modules/ui-global.js

(function () {
    function initGlobalUI () {

        // GUARD - double init
        window.hrSite = window.hrSite || {};
        if (window.hrSite.__globalUiInitialized) return;
        window.hrSite.__globalUiInitialized = true;

        const modalEl      = document.getElementById("modal");
        const modalContent = document.getElementById("modal-content");
        const modalMsg     = document.getElementById("modal-message-box");
        const messageBar   = document.getElementById("global-message-bar");
        const messageText  = document.getElementById("global-message-content");
        const floatingCart = document.querySelector('.floating-cart-btn');

        let _drawerScrollY = 0;

        function hideFloatingCart () {
            if (!floatingCart) return;
            floatingCart.classList.add('is-hidden');
        }

        function showFloatingCart () {
            if (!floatingCart) return;
            floatingCart.classList.remove('is-hidden');
        }

        function showGlobalMessage (text, timeoutMs = 1000) {
            if (!messageBar || !messageText) return;

            messageText.textContent = text || "";

            if (messageText.textContent !== "") {

                messageBar.classList.add("is-visible");
                window.setTimeout(() => {
                    messageBar.classList.remove("is-visible");
                }, timeoutMs);
            }
        }

        function refreshScrollOnModalClose () {
            const reflow   = window.hrSite?.reflowParallax;
            const syncWipe = window.hrSite?.syncActiveWipe;
            const banner   = window.hrSite?.banner;

            // Let scroll restore land + any viewport resize happen first
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    if (typeof reflow === "function") reflow();
                    if (typeof syncWipe === "function") syncWipe();
                    if (typeof banner?.setBannerState === "function") banner.setBannerState(window.scrollY || 0);
                    if (typeof banner?.updateFade === "function") banner.updateFade();
                });
            });
        }

        function openModal () {
            if (!modalEl) return;

            const scrollY = window.scrollY;
            modalEl.dataset.scrollY = scrollY;

            modalEl.classList.remove('hidden');
            modalEl.setAttribute('aria-hidden', 'false');

            document.body.classList.add('modal-open');
            document.body.style.top = `-${scrollY}px`;

            hideFloatingCart();
        }

        function hideModal () {
            if (!modalEl) return;

            const navOpenBtn = document.getElementById('nav-open-btn');
            if (navOpenBtn) navOpenBtn.classList.remove('hidden');

            const scrollY = parseInt(modalEl.dataset.scrollY || '0', 10);

            modalEl.classList.add('hidden');
            modalEl.setAttribute('aria-hidden', 'true');

            // unfreeze body
            document.body.classList.remove('modal-open');
            document.body.style.top = '';

            // IMPORTANT: restore scroll synchronously, before the next paint
            window.scrollTo(0, scrollY);

            // fix parallax/wipes once the DOM has settled for this frame
            refreshScrollOnModalClose();

            if (modalContent) modalContent.replaceChildren();
            if (modalMsg) modalMsg.replaceChildren();

            showFloatingCart();
        }

        // ------------------------------
        // Modal close behavior
        // ------------------------------
        if (modalEl) {
            document.addEventListener("click", (e) => {
                const backdrop = e.target.closest(".modal-backdrop");
                const closer = e.target.closest("[data-modal-close]");
                if (!backdrop && !closer) return;

                e.preventDefault();
                hideModal();
            });

            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape" && !modalEl.classList.contains("hidden")) {
                    hideModal();
                }
            });
        }

        // ------------------------------
        // Modal open + swap guards (HTMX)
        // ------------------------------
        if (modalEl && (modalContent || modalMsg)) {
            function isModalSwapTarget (target) {
                return (
                    target === modalContent ||
                    target === modalMsg ||
                    target?.id === "modal-content" ||
                    target?.id === "modal-message-box"
                );
            }

            document.addEventListener("htmx:afterSwap", (e) => {
                const target = e.target;
                if (!target) return;
                if (!isModalSwapTarget(target)) return;
                openModal();
            });

            document.addEventListener("htmx:beforeSwap", (e) => {
                const target = e.target;
                if (!target) return;
                if (!isModalSwapTarget(target)) return;

                const detail = e.detail || {};
                const xhr = detail.xhr;

                if (detail.shouldSwap === false) return;

                const isEmpty =
                    (xhr && xhr.status === 204) ||
                    !detail.serverResponse ||
                    detail.serverResponse.trim() === "";

                if (isEmpty) {
                    // cancel swap into modal targets for empty responses
                    detail.shouldSwap = false;
                    return;
                }

                modalEl.classList.add("is-swapping");
            });

            /* fires stashed triggers (showMessage) after modal content settles */
            document.addEventListener('htmx:afterSettle', (e) => {
                const target = e.target;
                if (!target || target.id !== 'modal-content') return;

                const loader = document.getElementById('modal-loader');
                const h = window.htmx;
                if (!loader || !h) return;

                const raw = loader.dataset.afterSwapTriggers;
                if (!raw) return;

                delete loader.dataset.afterSwapTriggers;

                let triggers;
                try {
                    triggers = JSON.parse(raw);
                } catch {
                    return;
                }
                if (!triggers || typeof triggers !== 'object') return;

                for (const [name, payload] of Object.entries(triggers)) {
                    h.trigger(document.body, name, payload);
                }
            });

        }

        // ------------------------------
        // Post-purchase CTA dismiss animation hook (HTMX)
        // ------------------------------
        document.body.addEventListener("htmx:beforeSwap", (e) => {
            const src = e.target;
            const btn = src?.closest?.("[data-cta-dismiss]");

            if (!btn) return;

            const wrap = btn.closest("#post-purchase-account");
            if (!wrap) return;

            // Add animation class - htmx handles the swap after this event
            wrap.classList.add("is-dismissing");
        }, true);


        document.body.addEventListener("htmx:afterSettle", async (e) => {
            const target = e.target;
            if (!target) return;

            const inBulletin = target.id === "bulletin-root" || target.closest?.("#bulletin-root");
            if (!inBulletin) return;

            if (document.body.classList.contains("modal-open") || document.body.classList.contains("drawer-open")) return;

            // decode any imgs in the swapped chunk to avoid late layout jump
            const imgs = target.querySelectorAll?.("img") || [];
            await Promise.all(Array.from(imgs).map(img => img.decode ? img.decode().catch(() => {
            }) : Promise.resolve()));

            // settle pass
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    window.hrSite?.reflowParallax?.();
                    window.hrSite?.syncActiveWipe?.();
                    window.dispatchEvent(new Event("scroll"));
                });
            });
        });

        // ------------------------------
        // Drawer navigation
        // ------------------------------
        function initDrawer () {
            const drawer = document.getElementById("drawer-navigation");
            const openBtn = document.getElementById("nav-open-btn");
            const closeBtn = document.getElementById("nav-close-btn");

            if (!drawer || !openBtn) return;

            const openDrawer = () => {

                // Delay load of BC player until the sidebar is first opened
                const bandcamp = drawer.querySelector('iframe[data-src]');
                if (bandcamp) {
                    bandcamp.src = bandcamp.dataset.src;
                    delete bandcamp.dataset.src;
                }

                const isMobile = window.matchMedia("(max-width: 767.98px)").matches;
                const isOpen = drawer.classList.contains('show');

                if (!isOpen) {
                    drawer.classList.add("show");
                    openBtn.classList.add("hidden");
                }

                if (isMobile) {
                    // ensure mobile lock is applied even if drawer was already open
                    if (!document.body.classList.contains("drawer-open")) {
                        _drawerScrollY = window.scrollY || 0;
                        document.body.classList.add("drawer-open");
                        document.body.style.top = `-${_drawerScrollY}px`;
                    }
                }
            };

            const closeDrawer = () => {
                const isMobile = window.matchMedia("(max-width: 767.98px)").matches;
                drawer.classList.remove("show");
                openBtn.classList.remove("hidden");
                if (isMobile) {
                    document.body.classList.remove("drawer-open");
                    document.body.style.top = "";
                    window.scrollTo(0, _drawerScrollY);
                }
            };

            openBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                openDrawer();
            });

            if (closeBtn) {
                closeBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    closeDrawer();
                });
            }

            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape") closeDrawer();
            });

            document.addEventListener("click", (e) => {
                if (!drawer.classList.contains("show")) return;
                const clickedInside = drawer.contains(e.target);
                const clickedOpenBtn = openBtn.contains(e.target);
                if (!clickedInside && !clickedOpenBtn) closeDrawer();
            });
        }

        // ---------------------------------------- //
        // Landing modal bootstrap (query params)   //
        // ---------------------------------------- //
        function bootstrapLandingModalFromUrl () {
            const loader = document.getElementById("modal-loader");
            if (!loader) return false;

            const params = new URLSearchParams(window.location.search);
            const modal = (params.get("modal") || "").trim();
            if (!modal) return false;

            if (!window.htmx) return false;

            const modalUrl = (params.get("modal_url") || "").trim();

            const routes = {

                email_confirmed: () => modalUrl || "/shop/checkout/email-confirmation/success/",

                order_payment_result: () => {
                    const token = (params.get("t") || "").trim();
                    if (!token) return null;
                    return `/shop/order/payment-result/?t=${encodeURIComponent(token)}`;
                },

                account_signup_confirm: () => {
                    const token = (params.get("t") || "").trim();
                    if (!token) return null;
                    return `/access/account/signup/confirm/?t=${encodeURIComponent(token)}`;
                },

                email_change: () => modalUrl || null,

                password_reset: () => modalUrl || null

            };

            const build = routes[modal];
            const hxGet = build ? build() : null;

            if (hxGet === null) return true; // exit on missing param

            window.htmx.trigger(document.body, 'loadModal', {hxGet});

            window.setTimeout(() => {
                try {
                    const cleanParams = new URLSearchParams(window.location.search);
                    ["modal", "order_id", "t", "u", "modal_url", "handoff"].forEach(k => cleanParams.delete(k));

                    const qs = cleanParams.toString();
                    const clean = window.location.pathname + (qs ? `?${qs}` : "") + window.location.hash;
                    window.history.replaceState({}, "", clean);
                } catch (e) {
                }
            }, 0);

            return true;
        }


        function tryBootstrapLandingModal () {
            return bootstrapLandingModalFromUrl();
        }

        if (!tryBootstrapLandingModal()) {
            document.addEventListener("htmx:load", () => tryBootstrapLandingModal(), {once: true});
        }


        initDrawer();

        // Expose a small API surface
        window.hrSite = window.hrSite || {};
        window.hrSite.hideModal = hideModal;
        window.hrSite.showGlobalMessage = showGlobalMessage;

        window.hrSite.cart = window.hrSite.cart || {};
        window.hrSite.cart.show = showFloatingCart;
        window.hrSite.cart.hide = hideFloatingCart;

        window.hrModal = {open: openModal, close: hideModal};

        showFloatingCart();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initGlobalUI);
    } else {
        initGlobalUI();
    }
})();
