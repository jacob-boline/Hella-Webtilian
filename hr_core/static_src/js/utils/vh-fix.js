// hr_core/static_src/js/utils/vh-fix.js

export function initVhFix () {
    const ua = navigator.userAgent || "";
    const isIOS = /iP(hone|od|ad)/.test(ua);
    const isSafariIOS = isIOS &&
        /Safari/.test(ua) &&
        !/CriOS|FxiOS|EdgiOS|OPiOS|DuckDuckGo|GSA|YaBrowser/.test(ua);
    const shouldApply = isIOS && !isSafariIOS;

    if (!shouldApply) return;

    const root = document.documentElement;
    root.classList.add("has-vh-fix");

    let lastHeightPx = 0;
    let rafId = 0;
    let lastScrollY = window.scrollY;
    let lastDir = 0;

    const timers = {
        resize: 0,
        scroll: 0
    };

    const measureHeightPx = () => {
        const vv = window.visualViewport;
        return vv && vv.height ? vv.height : window.innerHeight;
    };

    const applyVh = (heightPx) => {
        if (!heightPx) return;
        if (Math.abs(heightPx - lastHeightPx) < 2) return;
        lastHeightPx = heightPx;
        root.style.setProperty("--vh", `${heightPx * 0.01}px`);
    };

    const scheduleImmediate = () => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            rafId = 0;
            applyVh(measureHeightPx());
        });
    };

    const scheduleDebounced = (ms, timerKey) => {
        if (timers[timerKey]) clearTimeout(timers[timerKey]);
        timers[timerKey] = window.setTimeout(() => {
            timers[timerKey] = 0;
            scheduleImmediate();
        }, ms);
    };

    scheduleImmediate();

    window.visualViewport?.addEventListener("resize", () => {
        scheduleDebounced(150, "resize");
    }, {passive: true});

    window.addEventListener("resize", () => {
        scheduleImmediate();
        scheduleDebounced(150, "resize");
    }, {passive: true});

    window.addEventListener("orientationchange", () => {
        scheduleImmediate();
        scheduleDebounced(200, "resize");
    });

    window.addEventListener("scroll", () => {
        const currentY = window.scrollY;
        const dir = currentY > lastScrollY ? 1 : currentY < lastScrollY ? -1 : lastDir;

        if (dir !== lastDir && dir !== 0) {
            scheduleDebounced(150, "scroll");
        }

        lastDir = dir;
        lastScrollY = currentY;

        scheduleDebounced(150, "scroll");
    }, {passive: true});

    window.addEventListener("pageshow", (e) => {
        if (e.persisted) scheduleImmediate();
    });

    document.addEventListener("fullscreenchange", scheduleImmediate);
}
