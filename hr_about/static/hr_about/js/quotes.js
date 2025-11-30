// hr_about/static/hr_about/js/quotes.js

export function initAboutQuotes(root = document) {

    const container = root.querySelector('#about-quotes');
    if (!container) return;

    const rotator = container.querySelector('.about-quote-rotator');
    if (!rotator) return;

    const textEl = rotator?.querySelector('.quote-text');
    const sourceEl = rotator?.querySelector('.quote-source');
    const items = container.querySelectorAll('.about-quote-data li');

    if (!textEl || !items.length) return;

    let index = 0;

    function render (i) {
        const item = items[i];
        if (!item) return;

        const text = item.dataset.text || '';
        const source = item.dataset.source || '';

        textEl.textContent = text;

        if (sourceEl) {
            sourceEl.textContent = source ? `— ${source}` : '';
        }
    }

    render(0);

    if (items.length > 1) {
        const intervalMs = 8000;
        setInterval(() => {
            index = (index + 1) % items.length;
            render(index);
        }, intervalMs);
    }
}

/*------------------------------------------
            AUTO-INITIALIZER
 ------------------------------------------*/

function tryInitQuotes(root = document) {
    try {
        initAboutQuotes(root);
        if (window.hrSite && typeof window.hrSite.reflowParallax === 'function') {
            window.hrSite.reflowParallax();
        } else {
            alert('Failed to call reflowParallax from quotes');
        }
    } catch (err) {
        console.error('Quotes init error.', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    tryInitQuotes(document);
});

document.addEventListener('htmx:afterSwap', (e) => {
    if (e.target?.id === 'about-quotes-container' || e.target?.closest?.('#about-quotes-container')) {
        tryInitQuotes(e.target);
    }
});
