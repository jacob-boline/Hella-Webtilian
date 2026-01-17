// hr_core/static_src/js/modules/scroll-effects.js

import {wrapDateTimeChars, applyStitchedLetters} from "./ui-text.js";

(function () {
    // -----------------------------
    // Small, testable helpers
    // -----------------------------
    function defaultGetVH () {
        return (
            window.visualViewport?.height ||
            window.innerHeight ||
            document.documentElement.clientHeight
        );
    }

    function defaultDebounce (fn, wait = 200) {
        let t;
        return function (...args) {
            clearTimeout(t);
            t = setTimeout(() => fn.apply(this, args), wait);
        };
    }

    function safeCall (fn, ...args) {
        if (typeof fn === "function") fn(...args);
    }

    function readRuntimeDeps () {
        const config = window.hrSite?.config || {};
        const utils = window.hrSite?.utils || {};
        const bannerAPI = window.hrSite?.banner || {};

        return {
            config,
            bannerAPI,
            getVH: utils.getVH || defaultGetVH,
            debounce: utils.debounce || defaultDebounce,
        };
    }

    function getParallaxSpeed (config) {
        const ratio = config.PARALLAX_SCROLL_RATIO ?? 0.5;
        const reduced = !!config.REDUCED_MOTION;
        return reduced ? 0 : ratio;
    }

    function resetTransforms (selector) {
        document.querySelectorAll(selector).forEach((el) => {
            el.style.transform = "translate3d(0,0,0)";
        });
    }

    // -----------------------------
    // Module init
    // -----------------------------
    function initScrollEffects () {
        const {config, bannerAPI, getVH, debounce} = readRuntimeDeps();
        const parallaxSpeed = getParallaxSpeed(config);

        const wipes = document.querySelectorAll(".section-wipe");
        const parallaxSections = document.querySelectorAll(".parallax-section");

        // "Quiet efficiency": track visible sections without per-frame DOM queries
        const inViewSections = new Set();

        const STATE = {
            wipeData: new Map(),
            activeWipe: null,
            rafId: null,
            rafLayout: null,
            observers: {
                wipe: null,
                section: null,
            },
        };

        // -----------------------------
        // Layout + measurement
        // -----------------------------
        function initializeParallaxLayout () {
            const viewportHeight = getVH();

            parallaxSections.forEach((section) => {
                const content = section.querySelector(".parallax-content");
                const background = section.querySelector(".parallax-background");
                if (!content || !background) return;

                const adjusted = Math.max(
                    content.getBoundingClientRect().height,
                    viewportHeight
                );

                section.style.height = `${adjusted}px`;
                background.style.height = `${adjusted}px`;
            });
        }

        function positionWipesToNextSection () {
            wipes.forEach((wipe) => {
                const next = wipe.nextElementSibling;
                if (next && next.classList.contains("parallax-section")) {
                    const top = next.getBoundingClientRect().top + window.scrollY;
                    wipe.style.top = `${top}px`;
                }
                // preserve existing behavior
                delete wipe.dataset.baseHeight;
            });
        }

        function computeWipeData () {
            const viewportHeight = getVH();
            STATE.wipeData.clear();

            wipes.forEach((wipe) => {
                const rect = wipe.getBoundingClientRect();
                const wipeHeight = rect.height;

                const scrollSpeedRatio = (viewportHeight + wipeHeight) / viewportHeight;
                const wipeOffset = rect.top + window.scrollY + 50;

                STATE.wipeData.set(wipe, {scrollSpeedRatio, wipeOffset});
            });
        }

        // -----------------------------
        // Parallax updates
        // -----------------------------
        function updateParallaxForSection (section, scrollTop) {
            const background = section.querySelector(".parallax-background");
            if (!background) return;

            // Preserve existing math:
            // sectionOffset derived from viewport rect + scrollTop
            const sectionOffset = section.getBoundingClientRect().top + scrollTop;

            background.style.transform = `translate3d(0, ${(scrollTop - sectionOffset) * parallaxSpeed}px, 0)`;
        }

        function updateParallax (scrollTop) {
            if (parallaxSpeed === 0) return;
            if (inViewSections.size === 0) return;

            inViewSections.forEach((section) => {
                updateParallaxForSection(section, scrollTop);
            });
        }

        // -----------------------------
        // Wipe scroll behavior
        // -----------------------------
        function updateActiveWipeTransform () {
            if (!STATE.activeWipe) return;

            const data = STATE.wipeData.get(STATE.activeWipe);
            if (!data) return;

            const {scrollSpeedRatio, wipeOffset} = data;
            const scrollPosition = window.scrollY;
            const viewportHeight = getVH();

            const progress =
                (scrollPosition - wipeOffset + viewportHeight) / viewportHeight;

            if (progress < 0) return;

            const fasterScroll =
                (scrollPosition - wipeOffset + viewportHeight) / scrollSpeedRatio;

            STATE.activeWipe.style.transform = `translate3d(0, -${fasterScroll}px, 0)`;
        }

        function onWipeScroll () {
            updateActiveWipeTransform();
        }

        // -----------------------------
        // Observers
        // -----------------------------
        function disconnectObserver (key) {
            const obs = STATE.observers[key];
            if (obs) obs.disconnect();
            STATE.observers[key] = null;
        }

        function observeWipes () {
            disconnectObserver("wipe");

            STATE.observers.wipe = new IntersectionObserver(
                (entries) => {
                    entries.forEach((entry) => {
                        if (entry.isIntersecting) {
                            STATE.activeWipe = entry.target;
                            window.addEventListener("scroll", onWipeScroll, {passive: true});
                        } else if (STATE.activeWipe === entry.target) {
                            STATE.activeWipe = null;
                            window.removeEventListener("scroll", onWipeScroll);
                        }
                    });
                },
                {threshold: 0}
            );

            wipes.forEach((wipe) => STATE.observers.wipe.observe(wipe));
        }

        function observeSections () {
            disconnectObserver("section");

            STATE.observers.section = new IntersectionObserver(
                (entries) => {
                    entries.forEach((entry) => {
                        const section = entry.target;

                        if (entry.isIntersecting) {
                            section.classList.add("in-view");
                            inViewSections.add(section);
                        } else {
                            section.classList.remove("in-view");
                            inViewSections.delete(section);
                        }
                    });
                },
                {threshold: 0}
            );

            parallaxSections.forEach((section) =>
                STATE.observers.section.observe(section)
            );
        }

        // -----------------------------
        // rAF scheduling
        // -----------------------------
        function runBannerHooks (scrollTop) {
            safeCall(bannerAPI.setBannerState, scrollTop);
            safeCall(bannerAPI.updateFade);
        }

        function onScrollRaf () {
            if (STATE.rafId) return;

            STATE.rafId = requestAnimationFrame(() => {
                const scrollTop = window.scrollY;
                updateParallax(scrollTop);
                runBannerHooks(scrollTop);
                STATE.rafId = null;
            });
        }

        function isScrollLocked() {
            return (
                document.body.classList.contains('modal-open') ||
                document.body.classList.contains('drawer-open')
            );
        }

        function reflowParallax () {
            if (isScrollLocked()) return;
            if (STATE.rafLayout) return;

            STATE.rafLayout = requestAnimationFrame(() => {
                resetTransforms(".parallax-background, .section-wipe");

                initializeParallaxLayout();
                positionWipesToNextSection();
                computeWipeData();
                syncActiveWipe();

                // Preserve existing behavior: clear active wipe on reflow
                STATE.activeWipe = null;

                const scrollTop = window.scrollY;
                updateParallax(scrollTop);
                safeCall(bannerAPI.setBannerState, scrollTop);
                // Keep banner fade consistent after reflow/layout shifts
                safeCall(bannerAPI.updateFade);

                STATE.rafLayout = null;
            });
        }

        function syncActiveWipe() {
            const vh = getVH();

            let active = null;
            for (const wipe of wipes) {
                const rect = wipe.getBoundingClientRect();
                if (rect.bottom > 0 && rect.top < vh) {
                    active = wipe;
                    break;
                }
            }
            STATE.activeWipe = active;
            if (!STATE.wipeData.size) computeWipeData();
            updateActiveWipeTransform();
        }

        const reflowDebounced = debounce(reflowParallax, 80);

        // -----------------------------
        // Init sequence (preserve order)
        // -----------------------------
        wrapDateTimeChars(document);
        applyStitchedLetters(document, "#parallax-section-1 .act-name");

        initializeParallaxLayout();
        positionWipesToNextSection();
        computeWipeData();
        observeWipes();
        observeSections();

        const initialScroll = window.scrollY;
        updateParallax(initialScroll);
        safeCall(bannerAPI.setBannerState, initialScroll);
        safeCall(bannerAPI.updateFade);
        safeCall(bannerAPI.setupRecolorObserver);

        // -----------------------------
        // Event wiring (preserve behavior)
        // -----------------------------
        window.addEventListener("scroll", onScrollRaf, {passive: true});

        window.addEventListener("resize", reflowDebounced);
        window.addEventListener("orientationchange", reflowDebounced);
        window.visualViewport?.addEventListener("resize", reflowDebounced);

        document.fonts?.ready?.then?.(reflowParallax);
        window.addEventListener("load", reflowParallax);

        window.hrSite = window.hrSite || {};
        window.hrSite.reflowParallax = reflowParallax;
        window.hrSite.syncActiveWipe = syncActiveWipe;
    }

    // Run after DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initScrollEffects);
    } else {
        initScrollEffects();
    }
})();
