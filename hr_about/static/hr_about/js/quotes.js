// hr_about/static/hr_about/js/quotes.js

export function initAboutQuotes(root = document) {
    const container = root.querySelector('#about-quotes');
    if (!container) { return; }

    const rotator = container.querySelector('.about-quote-rotator');
    const textEl = rotator?.querySelector('.quote-text');
    const sourceEl = rotator?.querySelector('.quote-source');
    const dataItems = Array.from(
        container.querySelectorAll('.about-quote-data li')
    );

    if (!rotator || !textEl || !sourceEl || dataItems.length === 0) { return; }

    const quotes = dataItems.map(item => ({
        text: item.dataset.text || '',
        source: item.dataset.source || ''
    }));

    let index = 0;
    const ROTATE_MS = 8000;

    function showQuote(i) {
        const q = quotes[i];
        if (!q) { return; }

        textEl.textContent = q.text;
        sourceEl.textContent = q.source ? `- ${q.source}` : '';
    }

    function nextQuote() {
        index = (index + 1) % quotes.length;
        showQuote(index);
    }

    showQuote(0);

    if (rotator._quoteIntervalId) {
        clearInterval(rotator._quoteIntervalId);
    }

    rotator._quoteIntervalId = setInterval(nextQuote, ROTATE_MS);
}