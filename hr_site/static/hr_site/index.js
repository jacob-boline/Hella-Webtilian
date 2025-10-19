/* hr_site/index.js — drop-in */

// -----------------------------
// Utilities
// -----------------------------
function debounce (fn, wait = 200) {
    let t;
    return function (...args) {
        clearTimeout(t);
        t = setTimeout(() => fn.apply(this, args), wait);
    };
}

// Single source of truth for viewport height (URL-bar aware on mobile)
function getVH () {
    if (window.visualViewport && window.visualViewport.height) {
        return window.visualViewport.height;
        //return Math.round(window.visualViewport.height);
    }
    // const vhVar = getComputedStyle(document.documentElement).getPropertyValue('--vh').trim();
    // const n = parseFloat(vhVar);
    // if (!Number.isNaN(n) && n > 0) return Math.round(n * 100);
    return window.innerHeight || document.documentElement.clientHeight;
}

// Keep CSS var --vh in sync with real viewport height
function setVH () {
    const h = (window.visualViewport && window.visualViewport.height)
        ? window.visualViewport.height
        : (window.innerHeight || document.documentElement.clientHeight);
    document.documentElement.style.setProperty('--vh', (h * 0.01) + 'px');
}


/* About section module (no Tailwind required) */
const about = (() => {
    // ---------- defaults ----------
    const defaults = {
        rootSelector: '#about-carousel',
        items: [],               // [{src, alt, quote}]
        startIndex: 0,
        preload: true,
        loop: true,
        keyboard: true,
        swipe: true
    };

    // ---------- helpers ----------
    const clamp = (n, min, max) => Math.min(Math.max(n, min), max);
    const mod = (n, m) => ((n % m) + m) % m;

    function preloadAround (items, i) {
        const toPreload = [i, i + 1, i - 1].map(j => mod(j, items.length));
        toPreload.forEach(idx => {
            const img = new Image();
            img.src = items[idx].src;
        });
    }

    function centerThumb (thumb, rail) {
        if (!thumb || !rail) return;
        const railRect = rail.getBoundingClientRect();
        const liRect = thumb.getBoundingClientRect();
        const current = rail.scrollLeft;
        const target = current + (liRect.left - railRect.left) - (railRect.width / 2 - liRect.width / 2);
        rail.scrollTo({left: target, behavior: 'smooth'});
    }

    // touch swipe (stage)
    function swipeBinder (el, onSwipe) {
        let x0 = null, t0 = 0;
        const onTouchStart = (e) => {
            x0 = e.touches[0].clientX;
            t0 = Date.now();
        };
        const onTouchEnd = (e) => {
            if (x0 == null) return;
            const dx = e.changedTouches[0].clientX - x0;
            const dt = Date.now() - t0;
            x0 = null;
            // simple threshold
            if (Math.abs(dx) > 40 && dt < 600) onSwipe(dx < 0 ? 'next' : 'prev');
        };
        el.addEventListener('touchstart', onTouchStart, {passive: true});
        el.addEventListener('touchend', onTouchEnd, {passive: true});
        return () => {
            el.removeEventListener('touchstart', onTouchStart);
            el.removeEventListener('touchend', onTouchEnd);
        };
    }

    // ---------- main init ----------
    function init (userConfig = {}) {
        const cfg = {...defaults, ...userConfig};
        const root = document.querySelector(cfg.rootSelector);
        if (!root) {
            console.warn('[about] root not found:', cfg.rootSelector);
            return;
        }

        // required sub-elements (match the HTML you pasted)
        const stage = root.querySelector('.about-stage');
        const stageImg = root.querySelector('.about-stage-img');
        const captionEl = root.querySelector('.about-quote');
        const prevBtn = root.querySelector('.about-nav.prev');
        const nextBtn = root.querySelector('.about-nav.next');
        const thumbsUl = root.querySelector('.about-thumbs');
        const thumbsPrev = root.querySelector('.thumbs-prev');
        const thumbsNext = root.querySelector('.thumbs-next');

        if (!stage || !stageImg || !captionEl || !prevBtn || !nextBtn || !thumbsUl) {
            console.warn('[about] missing required child elements');
            return;
        }

        // state
        let index = clamp(cfg.startIndex, 0, Math.max(0, cfg.items.length - 1));
        let cleanupSwipe = null;

        // ARIA semantics
        thumbsUl.setAttribute('role', 'tablist');
        stage.setAttribute('role', 'group');

        // build thumbs
        thumbsUl.innerHTML = '';
        const thumbLis = cfg.items.map((item, i) => {
            const li = document.createElement('li');
            li.className = 'about-thumb';
            li.setAttribute('role', 'tab');
            li.setAttribute('aria-selected', 'false');
            li.setAttribute('tabindex', '-1');

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'about-thumb-btn';
            btn.setAttribute('aria-label', item.alt || `Image ${i + 1}`);

            const img = document.createElement('img');
            img.src = item.src;
            img.alt = item.alt || '';

            btn.appendChild(img);
            li.appendChild(btn);
            thumbsUl.appendChild(li);

            // click -> go to slide
            btn.addEventListener('click', () => setActive(i, true));
            // keyboard on thumbs
            li.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setActive(i, true);
                }
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    setActive(i + 1, true);
                }
                if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    setActive(i - 1, true);
                }
            });

            return li;
        });

        function render (i) {
            const item = cfg.items[i];
            if (!item) return;
            stageImg.src = item.src;
            stageImg.alt = item.alt || '';
            captionEl.textContent = item.quote || '';
        }

        function highlightThumb (i) {
            thumbLis.forEach((li, idx) => {
                const active = idx === i;
                li.classList.toggle('is-active', active);
                li.setAttribute('aria-selected', active ? 'true' : 'false');
                li.setAttribute('tabindex', active ? '0' : '-1');
            });
            centerThumb(thumbLis[i], thumbsUl);
        }

        function setActive (i, userInitiated = false) {
            const len = cfg.items.length;
            if (!len) return;

            index = cfg.loop ? mod(i, len) : clamp(i, 0, len - 1);
            render(index);
            highlightThumb(index);

            if (cfg.preload && len > 1) preloadAround(cfg.items, index);
            if (userInitiated) stage.focus({preventScroll: true});
            if (typeof cfg.onChange === 'function') cfg.onChange(index);
        }

        const scrollOne = dir => thumbsUl.scrollBy({left: dir * (thumbsUl.clientWidth / 3), behavior: 'smooth'});

        // nav actions
        const goPrev = () => {
            setActive(index - 1, true);
            scrollOne(-1);
        };
        const goNext = () => {
            setActive(index + 1, true);
            scrollOne(+1);
        };
        prevBtn.addEventListener('click', goPrev);
        nextBtn.addEventListener('click', goNext);

        // thumbnail nav
        if (thumbsPrev) thumbsPrev.addEventListener('click', () => {
            setActive(index - 1, true);
            scrollOne(-1);
        });
        if (thumbsNext) thumbsNext.addEventListener('click', () => {
            setActive(index + 1, true);
            scrollOne(+1);
        });

        // stage keyboard
        if (cfg.keyboard) {
            root.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    goNext();
                }
                if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    goPrev();
                }
            });
        }

        // stage swipe
        if (cfg.swipe) cleanupSwipe = swipeBinder(stage, dir => dir === 'next' ? goNext() : goPrev());

        // keep active thumb centered on resize
        const onResize = () => centerThumb(thumbLis[index], thumbsUl);
        window.addEventListener('resize', onResize);

        // first render
        setActive(index, false);

        // expose a tiny API if you want it later
        return {
            next: goNext,
            prev: goPrev,
            go: (i) => setActive(i, true),
            destroy () {
                prevBtn.removeEventListener('click', goPrev);
                nextBtn.removeEventListener('click', goNext);
                window.removeEventListener('resize', onResize);
                if (cleanupSwipe) cleanupSwipe();
            }
        };
    }

    return {init};
})();


