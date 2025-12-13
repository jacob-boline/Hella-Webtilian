// hr_site/static/hr_site/js/ui-global.js

(function () {
    function initGlobalUI () {
        // ------------------------------
        // Element handles
        // ------------------------------
        const modalEl = document.getElementById('modal');
        const modalContent = document.getElementById('modal-content');
        const modalMsg = document.getElementById('modal-message-box');

        const messageBar = document.getElementById('global-message-bar');
        const messageText = document.getElementById('global-message-content');

        // ------------------------------
        // Global message bar
        // ------------------------------
        function showGlobalMessage (text, timeoutMs = 1000) {
            if (!messageBar || !messageText) return;

            messageText.textContent = text || '';
            messageBar.classList.add('is-visible');

            window.setTimeout(() => {
                messageBar.classList.remove('is-visible');
            }, timeoutMs);
        }

        // ------------------------------
        // Modal helpers
        // ------------------------------
        function openModal () {
            if (!modalEl) return;
            modalEl.classList.remove('hidden');
            modalEl.setAttribute('aria-hidden', 'false');
            // Lock scroll behind modal
            document.body.style.overflow = 'hidden';
        }

        function hideModal () {
            if (!modalEl) return;

            const navOpenBtn = document.getElementById('nav-open-btn');
            if (navOpenBtn) navOpenBtn.classList.remove('hidden');

            modalEl.classList.add('hidden');
            modalEl.setAttribute('aria-hidden', 'true');
            // Restore scroll
            document.body.style.overflow = '';

            if (modalContent) {
                modalContent.replaceChildren();
            }
            if (modalMsg) {
                modalMsg.replaceChildren();
            }
        }

        // ------------------------------
        // Modal: click / escape
        // ------------------------------
        if (modalEl) {
            // Backdrop or [data-modal-close] closes modal
            document.addEventListener('click', (e) => {
                const backdrop = e.target.closest('.modal-backdrop');
                const closer = e.target.closest('[data-modal-close]');
                if (!backdrop && !closer) return;

                e.preventDefault();
                hideModal();
            });

            // ESC closes modal (if visible)
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && !modalEl.classList.contains('hidden')) {
                    hideModal();
                }
            });
        }

        // ------------------------------
        // Modal: HTMX integration
        // ------------------------------
        if (modalEl && modalContent) {
            // When HTMX swaps into modal content/message box → open modal
            document.addEventListener('htmx:afterSwap', (e) => {
                const target = e.target;
                if (!target) return;

                if (
                    target === modalContent ||
                    target === modalMsg ||
                    target.id === 'modal-content' ||
                    target.id === 'modal-message-box'
                ) {
                    openModal();
                }
            });

            // If server responds with 204 or empty for #modal-content, close & cancel swap
            document.addEventListener('htmx:beforeSwap', (e) => {
                const target = e.target;
                if (target !== modalContent) return;

                const detail = e.detail || {};
                const xhr = detail.xhr;

                const isEmpty =
                    (xhr && xhr.status === 204) ||
                    !detail.serverResponse ||
                    detail.serverResponse.trim() === '';

                if (isEmpty) {
                    hideModal();
                    detail.shouldSwap = false;
                }
            });
        }

        // ------------------------------
        // HTMX custom events from HX-Trigger
        // ------------------------------
        document.addEventListener('passwordChanged', (e) => {
            const detail = e.detail || {};
            const msg = detail.message || detail.text || 'Password updated.';
            hideModal();
            showGlobalMessage(msg, 5000);
        });

        document.body.addEventListener('showMessage', (event) => {
            // const detail = e.detail || {};
            // const msg =
            //   detail.message ||
            //   detail.text ||
            //   (typeof detail === 'string' ? detail : '') ||
            //   '';
            console.log('showMessage received event:', event);
            const msg = event.detail.message;
            if (msg) {
                showGlobalMessage(msg, 5000);
            }
        });


        document.body.addEventListener('htmx:afterSwap', function (event) {
            // Only react when the modal content is what got swapped
            if (event.target.id === 'modal-content') {
                const modal = document.getElementById('modal');
                const drawer = document.getElementById('drawer-navigation');

                if (modal) {
                    modal.classList.remove('hidden');
                    modal.setAttribute('aria-hidden', 'false');
                }

                if (drawer) {
                    drawer.classList.remove('show');
                }
            }
        });

        function initCheckoutDetailsForm(root) {
            const container = root || document;
            const form = container.getElementById
                ? container.getElementById('checkout-details-form')
                : container.querySelector('#checkout-details-form');

            if (!form) return;

            const buildingSelect = form.querySelector('#id_building_type');
            const unitGroup = form.querySelector('#unit-group');

            if (!buildingSelect || !unitGroup) return;

            const showFor = ['apartment', 'business', 'other'];

            function updateUnitVisibility () {
                const val = buildingSelect.value;
                const unitInput = unitGroup.querySelector('input');

                if (showFor.indexOf(val) >= 0) {
                    unitGroup.style.visibility = 'visible';
                }
                else {
                    unitGroup.style.visibility = 'hidden';
                    if (unitInput) unitInput.value = '';
                }
            }

            buildingSelect.addEventListener('change', updateUnitVisibility);
            updateUnitVisibility();
        }

        document.body.addEventListener('htmx:afterSwap', function (event) {
            if (event.target.id === 'modal-content' || event.target.querySelector('#checkout-details-form')) {
                initCheckoutDetailsForm(event.target);
            }
        });


        // ------------------------------
        // Drawer navigation
        // ------------------------------
        function initDrawer () {
            const drawer = document.getElementById('drawer-navigation');
            const openBtn = document.getElementById('nav-open-btn');
            const closeBtn = document.getElementById('nav-close-btn');

            if (!drawer || !openBtn) {
                console.warn('Drawer nav: missing #drawer-navigation or #nav-open-btn');
                return;
            }

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

            // ESC closes drawer
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    closeDrawer();
                }
            });

            // Click outside closes drawer
            document.addEventListener('click', (e) => {
                if (!drawer.classList.contains('show')) return;
                const clickedInside = drawer.contains(e.target);
                const clickedOpenBtn = openBtn.contains(e.target);
                if (!clickedInside && !clickedOpenBtn) {
                    closeDrawer();
                }
            });
        }

        initDrawer();

        // ------------------------------
        // Public API
        // ------------------------------
        window.hrSite = window.hrSite || {};
        window.hrSite.hideModal = hideModal;
        window.hrSite.showGlobalMessage = showGlobalMessage;

        // Optional small helper alias
        window.hrModal = {
            open: openModal,
            close: hideModal,
        };
    }

    // Ensure DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGlobalUI);
    } else {
        initGlobalUI();
    }
})();
