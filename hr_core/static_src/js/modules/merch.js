// hr_core/static_src/js/modules/merch.js

export function initMerch(root = document) {
    // One-time init for global delegated listeners
    if (document.body._merchInitDone) return;
    document.body._merchInitDone = true;

    // Mark the clicked thumbnail as active
    document.addEventListener('click', (event) => {
        const btn = event.target.closest('button.merch-img, .merch-actions .card-btn.btn-blue');
        if (!btn) return;

        const card = btn.closest('.merch-card');
        if (!card) return;

        document.querySelectorAll('.merch-thumb-img.is-active, .modal-image.is-active')
            .forEach(el => el.classList.remove('is-active'));

        const thumb = card.querySelector('.merch-thumb-img');
        if (thumb) thumb.classList.add('is-active');
    });

    function openModal() {
        const modal = document.getElementById('modal');
        if (!modal) return;
        modal.classList.remove('hidden');
    }

    // When HTMX swaps the modal content in:
    document.addEventListener('htmx:afterSwap', (event) => {
        const detail = event.detail;
        if (!detail || !detail.target) return;
        if (!detail.target.closest('#modal')) return;

        const modal = document.getElementById('modal');
        if (!modal) return;

        const thumb = document.querySelector('.merch-thumb-img.is-active');
        const modalImg = modal.querySelector('.modal-image');

        if (!document.startViewTransition || !thumb || !modalImg) {
            openModal();
            return;
        }

        document.startViewTransition(() => {
            thumb.classList.remove('is-active');
            modalImg.classList.add('is-active');
            openModal();
        });
    });
}