// -----------------------------
// Main
// -----------------------------
document.addEventListener("DOMContentLoaded", function () {
    // Drawer elements
    const button = document.querySelector('.text-left button');
    const sidebar = document.querySelector('#drawer-navigation');
    const sidebarCloseButton = document.querySelector('[data-drawer-hide="drawer-navigation"]');
    const drawerTarget = document.querySelector('[data-drawer-target="drawer-navigation"]');
    if (sidebar) sidebar.classList.add('-translate-x-full');

    // Parallax + wipes
    const parallaxSections = document.querySelectorAll('.parallax-section');
    let wipes = document.querySelectorAll('.section-wipe');
    const wipeData = {};
    let activeWipe = null;
    let rafId = null;

    // Banner setup
    const buffer = 2;
    const step = 5;
    const banners = document.querySelectorAll('.banner-letter');
    const banner = document.querySelector('#banner');
    const bannerScroller = document.querySelector('#banner-scroller');
    const bannerRow = document.querySelector('.banner-row');
    const sectionWipe0 = document.querySelector('#section-wipe-0');
    let lastIndexHidden = -1;
    let isBannerTransparent = false;
    const bannerTimeouts = {};

    // Parallax speed
    let parallaxSpeed = 0.5;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion) parallaxSpeed = 0;

    const aboutData = document.getElementById('about-data');
    const items = aboutData ? JSON.parse(aboutData.textContent) : [];


    // About config
    // const ABOUT_CONFIG = {
    //     rootSelector: '#about-carousel',
    //     items: [
    //         {
    //             src: '{% static "hr_site/img/about/HR_AMST_1.jpg" %}',
    //             alt: 'Live',
    //             quote: '"You are audible!" - Willian Murderface'
    //         },
    //         {
    //             src: '{% static "hr_site/img/about/HR_AMST_2.jpg" %}',
    //             alt: 'Backstage',
    //             quote: '"Some of my finest work, honestly I might have peaked." - God'
    //         },
    //         {
    //             src: '{% static "hr_site/img/about/HR_AMST_3.jpg" %}',
    //             alt: 'Studio',
    //             quote: '"They sang as they slew." - J.R.R. Tolkien'
    //         },
    //         {
    //             src: '{% static "hr_site/img/about/HR_AMST_4.jpg" %}',
    //             alt: 'Stick Wielder',
    //             quote: '"These guys fucking rock!" - Mr. Rogers'
    //         }
    //     ],
    //     startIndex: 0,
    //     preload: true,
    //     loop: true
    // };


    // -----------------------------
    // Banner helpers
    // -----------------------------
    banners.forEach(b => {
        b.classList.remove('is-visible', 'burn', 'is-fading', 'hidden-once');
        b.style.opacity = '';
    });

    function showBanner (i) {
        const el = banners[i];
        if (!el || el.classList.contains('burn')) return;
        el.classList.remove('blink', 'is-fading', 'hidden-once');
        el.classList.add('burn', 'is-visible');
    }

    function hideBanner (i) {
        const el = banners[i];
        if (!el || el.classList.contains('hidden-once')) return;
        if (bannerTimeouts[i]) {
            clearTimeout(bannerTimeouts[i].stage1);
            clearTimeout(bannerTimeouts[i].stage2);
            delete bannerTimeouts[i];
        }
        el.classList.add('hidden-once', 'is-fading');
        el.classList.remove('is-visible');
    }

    function setBannerState () {
        const scrollPosition = Math.floor(window.scrollY);
        const vh = Math.floor(getVH() / 100); // 1vh in px / 100
        const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
        const indexResetPoint = (bannerScroller ? (bannerScroller.offsetTop + bannerScroller.offsetHeight) : 0);

        if (scrollPosition < indexResetPoint) {
            lastIndexHidden = -1;
        }

        for (let i = 0; i < banners.length; i++) {
            if (i <= indexToShow && !banners[i].classList.contains('is-visible')) {
                showBanner(i);
            } else if (i > indexToShow && (scrollPosition - indexResetPoint) >= vh * i && i > lastIndexHidden) {
                hideBanner(i);
                lastIndexHidden = i;
            }
        }
    }

    function recolorBanner () {
        const first = document.getElementById('section-wipe-0');
        const bannerEl = banner;
        if (!first || !bannerEl) return;

        const observer = new IntersectionObserver(entries => {
            for (const e of entries) {
                if (!e.isIntersecting && e.boundingClientRect.top < 0) {
                    bannerEl.style.backgroundColor = 'rgba(0,0,0,1)';
                    banners.forEach(b => {
                        b.style.color = 'darkorange';
                    });
                } else {
                    banners.forEach(b => {
                        b.style.color = '';
                    });
                }
            }
        }, {root: null, threshold: 0, rootMargin: `-${bannerEl.offsetHeight}px 0px 0px 0px`});
        observer.observe(first);
    }

    function addBannerObserver () {
        if (!sectionWipe0 || !bannerRow || !banner) return;
        const bannerObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (!isBannerTransparent && entry.isIntersecting) {
                    bannerRow.style.transition = 'opacity 0.1s ease-in-out';
                    bannerRow.style.opacity = '0';
                    banner.style.transition = 'opacity 0.1s ease-in-out';
                    banner.style.opacity = '0';
                    isBannerTransparent = true;
                }
            });
        }, {
            root: null,
            threshold: 0,
            rootMargin: '0px 0px -100% 0px'
        });
        bannerObserver.observe(sectionWipe0);
    }

    // -----------------------------
    // Content helpers
    // -----------------------------
    function applyStitchedLetters (selector) {
        document.querySelectorAll(selector).forEach(el => {
            const text = el.textContent.trim();
            el.innerHTML = '';
            for (let char of text) {
                const span = document.createElement('span');
                span.className = 'letter';
                span.textContent = char === ' ' ? '\u00A0' : char;
                el.appendChild(span);
            }
        });
    }

    function wrapDateTimeChars () {
        document.querySelectorAll('.date, .time').forEach(el => {
            const text = el.textContent.trim();
            el.innerHTML = '';
            text.split('').forEach(char => {
                const span = document.createElement('span');
                span.className = el.classList.contains('date')
                    ? 'date-char'
                    : el.classList.contains('time')
                        ? 'time-char'
                        : 'btn-char';
                span.textContent = char === ' ' ? '\u00A0' : char;
                el.appendChild(span);
            });
        });
    }

    // -----------------------------
    // Parallax sizing & positioning
    // -----------------------------
    function initializeParallax () {
        const viewportHeight = getVH();
        parallaxSections.forEach(section => {
            const content = section.querySelector('.parallax-content');
            const background = section.querySelector('.parallax-background');
            if (!content || !background) return;
            const adjusted = Math.max(content.getBoundingClientRect().height, viewportHeight);
            section.style.height = `${adjusted}px`;
            background.style.height = `${adjusted}px`;
        });
    }

    function positionSectionWipes () {
        document.querySelectorAll('.section-wipe').forEach(wipe => {
            const next = wipe.nextElementSibling;
            if (next && next.classList.contains('parallax-section')) {
                const top = next.getBoundingClientRect().top + window.scrollY;
                wipe.style.top = `${top}px`;
            }
            // Do NOT set wipe height here; CSS controls it.
            delete wipe.dataset.baseHeight;
        });
    }

    function calculateWipeData () {
        const viewportHeight = getVH();
        wipes.forEach(wipe => {
            const wipeRect = wipe.getBoundingClientRect();
            const wipeHeight = wipeRect.height;
            const scrollSpeedRatio = (viewportHeight + wipeHeight) / viewportHeight;
            const wipeOffset = wipeRect.top + window.scrollY + 50;
            wipeData[wipe.id] = {scrollSpeedRatio, wipeOffset};
        });

        // wipes.forEach(wipe => {
        //     const wipeHeight = wipe.getBoundingClientRect().height;
        //     const viewportHeight = getVH(); // - 30; // keep your fudge factor
        //     const scrollSpeedRatio = (viewportHeight + wipeHeight) / viewportHeight;
        //     const wipeOffset = wipe.getBoundingClientRect().top + window.scrollY;
        //     wipeData[wipe.id] = {scrollSpeedRatio, wipeOffset};
        // });
    }

    function updateParallax (scrollTop) {
        document.querySelectorAll('.parallax-section.in-view').forEach(section => {
            //const sectionOffset = section.offsetTop;
            const sectionOffset = section.getBoundingClientRect().top + scrollTop;
            const background = section.querySelector('.parallax-background');
            if (!background) return;
            background.style.transform =
                `translate3d(0, ${(scrollTop - sectionOffset) * parallaxSpeed}px, 0)`; // GPU path
        });
    }

    // Active wipe scroll handler (GPU path)
    function handleScroll () {
        if (!activeWipe || !wipeData[activeWipe.id]) return;
        const scrollPosition = window.scrollY;
        const {scrollSpeedRatio, wipeOffset} = wipeData[activeWipe.id];
        const viewportHeight = getVH();
        const progress = (scrollPosition - wipeOffset + viewportHeight) / viewportHeight;
        if (progress >= 0) {
            const fasterScroll = (scrollPosition - wipeOffset + viewportHeight) / scrollSpeedRatio;
            activeWipe.style.transform = `translate3d(0, -${fasterScroll}px, 0)`;
        }
    }

    // -----------------------------
    // Observers
    // -----------------------------
    let wipeObserver = null;

    function observeWipes () {
        if (wipeObserver) wipeObserver.disconnect();
        wipeObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    activeWipe = entry.target;
                    window.addEventListener("scroll", handleScroll, {passive: true});
                } else if (activeWipe === entry.target) {
                    activeWipe = null;
                    window.removeEventListener("scroll", handleScroll);
                }
            });
        }, {threshold: 0});
        wipes.forEach(wipe => wipeObserver.observe(wipe));
    }

    let sectionObserver = null;

    function observeElements () {
        if (sectionObserver) sectionObserver.disconnect();
        sectionObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                } else {
                    entry.target.classList.remove('in-view');
                }
            });
        }, {threshold: 0});
        parallaxSections.forEach(section => sectionObserver.observe(section));
    }

    // -----------------------------
    // Scroll RAF
    // -----------------------------
    function onScrollRaf () {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            updateParallax(window.scrollY);
            setBannerState();
            rafId = null;
        });
    }

    // -----------------------------
    // Reflow (order-of-ops matters)
    // -----------------------------
    let rafLayout = null;

    function reflowParallax () {
        if (rafLayout) return;
        rafLayout = requestAnimationFrame(() => {
            // Clear transforms before measuring
            document.querySelectorAll('.parallax-background, .section-wipe')
                .forEach(el => el.style.transform = 'translate3d(0,0,0)');

            initializeParallax();    // size sections/backgrounds
            positionSectionWipes();  // re-anchor wipes to their sections
            calculateWipeData();     // recompute offsets/ratios
            activeWipe = null;       // stale ref reset; observer will re-pick
            updateParallax(window.scrollY);
            setBannerState();

            rafLayout = null;
        });
    }

    const reflowDebounced = debounce(reflowParallax, 80);

    // -----------------------------
    // Drawer controls
    // -----------------------------
    function addSidebarListener () {
        if (!drawerTarget || !button || !sidebar) return;
        drawerTarget.addEventListener('click', function () {
            button.style.opacity = '0';
            button.style.pointerEvents = 'none';
            sidebar.classList.toggle('show');
            sidebar.classList.toggle('-translate-x-full');
            sidebar.classList.toggle('translate-x-0');
            drawerTarget.setAttribute('aria-expanded', sidebar.classList.contains('show') ? 'true' : 'false');
            sidebar.setAttribute('aria-hidden', sidebar.classList.contains('show') ? 'false' : 'true');
        });
    }

    function addCloseSidebarBtnListener () {
        if (!sidebarCloseButton || !sidebar || !button) return;
        sidebarCloseButton.addEventListener('click', function () {
            button.style.opacity = '1';
            button.style.pointerEvents = 'auto';
            sidebar.classList.remove('show');
            sidebar.classList.add('-translate-x-full');
            sidebar.classList.remove('translate-x-0');
        });
    }

    // -----------------------------
    // Init
    // -----------------------------
    setVH();                   // sync CSS --vh
    wrapDateTimeChars();
    applyStitchedLetters('#parallax-section-1 .act-name');

    // Initial measurement & observers
    initializeParallax();
    positionSectionWipes();
    calculateWipeData();
    observeWipes();
    observeElements();
    updateParallax(window.scrollY);
    setBannerState();
    recolorBanner();
    addBannerObserver();
    addSidebarListener();
    addCloseSidebarBtnListener();
    //about.init(ABOUT_CONFIG);
    about.init({rootSelector: '#about-carousel', items, startIndex: 0, preload: true, loop: true});

    // Scroll
    window.addEventListener('scroll', onScrollRaf, {passive: true});

    // Resize-ish events
    window.addEventListener('resize', () => {
        setVH();
        reflowDebounced();
    });
    window.addEventListener('orientationchange', () => {
        setVH();
        reflowDebounced();
    });
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', () => {
            setVH();
            reflowDebounced();
        });
    }
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(() => {
            setVH();
            reflowParallax();
        });
    }
    window.addEventListener('load', () => {
        setVH();
        reflowParallax();
    });

    // -----------------------------
    // HTMX modal open hook (unchanged)
    // -----------------------------
    document.addEventListener('htmx:afterSwap', (e) => {
        if (e.target && e.target.id === 'merch-modal-body') {
            const modal = document.getElementById('merch-modal');
            if (modal) modal.classList.remove('hidden');
        }
    });

    // -----------------------------
    // Stripe buy buttons (unchanged)
    // -----------------------------
    const stripe = window.Stripe ? Stripe("pk_test_XXXXYOUR_PUBLISHABLE_KEY") : null;

    function handleStripeResult (result) {
        if (result && result.error) {
            console.error(result.error.message);
            alert(result.error.message);
        }
    }

    document.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-buy]');
        if (!btn || !stripe) return;

        const priceId = btn.dataset.priceId;
        const qty = parseInt(btn.dataset.qty || '1', 10);
        if (!priceId) {
            console.warn('Missing data-price-id on buy button');
            return;
        }

        stripe.redirectToCheckout({
            lineItems: [{price: priceId, quantity: qty}],
            mode: 'payment',
            successUrl: window.location.origin + '/checkout/success?session_id={CHECKOUT_SESSION_ID}',
            cancelUrl: window.location.origin + '/checkout/cancel'
        }).then(handleStripeResult);
    });
});