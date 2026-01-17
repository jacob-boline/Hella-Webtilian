// hr_core/static_src/js/utils/vh-fix.js

(() => {
    const setVH = () => {
        const vh = (window.visualViewport?.height ?? window.innerHeight) * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    setVH();

    window.addEventListener('resize', setVH, {passive: true});
    window.addEventListener('orientationchange', setVH);
    window.visualViewport?.addEventListener('resize', setVH, {passive: true});

    window.addEventListener('pageshow', (e) => {
        if (e.persisted) { setVH(); }
    });
    document.addEventListener('fullscreenchange', setVH);

    let raf;
    ['scroll', 'resize'].forEach(evt => {
        window.addEventListener(evt, () => {
            cancelAnimationFrame(raf);
            raf = requestAnimationFrame(setVH);
        }, {passive: true});
    });
})();
