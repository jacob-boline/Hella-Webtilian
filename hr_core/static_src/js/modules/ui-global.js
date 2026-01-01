// hr_site/static/hr_site/js/ui-global.js
//
// UI primitives (things that directly implement the behavior of UI components) -- modal, messages, drawer, etc.
//
// Also includes "Option A" landing-modal bootstrapping:
//   - /?modal=email_confirmed -> loads email confirmation success partial into modal
//   - /?modal=order_payment_result&order_id=...&t=... -> loads thank-you partial into modal
//
// Option B (recommended long-term; implementation notes):
//   Instead of encoding modal intent into query params, do a "hash route" + single loader:
//
//     1) Stripe return_url -> SITE_URL + "/#thank-you?order_id=123&t=SIGNED"
//     2) On page load, ui-global.js checks location.hash, parses #thank-you,
//        then sets hx-get on #modal-loader and triggers hr:loadModal.
//     3) After load, clean the hash with history.replaceState to avoid re-trigger on refresh.
//
//   Pros:
//     - avoids query-string collisions with other links
//     - keeps "modal routing" in one predictable place (hash)
//     - generally friendlier to caching/CDNs and "shareable" URLs
//
// Cart badge updates:
//   - The server is the authority. When order_payment_result clears cart, it should set:
//       HX-Trigger: {"updateCart": {"count": 0}}
//     events.js already listens for updateCart and updates both sidebar + floating badge.
//   - Client does NOT guess cart state; it only reacts to server events.

