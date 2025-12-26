// hr_site/static/hr_site/js/ui-global.js
//
// UI primitives (things that directly implement that bavior of UI components) -- modal, messages, drawer,etc.

(function () {
    function initGlobalUI() {
        const modalEl = document.getElementById('modal');
        const modalContent = document.getElementById('modal-content');
        const modalMsg = document.getElementById('modal-message-box');

        const messageBar = document.getElementById('global-message-bar');
        const messageText = document.getElementById('global-message-content');

        function showGlobalMessage(text, timeoutMs = 1000) {
            if (!messageBar || !messageText) return;

            messageText.textContent = text || '';
            messageBar.classList.add('is-visible');

            window.setTimeout(() => {
                messageBar.classList.remove('is-visible');
            }, timeoutMs);
        }

        function openModal() {
            if (!modalEl) return;
            modalEl.classList.remove('hidden');
            modalEl.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
        }

        function hideModal() {
            if (!modalEl) return;

            const navOpenBtn = document.getElementById('nav-open-btn');
            if (navOpenBtn) navOpenBtn.classList.remove('hidden');

            modalEl.classList.add('hidden');
            modalEl.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';

            if (modalContent) modalContent.replaceChildren();
            if (modalMsg) modalMsg.replaceChildren();
        }
        
        // Backdrop close
        if (modalEl) {
            document.addEventListener('click', (e) => {
                const backdrop = e.target.closest('.modal-backdrop');
                const closer = e.target.closest('[data-modal-close]');
                if (!backdrop && !closer) return;

                e.preventDefault();
                hideModal();
            });

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && !modalEl.classList.contains('hidden')) {
                    hideModal();
                }
            });
        }

        // Modal open on swap
        if (modalEl && (modalContent || modalMsg)) {
            function isModalSwapTarget(target) {
                // HTMX event target is the swap target element
                return (
                    target === modalContent ||
                    target === modalMsg ||
                    target?.id === 'modal-content' ||
                    target?.id === 'modal-message-box'
                );
            }

            document.addEventListener('htmx:afterSwap', (e) => {
                const target = e.target;
                if (!target) return;

                // Only open when modal's swap targets get content
                if (!isModalSwapTarget(target)) return;

                openModal();
            });

            // Cancel swap for empty/204 responses ONLY when swapping into modal-content/message-box
            document.addEventListener('htmx:beforeSwap', (e) => {
                const target = e.target;
                if (!target) return;

                if (!isModalSwapTarget(target)) return;

                const detail = e.detail || {};
                const xhr = detail.xhr;

                // If swap is already disabled (hx-swap="none"), don't touch anything
                if (detail.shouldSwap === false) return;

                const isEmpty =
                    (xhr && xhr.status === 204) ||
                    !detail.serverResponse ||
                    detail.serverResponse.trim() === '';

                if (isEmpty) {
                    // Important: cancel the swap, but DON'T auto-close the modal
                    // Empty responses can be legit "no change" signals.
                    detail.shouldSwap = false;
                    return;
                }

                modalEl.classList.add('is-swapping');
            });

            document.addEventListener('htmx:afterSettle', (e) => {
                const target = e.target;
                if (!target) return;

                if (!isModalSwapTarget(target)) return;
                modalEl.classList.remove('is-swapping');
            });
        }


        // Drawer navigation
        function initDrawer() {
            const drawer = document.getElementById('drawer-navigation');
            const openBtn = document.getElementById('nav-open-btn');
            const closeBtn = document.getElementById('nav-close-btn');

            if (!drawer || !openBtn) return;

            const openDrawer = () => {
                drawer.classList.add('show');
                openBtn.classList.add('hidden');
            };

            const closeDrawer = () => {
                drawer.classList.remove('show');
                openBtn.classList.remove('hidden');
            };

            openBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openDrawer();
            });

            if (closeBtn) {
                closeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    closeDrawer();
                });
            }

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') closeDrawer();
            });

            document.addEventListener('click', (e) => {
                if (!drawer.classList.contains('show')) return;
                const clickedInside = drawer.contains(e.target);
                const clickedOpenBtn = openBtn.contains(e.target);
                if (!clickedInside && !clickedOpenBtn) closeDrawer();
            });
        }

        initDrawer();

        window.hrSite = window.hrSite || {};
        window.hrSite.hideModal = hideModal;
        window.hrSite.showGlobalMessage = showGlobalMessage;

        window.hrModal = { open: openModal, close: hideModal };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGlobalUI);
    } else {
        initGlobalUI();
    }
})();
