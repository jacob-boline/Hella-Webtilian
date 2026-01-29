// hr_core/static_src/js/utils/vh-fix.js

(() => {
    let last = null;
    let raf = null;

    const computeVH = () => {
        const h = window.visualViewport?.height ?? window.innerHeight;
        return Math.max(1, h) * 0.01;
    };

    const setVH = () => {
        raf = null;
        const vh = computeVH();

        if (last !== null && Math.abs(vh - last) < 0.5 * 0.01) return; // ~0.5px threshold
        last = vh;

        document.documentElement.style.setProperty("--vh", `${vh}px`);
    };

    const scheduleSetVH = () => {
        if (raf) return;
        raf = requestAnimationFrame(setVH);
    };

    setVH();

    window.addEventListener("resize", scheduleSetVH, {passive: true});
    window.addEventListener("orientationchange", scheduleSetVH);
    window.visualViewport?.addEventListener("resize", scheduleSetVH, {passive: true});

    window.addEventListener("pageshow", (e) => {
        if (e.persisted) setVH();
    });

    document.addEventListener("fullscreenchange", scheduleSetVH);
})();
