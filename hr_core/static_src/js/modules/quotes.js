// hr_core/static_src/js/modules/quotes.js

export function initQuotes(root = document) {
    const container = root.querySelector('#about-quotes');
    if (!container) return;

    if (container._quotesInstance?.destroy) {
        container._quotesInstance.destroy();
    }

    const rotator = container.querySelector('.about-quote-rotator');
    if (!rotator) return;

    const textEl = rotator.querySelector('.quote-text');
    const sourceEl = rotator.querySelector('.quote-source');
    const items = container.querySelectorAll('.about-quote-data li');

    if (!textEl || !items.length) return;

    let index = 0;
    let intervalId = null;

    function render(i) {
        const item = items[i];
        if (!item) return;

        const text = item.dataset.text || '';
        const source = item.dataset.source || '';

        textEl.textContent = `"${text}"`;
        if (sourceEl) sourceEl.textContent = source ? `— ${source}` : '';
    }

    render(0);

    if (items.length > 1) {
        const intervalMs = 3456;
        intervalId = window.setInterval(() => {
            index = (index + 1) % items.length;
            render(index);
        }, intervalMs);
    }

    const instance = {
        destroy() {
            if (intervalId) window.clearInterval(intervalId);
        }
    };

    container._quotesInstance = instance;
    return instance;
}
