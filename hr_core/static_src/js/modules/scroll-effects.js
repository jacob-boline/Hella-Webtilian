// hr_core/static_src/js/modules/scroll-effects.js

import {applyStitchedLetters, wrapDateTimeChars} from "./ui-text.js";

(function () {

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
            debounce: utils.debounce || defaultDebounce
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

        // track visible sections without per-frame DOM queries
        const inViewSections = new Set();

        const STATE = {
            wipeData: new Map(),
            sectionData: new Map(),
            rafId: null,
            rafLayout: null,
            observers: {
                section: null
            },
            frame: {
                scrollTop: 0,
                vh: 0,
                dirty: true
            },
            viewport: {
                lockedVh: 0,
                pendingVh: 0,
                lastVvTs: 0,
                applyAfterMs: 140
            },
            scroll: {
                lastTs: 0,
                keepAliveMs: 120
            }
        };


        function beginFrameReads () {
            STATE.frame.scrollTop = window.scrollY;

            const liveVh = getVH();
            const now = performance.now();

            const isActivelyScrolling = (now - STATE.scroll.lastTs) < STATE.scroll.keepAliveMs;

            if (!STATE.viewport.lockedVh) {
                STATE.viewport.lockedVh = liveVh;
            }

            if (isActivelyScrolling) {
                // stay locked during scroll
                STATE.frame.vh = STATE.viewport.lockedVh;
            } else {
                // apply pending vh after scroll settles
                if (STATE.viewport.pendingVh) {
                    STATE.viewport.lockedVh = STATE.viewport.pendingVh;
                    STATE.viewport.pendingVh = 0;
                } else {
                    STATE.viewport.lockedVh = liveVh;
                }
                STATE.frame.vh = STATE.viewport.lockedVh;
            }

            STATE.frame.dirty = false;
        }


        function markFrameDirty () {
            STATE.frame.dirty = true;
        }

        function getFrameVH () {
            if (STATE.frame.dirty) beginFrameReads();
            return STATE.frame.vh;
        }

        function getFrameScrollTop () {
            if (STATE.frame.dirty) beginFrameReads();
            return STATE.frame.scrollTop;
        }

        // -----------------------------
        // Layout + measurement
        // -----------------------------
        function initializeParallaxLayout () {
            const viewportHeight = getVH();

            parallaxSections.forEach((section) => {
                const content = section.querySelector(".parallax-content");
                const background = section.querySelector(".parallax-background");
                if (!content || !background) return;

                if (section.classList.contains("parallax-sticky-bg")) {
                    const mult = Number(
                        getComputedStyle(document.documentElement)
                            .getPropertyValue("--bulletin-stage-mult")
                    ) || 2;

                    const contentH = content.getBoundingClientRect().height;
                    const maxStage = viewportHeight * mult;

                    const stageH = Math.max(viewportHeight, Math.min(contentH, maxStage));

                    // Store for parallax math
                    section.dataset.stageHeight = String(stageH);

                    // Set a CSS var so CSS can overlap content by the stage height
                    section.style.setProperty("--bulletin-stage-h", `${stageH}px`);

                    // Let section grow naturally with infinite content
                    section.style.height = "";
                    background.style.height = "";

                    return;
                }

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

        // Cache section "document top"
        function computeSectionData () {
            STATE.sectionData.clear();
            parallaxSections.forEach((section) => {
                const topDoc = section.getBoundingClientRect().top + window.scrollY;
                STATE.sectionData.set(section, {topDoc});
            });
        }

        // -----------------------------
        // Parallax updates
        // -----------------------------
        function updateParallaxForSection (section, scrollTop) {
            if (section.classList.contains("parallax-sticky-bg")) {
                updateBulletinStickyParallax(section, scrollTop);
                return;
            }

            const background = section.querySelector(".parallax-background");
            if (!background) return;

            const topDoc = STATE.sectionData.get(section)?.topDoc;
            if (topDoc == null) return;

            background.style.transform =
                `translate3d(0, ${(scrollTop - topDoc) * parallaxSpeed}px, 0)`;
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
        function updateWipesTransform () {
            // With only ~4 wipes, update all of them deterministically each frame.
            if (!STATE.wipeData.size) return;

            const scrollPosition = getFrameScrollTop();
            const viewportHeight = getFrameVH();

            wipes.forEach((wipe) => {
                const data = STATE.wipeData.get(wipe);
                if (!data) return;

                const {scrollSpeedRatio, wipeOffset} = data;

                const fasterScroll =
                    (scrollPosition - wipeOffset + viewportHeight) / scrollSpeedRatio;

                const y = Math.max(0, fasterScroll);

                wipe.style.transform = `translate3d(0, -${y}px, 0)`;
            });
        }

        function onWipeScroll () {
            markFrameDirty();
            scheduleScrollRaf();
        }

        // -----------------------------
        // Observers
        // -----------------------------
        function disconnectObserver (key) {
            const obs = STATE.observers[key];
            if (obs) obs.disconnect();
            STATE.observers[key] = null;
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

        function clamp (n, min, max) {
            return Math.max(min, Math.min(max, n));
        }

        function updateBulletinStickyParallax (section, scrollTop) {
            const bg = section.querySelector(".parallax-background");
            if (!bg) return;

            const vh = getFrameVH();
            const stageH = Number(section.dataset.stageHeight || 0) || vh;

            const maxTravel = Math.max(0, stageH - vh);

            const topDoc = STATE.sectionData.get(section)?.topDoc;
            if (topDoc == null) return;

            const into = clamp(scrollTop - topDoc, 0, maxTravel);

            const y = into * parallaxSpeed;

            bg.style.transform = `translate3d(0, ${y}px, 0)`;
        }

        // -----------------------------
        // rAF scheduling
        // -----------------------------
        function runBannerHooks (scrollTop) {
            safeCall(bannerAPI.setBannerState, scrollTop);
            safeCall(bannerAPI.updateFade);
        }

        function scheduleScrollRaf () {
            if (STATE.rafId) return;

            STATE.rafId = requestAnimationFrame(() => {
                // batch reads once
                beginFrameReads();

                const scrollTop = STATE.frame.scrollTop;

                updateParallax(scrollTop);
                updateWipesTransform();
                runBannerHooks(scrollTop);

                // next scroll/frame should re-read
                markFrameDirty();

                // keep animating briefly after the last scroll event  (mobile touchscreens)
                const now = performance.now();
                if (now - STATE.scroll.lastTs < STATE.scroll.keepAliveMs) {
                    STATE.rafId = null;
                    scheduleScrollRaf();
                    return;
                }

                STATE.rafId = null;
            });
        }

        function onScroll () {
            STATE.scroll.lastTs = performance.now();
            markFrameDirty();
            scheduleScrollRaf();
        }

        function isScrollLocked () {
            return (
                document.body.classList.contains("modal-open") ||
                document.body.classList.contains("drawer-open")
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
                computeSectionData();

                // Update once after reflow
                markFrameDirty();
                beginFrameReads();

                const scrollTop = STATE.frame.scrollTop;
                updateParallax(scrollTop);
                updateWipesTransform();
                safeCall(bannerAPI.setBannerState, scrollTop);
                safeCall(bannerAPI.updateFade);

                markFrameDirty();
                STATE.rafLayout = null;
            });
        }

        const reflowDebounced = debounce(reflowParallax, 80);

        // reflow wipes/parallax on any image load
        document.addEventListener("load", (e) => {
            const el = e.target;
            if (!el || el.tagName !== "IMG") return;
            if (!el.closest?.("#parallax-wrapper")) return;
            reflowDebounced();
        }, true);

        // --------------
        // Init sequence
        // --------------
        wrapDateTimeChars(document);
        applyStitchedLetters(document, "#parallax-section-1 .act-name");

        initializeParallaxLayout();
        positionWipesToNextSection();
        computeWipeData();
        computeSectionData();
        observeSections();

        markFrameDirty();
        beginFrameReads();

        const initialScroll = STATE.frame.scrollTop;
        updateParallax(initialScroll);
        updateWipesTransform();
        safeCall(bannerAPI.setBannerState, initialScroll);
        safeCall(bannerAPI.updateFade);
        safeCall(bannerAPI.setupRecolorObserver);

        markFrameDirty();

        // ------------
        // Event wiring
        // -------------
        window.addEventListener("scroll", onScroll, {passive: true});
        window.addEventListener("resize", reflowDebounced);
        window.addEventListener("orientationchange", reflowDebounced);
        window.visualViewport?.addEventListener("resize", () => {
          // record the new vh, but don't force layout while scrolling
          const live = defaultGetVH();
          STATE.viewport.pendingVh = live;

          // If user isn't actively scrolling, reflow soon.
          const now = performance.now();
          const isActivelyScrolling = (now - STATE.scroll.lastTs) < STATE.scroll.keepAliveMs;
          if (!isActivelyScrolling) reflowDebounced();
        });
        document.fonts?.ready?.then?.(reflowParallax);
        window.addEventListener("load", reflowParallax);

        window.hrSite = window.hrSite || {};
        window.hrSite.reflowParallax = reflowParallax;
        window.hrSite.onWipeScroll = onWipeScroll;
    }

    // Run after DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initScrollEffects);
    } else {
        initScrollEffects();
    }
})();
