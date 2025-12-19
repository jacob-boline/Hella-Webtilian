// hr_core/static/hr_core/js/meta-init.js

import { initCarousel } from './modules/carousel.js';
import { initQuotes } from './modules/quotes.js';
import { initMerch } from './modules/merch.js';
import { initCheckout } from './modules/checkout.js';
import { initBulletin } from './modules/bulletin.js';
import { initUIText } from './modules/ui-text.js';

// Registry for optional HX-Trigger "initModules"
const MODULES = {
    carouselModule: initCarousel,
    quotesModule: initQuotes,
    merchModule: initMerch,
    checkoutModule: initCheckout,
    bulletinModule: initBulletin,
    textModule:initUIText
};

function runAll(root = document) {
    // Idempotent init calls
    initUIText(root);
    initCarousel(root);
    initQuotes(root);
    initMerch(root);
    initCheckout(root);
    initBulletin(root);


    // one reflow after feature init
    if (window.hrSite?.reflowParallax) window.hrSite.reflowParallax();
}

function shouldReinit(target) {
    if (!target) return false;

    return (
        target.id === 'about-carousel-container' ||
        target.id === 'about-quotes-container' ||
        target.id === 'bulletin-root' ||
        target.id === 'modal-content' ||
        target.id === 'modal-message-box' ||
        target.closest?.('#about-carousel-container') ||
        target.closest?.('#about-quotes-container') ||
        target.closest?.('#bulletin-root') ||
        target.closest?.('#modal')
    );
}

/*
|--------------------------------------------------------------------------
| Initial load
|--------------------------------------------------------------------------
*/
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => runAll(document));
} else {
    runAll(document);
}


/*
|--------------------------------------------------------------------------
| HTMX lifecycle hooks
|--------------------------------------------------------------------------
*/
document.addEventListener('htmx:afterSwap', (e) => {
    const target = e.target;
    if (!shouldReinit(target)) return;
    runAll(target);
});

document.addEventListener('htmx:afterSettle', (e) => {
    const target = e.target;
    if (!shouldReinit(target)) return;
    if (window.hrSite?.reflowParallax) window.hrSite.reflowParallax();
});

/*
|--------------------------------------------------------------------------
| HX-Trigger driven module init
|--------------------------------------------------------------------------
| Example response header:
| HX-Trigger: {"initModules":{"modules":["textModule"],"reflow":false}}
|--------------------------------------------------------------------------
*/
document.body.addEventListener('initModules', (e) => {
    const detail = e.detail || {};
    const mods = detail.modules || detail.module || detail;
    const list = Array.isArray(mods) ? mods : [mods];

    list.forEach((name) => {
        const fn = MODULES[name];
        if (!fn) {
            console.warn('[meta-init] unknown module:', name);
            return;
        }
        fn(document);
    });

    if (detail.reflow !== false && window.hrSite?.reflowParallax) {
        window.hrSite.reflowParallax();
    }
});
