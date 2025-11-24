// hr_site/static/hr_site/js/main.js

(function () {
    const modalEl = document.getElementById('modal');
    const modalContent = document.getElementById('modal-content');
    const messageBar = document.getElementById('global-message-bar');
    const messageText = document.getElementById('global-message-text');

    function openModal() {
        if (!modalEl) { return; }
        modalEl.classList.remove('hidden');
        modalEl.setAttribute('aria-hidden', 'false');
        modalEl.focus?.();
    }

    function hideModal() {
        if (!modalEl) { return; }
        modalEl.classList.add('hidden');
        modalEl.setAttribute('aria-hidden', 'true');

        if (modalContent) {
            modalContent.innerHTML = '';
        }
    }

    function showGlobalMessage(text, timeoutMs = 1000) {
        if (!messageBar || !messageText) { return; }

        messageText.textContent = text || '';
        messageBar.classList.add('is-visible');

        window.setTimeout(() => {
            messageBar.classList.remove('is-visible');
        }, timeoutMs);
    }

    // --------------------------------------------------
    // Hook into HTMX swaps:
    // - When we swap into #modal-content, open the modal
    // --------------------------------------------------

    document.body.addEventListener('htmx:afterSwap', (e) => {
        const target = e.target;
        if (!target || !modalEl) { return; }

        if (target.id === 'modal-content' || (modalContent && modalContent.contains(target))) {
            openModal();
        }
    });

    // --------------------------------------------------
    // Click outside / close button
    // --------------------------------------------------
    document.addEventListener('click', (e) => {
        if (!modalEl) { return; }
        const isBackdrop = e.target.matches('.modal-backdrop, #modal .modal-backdrop');
        const isCloseBtn = e.target.closest('[data-modal-close]');

        if (isBackdrop || isCloseBtn) {
            hideModal();
        }
    });

    // --------------------------------------------------
    // Escape key closes modal
    // --------------------------------------------------
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideModal();
        }
    });

    // --------------------------------------------------
    // HTMX custom events from HX-Trigger headers
    // - passwordChanged
    // - showMessage
    // --------------------------------------------------
    document.body.addEventListener('passwordChanged', (e) => {
        const detail = event.detail || {};
        const msg = detail.message || detail.text || 'Password updated.';
        hideModal();
        showGlobalMessage(msg, 5000);
    });

    document.body.addEventListener('showMessage', (e) => {
        const detail = event.detail || {};
        const msg = detail.message || detail.text || (typeof detail === 'string' ? detail : '') || '';
        if (msg) { showGlobalMessage(msg, 5000);}
    });


    document.addEventListener('DOMContentLoaded', () => {
        const drawer = document.getElementById('drawer-navigation');
        const openBtn = document.getElementById('nav-open');
        const closeBtns = drawer ? drawer.querySelectorAll('[data-drawer-close]') : [];

        if (!drawer || !openBtn) {
            console.warn('Drawer nav: missing #drawer-navigation or #nav-open');
            return;
        }

        const openDrawer = () => drawer.classList.add('show');
        const closeDrawer = () => drawer.classList.remove('show');
        const toggleDrawer = () => drawer.classList.toggle('show');

        openBtn.addEventListener('click', toggleDrawer);

        closeBtns.forEach(btn => {
            btn.addEventListener('click', closeDrawer);
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeDrawer();
            }
        });
    });


    window.hrSite = window.hrSite || {};
    window.hrSite.hideModal = hideModal;
    window.hrSite.showGlobalMessage = showGlobalMessage;


})();