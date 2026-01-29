// hr_core/static_src/js/modules/auto-advance.js

/**
 * Auto-advance utility:
 * Finds nodes with [data-hr-auto-advance] and schedules a delayed HTMX swap.
 *
 * Generic enough to reuse in other modal states:
 * - delayed transitions (success -> next step)
 * - soft redirects inside modal
 *
 * Cancellation:
 * - By default cancels if user interacts inside the closest modal content area.
 */

function parseList (val) {
    if (!val) return [];
    return String(val)
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);
}

function isModalOpen () {
    const modal = document.getElementById('modal');
    return !!modal && !modal.classList.contains('hidden') && modal.getAttribute('aria-hidden') !== 'true';
}

function defaultTargetEl (selector) {
    if (!selector) return null;
    return document.querySelector(selector);
}

export function initAutoAdvance (root = document) {
    const container = root || document;
    const nodes = container.querySelectorAll?.('[data-hr-auto-advance]') || [];
    if (!nodes.length) return;

    nodes.forEach((node) => {
        // idempotent per node
        if (node._hrAutoAdvanceInitDone) return;
        node._hrAutoAdvanceInitDone = true;

        const delayMs = parseInt(node.getAttribute('data-delay-ms') || '0', 10) || 0;
        const nextUrl = node.getAttribute('data-next-url');
        const targetSel = node.getAttribute('data-target') || '#modal-content';
        const swap = node.getAttribute('data-swap') || 'innerHTML';
        const cancelOn = parseList(node.getAttribute('data-cancel-on')) || ['click', 'keydown', 'submit'];

        if (!nextUrl || delayMs <= 0) return;

        // Determine the interaction zone where cancel events apply:
        // Prefer closest modal, else fall back to document.
        const modal = node.closest?.('#modal');
        const cancelZone = modal || document;

        let cancelled = false;
        let timerId = null;

        function cancel () {
            cancelled = true;
            if (timerId) window.clearTimeout(timerId);
            timerId = null;

            // Remove listeners once cancelled to avoid leaks
            cancelOn.forEach((evt) => cancelZone.removeEventListener(evt, cancel, true));
        }

        // Cancel if user does anything in the cancel zone
        cancelOn.forEach((evt) => cancelZone.addEventListener(evt, cancel, true));

        timerId = window.setTimeout(() => {
            if (cancelled) return;

            // If this was meant for the modal, don't resurrect closed modals.
            if (targetSel === '#modal-content' && !isModalOpen()) return;

            const targetEl = defaultTargetEl(targetSel);
            if (!targetEl) return;

            if (!window.htmx) {
                console.warn('[auto-advance] htmx not available, cannot load:', nextUrl);
                return;
            }

            // Perform the swap
            window.htmx.ajax('GET', nextUrl, {
                target: targetSel,
                swap,
            });

            // After firing once, stop listening to cancellations
            cancel();
        }, delayMs);
    });
}
