// hr_core/static_src/js/meta-init.js
//
// NOTE: Updated to call initCheckoutModule (details + pay in one shot)

import { initCarousel } from './modules/carousel.js';
import { initQuotes } from './modules/quotes.js';
import { initMerch } from './modules/merch.js';
import { initCheckoutModule } from './modules/checkout.js';
import { initBulletin } from './modules/bulletin.js';
import { initUIText } from './modules/ui-text.js';
import { initAutoAdvance } from './modules/auto-advance.js';
import { initTabHandoff } from './modules/tab-handoff.js';

// Registry for optional HX-Trigger "initModules"
const MODULES = {
  carouselModule: initCarousel,
  quotesModule: initQuotes,
  merchModule: initMerch,
  checkoutModule: initCheckoutModule,
  bulletinModule: initBulletin,
  textModule: initUIText,
  autoAdvanceModule: initAutoAdvance,
  tabHandoff: initTabHandoff
};

function reflowParallaxNow() {
  if (window.hrSite?.reflowParallax) window.hrSite.reflowParallax();
}

/**
 * "Settle" pass:
 * - wait for layout/styles to settle (especially after hash jumps and modal open)
 * - then reflow parallax
 * - then force a scroll event so wipe logic updates even if user didn't scroll
 */
function settleParallaxAndWipe() {
  if (!window.hrSite?.reflowParallax) return;

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      window.hrSite.reflowParallax();

      // If wipe/parallax state is scroll-driven, this ensures a recompute
      window.dispatchEvent(new Event('scroll'));
    });
  });
}

function runAll(root = document) {
  // Idempotent init calls
  initUIText(root);
  initCarousel(root);
  initQuotes(root);
  initMerch(root);
  initCheckoutModule(root);
  initBulletin(root);
  initAutoAdvance(root);
  initTabHandoff(root);

  // Keep this immediate reflow (useful for many swaps)
  reflowParallaxNow();
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

function isModalTarget(target) {
  if (!target) return false;
  return target.id === 'modal-content' || target.closest?.('#modal');
}

/*
|--------------------------------------------------------------------------
| Initial load
|--------------------------------------------------------------------------
*/
function initialBoot() {
  runAll(document);

  // Critical: hash jumps + vh shims + parallax measurements need a settle pass
  settleParallaxAndWipe();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => initialBoot());
} else {
  initialBoot();
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

  // If we swapped into the modal, do a settle pass.
  // Modal open often changes layout (scrollbar, focus, vh shims), which breaks wipe math.
  if (isModalTarget(target)) {
    settleParallaxAndWipe();
  }
});

document.addEventListener('htmx:afterSettle', (e) => {
  const target = e.target;
  if (!shouldReinit(target)) return;

  // Still safe to reflow; just don't rely on it alone.
  reflowParallaxNow();
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

  if (detail.reflow !== false) {
    settleParallaxAndWipe();
  }
});