(function () {
    function initGlobalUI () {
        const modalEl = document.getElementById("modal");
        const modalContent = document.getElementById("modal-content");
        const modalMsg = document.getElementById("modal-message-box");

        const messageBar = document.getElementById("global-message-bar");
        const messageText = document.getElementById("global-message-content");

        const floatingCart = document.querySelector('.floating-cart-btn');

        function hideFloatingCart() {
            if (!floatingCart) return;
            floatingCart.classList.add('is-hidden');
        }

        function showFloatingCart() {
            if (!floatingCart) return;
            floatingCart.classList.remove('is-hidden');
        }

        function showGlobalMessage (text, timeoutMs = 1000) {
            if (!messageBar || !messageText) return;

            messageText.textContent = text || "";
            messageBar.classList.add("is-visible");

            window.setTimeout(() => {
                messageBar.classList.remove("is-visible");
            }, timeoutMs);
        }

        // function openModal () {
        //     if (!modalEl) return;
        //     modalEl.classList.remove("hidden");
        //     modalEl.setAttribute("aria-hidden", "false");
        //     document.body.style.overflow = "hidden";
        //
        //     hideFloatingCart();
        // }


        function openModal () {
            if (!modalEl) return;

            const scrollY = window.scrollY;
            modalEl.dataset.scrollY = scrollY;

            modalEl.classList.remove('hidden');
            modalEl.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
            window.scrollTo(0, scrollY);

            hideFloatingCart();
        }


        function hideModal () {
            if (!modalEl) return;

            const navOpenBtn = document.getElementById('nav-open-btn');
            if (navOpenBtn) navOpenBtn.classList.remove('hidden');

            const scrollY = parseInt(modalEl.dataset.scrollY || '0');

            modalEl.classList.add('hidden');
            modalEl.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';

            window.scrollTo(0, scrollY);

            if (modalContent) modalContent.replaceChildren();
            if (modalMsg) modalMsg.replaceChildren();

            showFloatingCart()
        }


        // function hideModal () {
        //     if (!modalEl) return;
        //
        //     const navOpenBtn = document.getElementById("nav-open-btn");
        //     if (navOpenBtn) navOpenBtn.classList.remove("hidden");
        //
        //     modalEl.classList.add("hidden");
        //     modalEl.setAttribute("aria-hidden", "true");
        //     document.body.style.overflow = "";
        //
        //     if (modalContent) modalContent.replaceChildren();
        //     if (modalMsg) modalMsg.replaceChildren();
        //
        //     showFloatingCart();
        // }

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

            // document.addEventListener('htmx:beforeSwap', (e) => {
            //     const target = e.target;
            //     if (!shouldReinit(target)) return;
            //
            //     const detail = e.detail || {};
            //
            //     if (isModalTarget(target)) {
            //         const scrollY = window.scrollY;
            //
            //         requestAnimationFrame(() => {
            //             if (window.scrollY !== scrollY) {
            //                 window.scrollTo(0, scrollY);
            //             }
            //         });
            //     }
            // });

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

            document.addEventListener("htmx:afterSettle", (e) => {
                const target = e.target;
                if (!target) return;
                if (!isModalSwapTarget(target)) return;
                modalEl.classList.remove("is-swapping");
            });
        }

        // ------------------------------
        // Post-purchase CTA dismiss animation hook (HTMX)
        // ------------------------------
        // Note: We add a one-shot bypass flag on the button so re-triggering the click
        // doesn't get re-intercepted and loop forever.
        document.body.addEventListener("htmx:beforeRequest", (e) => {
            const src = e.target;
            const btn = src?.closest?.("[data-cta-dismiss]");
            if (!btn) return;

            // bypass for the re-fired click
            if (btn.dataset.ctaDismissBypass === "1") {
                delete btn.dataset.ctaDismissBypass;
                return;
            }

            const wrap = btn.closest("#post-purchase-account");
            if (!wrap) return;

            wrap.classList.add("is-dismissing");

            // delay the request just a hair
            btn.dataset.ctaDismissBypass = "1";
            e.preventDefault();

            window.setTimeout(() => {
                if (!window.htmx) return;
                window.htmx.trigger(btn, "click");
            }, 200);
        }, true);

        // ------------------------------
        // Drawer navigation
        // ------------------------------
        function initDrawer () {
            const drawer = document.getElementById("drawer-navigation");
            const openBtn = document.getElementById("nav-open-btn");
            const closeBtn = document.getElementById("nav-close-btn");

            if (!drawer || !openBtn) return;

            const openDrawer = () => {
                drawer.classList.add("show");
                openBtn.classList.add("hidden");
            };

            const closeDrawer = () => {
                drawer.classList.remove("show");
                openBtn.classList.remove("hidden");
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

            let hxGet = null;

            if (modal === "email_confirmed") {
                hxGet = "/shop/checkout/email-confirmation/success/";
            } else if (modal === "order_payment_result") {
                const orderId = (params.get("order_id") || "").trim();
                const token = (params.get("t") || "").trim();
                if (!orderId || !token) return false;

                hxGet = `/shop/order/${encodeURIComponent(orderId)}/payment-result/?t=${encodeURIComponent(token)}`;
            } else {
                return true;  // unknown modal key -> don't do anything (but also don't keep re-trying)
            }

            loader.setAttribute("hx-get", hxGet);
            window.htmx.process(loader);
            window.htmx.trigger(loader, "hr:loadModal");

            // Clean the URL so refresh doesn't re-open.
            // (Preserve pathname + hash only; drop query string.)
            window.setTimeout(() => {
                try {
                    const cleanParams = new URLSearchParams(window.location.search);
                    cleanParams.delete("modal");
                    cleanParams.delete("order_id");
                    cleanParams.delete("t");

                    const qs = cleanParams.toString();
                    const clean =
                        window.location.pathname +
                        (qs ? `?${qs}` : "") +
                        window.location.hash;
                    window.history.replaceState({}, "", clean);
                } catch (e) { }
            }, 0);
            return true;
        }

        function tryBootstrapLandingModal () {
            return bootstrapLandingModalFromUrl();
        }

        // Try immediately; if HTMX isn't ready, try once on htmx:load + one small retry.
        if (!tryBootstrapLandingModal()) {
            document.addEventListener("htmx:load", () => tryBootstrapLandingModal(), { once: true });
            window.setTimeout(tryBootstrapLandingModal, 50);
        }

        initDrawer();

        // Expose a small API surface
        window.hrSite = window.hrSite || {};
        window.hrSite.hideModal = hideModal;
        window.hrSite.showGlobalMessage = showGlobalMessage;

        window.hrModal = { open: openModal, close: hideModal };
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initGlobalUI);
    } else {
        initGlobalUI();
    }
})();
