// hr_core/static_src/js/modules/intro.js

(function () {
    'use strict';

    const INTRO_BOOT_FLAG = '__hrIntroInitialized';

    // ===========================
    // Configuration & Timing
    // ===========================

    const TIMINGS = {
        logoFadeIn:                                300,
        highlightH:      { start:  500, duration:  250 },
        highlightR:      { start:  800, duration:  250 },
        highlightStroke: { start: 1100, duration:  250 },
        highlightDot:    { start: 1100, duration:  250 },
        lockIn:          { start: 1400, duration:  250 },
        hold:                                      750,
        introYield:      { start: 2400, duration: 1500 },  // lockIn.start + lockIn.duration + hold
        total:                    3900,                    // introYield.start + introYield.duration,
        // hintIdleDelay:            6000,
        // hintNudgeDuration:                         500
    };

    // ===========================
    // State Management
    // ===========================

    const STATE = {
        phase: 'inactive',
        timeouts: [],
        startTime: null,
        skipRequested: false,
        // hintNudgeTriggered: false,
        interactionDetected: false
    };

    // ===========================
    // DOM References
    // ===========================

    let overlay = null;
    let logoBase = null;
    let highlightH = null;
    let highlightCenter = null;
    let highlightR = null;
    let highlightStroke = null;
    let highlightDot = null;
    let introName = null;
    // let scrollHint = null;

    // ===========================
    // Utilities
    // ===========================

    function clearAllTimeouts () {
        STATE.timeouts.forEach(id => clearTimeout(id));
        STATE.timeouts = [];
    }

    function addTimeout (fn, delay) {
        const id = setTimeout(() => {
            STATE.timeouts = STATE.timeouts.filter(t => t !== id);
            fn();
        }, delay);
        STATE.timeouts.push(id);
        return id;
    }

    function pulseHighlight (element, duration) {
        if (!element) return;
        element.classList.add('pulse');
        addTimeout(() => {
            element.classList.remove('pulse');
        }, duration);
    }

    function warmBelowFoldFonts() {
        if (!document.fonts || typeof document.fonts.load !== "function") return;

        try {
            const syne = document.fonts.load('400 1em "Syne Mono"');
            const edu  = document.fonts.load('400 1em "Edu SA Beginner"');

            // Optional: once loaded, mark as ready (if you want to flip CSS later)
            Promise.allSettled([syne, edu]).then(() => {
                document.documentElement.classList.add("fonts-belowfold-ready");
            });
        } catch (e) { }
    }

    function scheduleFontWarmup() {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                warmBelowFoldFonts();
            });
        });
    }


    // ===========================
    // Animation Sequence
    // ===========================

    function runIntroSequence (prefersReducedMotion) {
        if (prefersReducedMotion) {
            runReducedMotionSequence();
            return;
        }

        STATE.phase = 'active';
        STATE.startTime = performance.now();
        overlay.classList.add('active');

        scheduleFontWarmup();

        // Phase 2: Diagnostic highlights
        addTimeout(() => {
            pulseHighlight(highlightH, TIMINGS.highlightH.duration);
            pulseHighlight(highlightCenter, TIMINGS.highlightH.duration);
        }, TIMINGS.highlightH.start);

        addTimeout(() => {
            pulseHighlight(highlightR, TIMINGS.highlightR.duration);
            pulseHighlight(highlightCenter, TIMINGS.highlightR.duration);
        }, TIMINGS.highlightR.start);

        addTimeout(() => {
            pulseHighlight(highlightStroke, TIMINGS.highlightStroke.duration);
        }, TIMINGS.highlightStroke.start);

        addTimeout(() => {
            pulseHighlight(highlightDot, TIMINGS.highlightDot.duration);
        }, TIMINGS.highlightDot.start);

        // Phase 3: Identity
        addTimeout(() => {
            logoBase.classList.add('locked');
            introName.classList.add('visible');

            setupGlitchName(introName, "HELLA REPTILIAN!");
            playGlitchName(introName, { settleMs: 520 });
        }, TIMINGS.lockIn.start);

        // Phase 4: Hold

        // Phase 5: Yield
        addTimeout(() => {
            yieldToSite();
        }, TIMINGS.introYield.start);
    }

    function runReducedMotionSequence () {
        STATE.phase = 'active';
        overlay.classList.add('active');

        scheduleFontWarmup();

        // Show everything immediately
        logoBase.classList.add('locked');
        logoBase.style.opacity = '1';
        introName.classList.add('visible');

        // Brief display, then yield
        addTimeout(() => {
            yieldToSite();
        }, 800);
    }

    function yieldToSite () {
        if (STATE.phase === 'complete') return;

        STATE.phase = 'yielding';
        overlay.classList.remove('active');
        overlay.classList.add('yielding');

        addTimeout(() => {
            completeIntro();
        }, TIMINGS.introYield.duration);
    }

    function completeIntro () {
        STATE.phase = 'complete';
        overlay.classList.add('complete');
        // showScrollHint();
        removeSkipListeners();
    }

    // ===========================
    // Skip/Accelerate Logic
    // ===========================

    function skipIntro () {
        if (STATE.phase !== 'active') return;

        STATE.skipRequested = true;
        clearAllTimeouts();

        yieldToSite();
    }

    function handleWheel () {
        skipIntro();
    }

    function handleTouchStart () {
        skipIntro();
    }

    function handleTouchMove () {
        skipIntro();
    }

    function handleKeyDown (event) {
        const skipKeys = ['ArrowDown', 'PageDown', ' '];
        if (skipKeys.includes(event.key)) {
            skipIntro();
        }
    }

    function addSkipListeners () {
        window.addEventListener('wheel', handleWheel, {passive: true});
        window.addEventListener('touchstart', handleTouchStart, {passive: true});
        window.addEventListener('touchmove', handleTouchMove, {passive: true});
        window.addEventListener('keydown', handleKeyDown);
    }

    function removeSkipListeners () {
        window.removeEventListener('wheel', handleWheel);
        window.removeEventListener('touchstart', handleTouchStart);
        window.removeEventListener('touchmove', handleTouchMove);
        window.removeEventListener('keydown', handleKeyDown);
    }


    function setupGlitchName (el, text) {
        const pool = "HR!+*#=/\\<>[]{}:-_".split("");

        const frag = document.createDocumentFragment();

        for (const ch of text) {
            const span = document.createElement("span");
            span.className = "ch";

            // PRESERVE SPACES
            const finalChar = ch === " " ? "\u00A0" : ch;
            span.dataset.final = finalChar;

            // SET 6 RANDOMIZED GLIPHS PER CHARACTER
            const picks = Array.from({length: 6}, () => pool[(Math.random() * pool.length) | 0]);

            // KEYS USED FOR RANDOMIZATION
            span.style.setProperty("--c0", `"${picks[0]}"`);
            span.style.setProperty("--c1", `"${picks[1]}"`);
            span.style.setProperty("--c2", `"${picks[2]}"`);
            span.style.setProperty("--c3", `"${picks[3]}"`);
            span.style.setProperty("--c4", `"${picks[4]}"`);
            span.style.setProperty("--c5", `"${picks[5]}"`);

            const colors = ["var(--text)", "var(--neon-blue)", "darkorange"];
            for (let g = 0; g < 6; g++) {
                span.style.setProperty(`--g${g}`, colors[Math.floor(Math.random() * colors.length)]);
            }

            // STAGGARED ITERATION
            const i = frag.childNodes.length;
            span.style.setProperty("--delay", `${i * 22}ms`);
            span.style.setProperty("--iters", `${3 + ((Math.random() * 3) | 0)}`); // LINTER IS LIES, HEED NO WARNING

            span.textContent = finalChar;
            frag.appendChild(span);
        }

        el.textContent = "";
        el.appendChild(frag);
        el.dataset.split = "1";
    }

    function playGlitchName (el, opts = {}) {
        const settleMs = opts.settleMs ?? 1200; // LENGTH OF GLITCH EFFECT
        if (el.querySelectorAll('.ch').length === 0) return;
        el.classList.add("is-glitching");

        // after the glitch window, reveal real glyphs
        window.setTimeout(() => {
            el.classList.remove("is-glitching");
        }, settleMs);
    }

    // TODO might be work trying to rework this for metrics
    // function releaseLayoutWhenFontsReady() {
    //     if (!document.fonts || !document.fonts.ready) {
    //         unlockLayout();
    //         return;
    //     }
    //     document.fonts.ready.then(() => {
    //         unlockLayout();
    //     })
    // }
    //
    // function unlockLayout() {
    //     const shell = document.getElementById('app-shell');
    //     if (shell) {
    //         shell.classList.remove('is-intro');
    //     }
    // }


    // ===========================
    // Initialization
    // ===========================

    function initIntro () {
        if (window[INTRO_BOOT_FLAG]) {
            return;
        }

        // Get DOM references
        overlay = document.getElementById('intro-overlay');
        if (!overlay) {
            // console.warn('[intro] #intro-overlay not found, skipping intro');
            return;
        }

        window[INTRO_BOOT_FLAG] = true;
        overlay.classList.add('ready');

        logoBase = overlay.querySelector('.intro-logo-base');
        highlightH = overlay.querySelector('.intro-logo-highlight-h');
        highlightCenter = overlay.querySelector('.intro-logo-highlight-center');
        highlightR = overlay.querySelector('.intro-logo-highlight-r');
        highlightStroke = overlay.querySelector('.intro-logo-highlight-stroke');
        highlightDot = overlay.querySelector('.intro-logo-highlight-dot');
        introName = overlay.querySelector('.intro-name');
        // scrollHint = overlay.querySelector('.intro-scroll-hint');

        if (!logoBase || !introName) {
            // console.warn('[intro] Required elements not found, skipping intro');
            overlay.classList.add('complete');
            return;
        }

        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        addSkipListeners();

        runIntroSequence(prefersReducedMotion);
    }

    // ===========================
    // Entry Point
    // ===========================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initIntro);
    } else {
        initIntro();
    }

})();
