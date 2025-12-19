// hr_core/static/hr_core/js/core-utils.js

(function () {
    const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const defaultConfig = {
        PARALLAX_SCROLL_RATIO: 0.5,
        BANNER_BUFFER: 2,
        BANNER_STEP: 5,
        BANNER_FADE_DISTANCE_VH: 40,
        REDUCED_MOTION
    };

    function debounce(fn, wait = 200) {
        let t;
        return function (...args) {
            clearTimeout(t);
            t = setTimeout(() => fn.apply(this, args), wait);
        };
    }

    // Single source of truth for viewport height
    function getVH() {
        if (window.visualViewport && window.visualViewport.height) {
            return window.visualViewport.height;
        }
        return window.innerHeight || document.documentElement.clientHeight;
    }

    window.hrSite = window.hrSite || {};
    window.hrSite.config = Object.assign({}, window.hrSite.config || {}, defaultConfig);
    window.hrSite.utils = Object.assign({}, window.hrSite.utils || {}, {
        debounce,
        getVH
    });
})();
