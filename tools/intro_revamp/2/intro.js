// tools/intro_revamp/2/intro.js

(function () {
    'use strict';

    // ===========================
    // Configuration & Timing
    // ===========================
    
    const TIMINGS = {
        logoFadeIn: 150,
        
        highlightH: {
            start: 150,
            duration: 200
        },
        highlightR: {
            start: 370,
            duration: 200
        },
        highlightStroke: {
            start: 590,
            duration: 150
        },
        highlightDot: {
            start: 760,
            duration: 150
        },
        
        lockIn: {
            start: 850,
            duration: 350
        },
        
        hold: 500,
        
        yield: {
            start: 1700,
            duration: 400
        },
        
        total: 2100,
        
        hintIdleDelay: 1200,
        hintNudgeDuration: 500
    };

    // ===========================
    // State Management
    // ===========================
    
    const STATE = {
        phase: 'inactive',
        timeouts: [],
        startTime: null,
        skipRequested: false,
        hintNudgeTriggered: false,
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
    let scrollHint = null;

    // ===========================
    // Utilities
    // ===========================
    
    function clearAllTimeouts() {
        STATE.timeouts.forEach(id => clearTimeout(id));
        STATE.timeouts = [];
    }

    function addTimeout(fn, delay) {
        const id = setTimeout(() => {
            STATE.timeouts = STATE.timeouts.filter(t => t !== id);
            fn();
        }, delay);
        STATE.timeouts.push(id);
        return id;
    }

    function pulseHighlight(element, duration) {
        if (!element) return;
        element.classList.add('pulse');
        addTimeout(() => {
            element.classList.remove('pulse');
        }, duration);
    }

    // ===========================
    // Animation Sequence
    // ===========================
    
    function runIntroSequence(prefersReducedMotion) {
        if (prefersReducedMotion) {
            runReducedMotionSequence();
            return;
        }

        STATE.phase = 'active';
        STATE.startTime = performance.now();
        overlay.classList.add('active');

        // Phase 1: Logo fade-in (0-150ms)
        // Logo starts at 0.35 opacity via CSS

        // Phase 2: Diagnostic highlights (150-850ms)
        addTimeout(() => {
            pulseHighlight(highlightH, TIMINGS.highlightH.duration);
            pulseHighlight(highlightCenter, TIMINGS.highlightH.duration); // Shared vertical pulses with H
        }, TIMINGS.highlightH.start);

        addTimeout(() => {
            pulseHighlight(highlightR, TIMINGS.highlightR.duration);
            pulseHighlight(highlightCenter, TIMINGS.highlightR.duration); // Shared vertical pulses with R
        }, TIMINGS.highlightR.start);

        addTimeout(() => {
            pulseHighlight(highlightStroke, TIMINGS.highlightStroke.duration);
        }, TIMINGS.highlightStroke.start);

        addTimeout(() => {
            pulseHighlight(highlightDot, TIMINGS.highlightDot.duration);
        }, TIMINGS.highlightDot.start);

        // Phase 3: Identity lock-in (850-1200ms)
        addTimeout(() => {
            logoBase.classList.add('locked');
            introName.classList.add('visible');
        }, TIMINGS.lockIn.start);

        // Phase 4: Hold (1200-1700ms)
        // Just waiting

        // Phase 5: Yield (1700-2100ms)
        addTimeout(() => {
            yieldToSite();
        }, TIMINGS.yield.start);
    }

    function runReducedMotionSequence() {
        STATE.phase = 'active';
        overlay.classList.add('active');

        // Show everything immediately
        logoBase.classList.add('locked');
        logoBase.style.opacity = '1';
        introName.classList.add('visible');

        // Brief display, then yield
        addTimeout(() => {
            yieldToSite();
        }, 800);
    }

    function yieldToSite() {
        if (STATE.phase === 'complete') return;
        
        STATE.phase = 'yielding';
        overlay.classList.remove('active');
        overlay.classList.add('yielding');

        addTimeout(() => {
            completeIntro();
        }, TIMINGS.yield.duration);
    }

    function completeIntro() {
        STATE.phase = 'complete';
        overlay.classList.add('complete');
        
        // Show scroll hint
        showScrollHint();
        
        // Remove skip listeners
        removeSkipListeners();
    }

    // ===========================
    // Skip/Accelerate Logic
    // ===========================
    
    function skipIntro() {
        if (STATE.phase !== 'active') return;
        
        STATE.skipRequested = true;
        clearAllTimeouts();
        
        yieldToSite();
    }

    function handleWheel() {
        skipIntro();
    }

    function handleTouchStart() {
        skipIntro();
    }

    function handleTouchMove() {
        skipIntro();
    }

    function handleKeyDown(event) {
        const skipKeys = ['ArrowDown', 'PageDown', ' '];
        if (skipKeys.includes(event.key)) {
            skipIntro();
        }
    }

    function addSkipListeners() {
        window.addEventListener('wheel', handleWheel, { passive: true });
        window.addEventListener('touchstart', handleTouchStart, { passive: true });
        window.addEventListener('touchmove', handleTouchMove, { passive: true });
        window.addEventListener('keydown', handleKeyDown);
    }

    function removeSkipListeners() {
        window.removeEventListener('wheel', handleWheel);
        window.removeEventListener('touchstart', handleTouchStart);
        window.removeEventListener('touchmove', handleTouchMove);
        window.removeEventListener('keydown', handleKeyDown);
    }

    // ===========================
    // Scroll Hint (Post-Intro)
    // ===========================
    
    function showScrollHint() {
        if (!scrollHint) return;

        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // Fade in hint
        scrollHint.classList.add('visible');

        // Add interaction listeners
        addHintInteractionListeners();

        // Trigger nudge after idle delay (if not reduced motion)
        if (!prefersReducedMotion && !STATE.hintNudgeTriggered) {
            addTimeout(() => {
                if (!STATE.interactionDetected) {
                    triggerHintNudge();
                }
            }, TIMINGS.hintIdleDelay);
        }
    }

    function triggerHintNudge() {
        if (!scrollHint || STATE.hintNudgeTriggered) return;
        
        STATE.hintNudgeTriggered = true;
        scrollHint.classList.add('nudge');
        
        addTimeout(() => {
            scrollHint.classList.remove('nudge');
        }, TIMINGS.hintNudgeDuration);
    }

    function hideScrollHint() {
        if (!scrollHint || STATE.interactionDetected) return;
        
        STATE.interactionDetected = true;
        scrollHint.classList.add('interacted');
        
        // Remove hint and overlay after fade
        addTimeout(() => {
            if (overlay) {
                overlay.remove();
            }
        }, 400);
        
        removeHintInteractionListeners();
    }

    function handleHintInteraction() {
        hideScrollHint();
    }

    function addHintInteractionListeners() {
        window.addEventListener('scroll', handleHintInteraction, { passive: true, once: true });
        window.addEventListener('wheel', handleHintInteraction, { passive: true, once: true });
        window.addEventListener('touchstart', handleHintInteraction, { passive: true, once: true });
    }

    function removeHintInteractionListeners() {
        window.removeEventListener('scroll', handleHintInteraction);
        window.removeEventListener('wheel', handleHintInteraction);
        window.removeEventListener('touchstart', handleHintInteraction);
    }

    // ===========================
    // Initialization
    // ===========================
    
    function initIntro() {
        // Get DOM references
        overlay = document.getElementById('intro-overlay');
        if (!overlay) {
            console.warn('[intro] #intro-overlay not found, skipping intro');
            return;
        }

        logoBase = overlay.querySelector('.intro-logo-base');
        highlightH = overlay.querySelector('.intro-logo-highlight-h');
        highlightCenter = overlay.querySelector('.intro-logo-highlight-center');
        highlightR = overlay.querySelector('.intro-logo-highlight-r');
        highlightStroke = overlay.querySelector('.intro-logo-highlight-stroke');
        highlightDot = overlay.querySelector('.intro-logo-highlight-dot');
        introName = overlay.querySelector('.intro-name');
        scrollHint = overlay.querySelector('.intro-scroll-hint');

        if (!logoBase || !introName) {
            console.warn('[intro] Required elements not found, skipping intro');
            overlay.classList.add('complete');
            return;
        }

        // Check reduced motion preference
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // Add skip listeners
        addSkipListeners();

        // Start intro sequence
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
