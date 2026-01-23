// hr_core/static_src/js/modules/banner.js

(function () {
    window.hrSite = window.hrSite || {};
    const bannerAPI = {
        setBannerState: function () {},
        setupRecolorObserver: function () {},
        updateFade: function () {}
    };
    window.hrSite.banner = bannerAPI;

    document.addEventListener("DOMContentLoaded", () => {
        const config = window.hrSite?.config || {};
        const utils = window.hrSite?.utils || {};
        const getVH = utils.getVH || (() => window.innerHeight || document.documentElement.clientHeight);

        const BANNER_BUFFER = config.BANNER_BUFFER ?? 2;
        const BANNER_STEP = config.BANNER_STEP ?? 5;

        const banner = document.querySelector("#banner");
        const bannerScroller = document.querySelector("#banner-scroller");
        const banners = banner ? banner.querySelectorAll(".banner-row > span") : [];
        const firstSectionWipe = document.querySelector("#section-wipe-0");

        const navOpenBtn = document.getElementById("nav-open-btn");
        const floatingCartBtn = document.getElementById("floating-cart-btn");

        let recolorObserver = null;

        const STATE = {
            lastIndexHidden: -1,
            cartShown: null,

            // cache last written opacities so we don't spam style recalcs
            lastBannerOpacity: null,
            lastBtnOpacity: null,

            // cached banner height for observer + fade math
            bannerHeightPx: null
        };

        // Reset letter state on load
        if (banners.length) {
            banners.forEach((b) => {
                b.classList.remove("is-visible", "burn", "is-fading", "hidden-once");
                b.style.opacity = "";
            });
        }

        function showBanner(i) {
            if (!banners.length) return;
            const el = banners[i];
            if (!el || el.classList.contains("burn")) return;
            el.classList.remove("blink", "is-fading", "hidden-once");
            el.classList.add("burn", "is-visible");
        }

        function hideBanner(i) {
            if (!banners.length) return;
            const el = banners[i];
            if (!el || el.classList.contains("hidden-once")) return;
            el.classList.add("hidden-once", "is-fading");
            el.classList.remove("is-visible");
        }

        function setBannerState(scrollTopOverride) {
            if (!banners.length) return;

            const scrollPosition =
                typeof scrollTopOverride === "number" ? scrollTopOverride : window.scrollY;

            let vhPx = getVH();
            if (!vhPx || vhPx <= 0) vhPx = window.innerHeight || 1;
            const vhUnit = Math.max(1, Math.floor(vhPx / 100)); // avoid zero

            const indexToShow = Math.floor(scrollPosition / (BANNER_STEP * vhUnit)) - BANNER_BUFFER;
            const indexResetPoint = bannerScroller
                ? (bannerScroller.offsetTop + bannerScroller.offsetHeight)
                : 0;

            if (scrollPosition < indexResetPoint) {
                STATE.lastIndexHidden = -1;
            }

            for (let i = 0; i < banners.length; i++) {
                if (i <= indexToShow && !banners[i].classList.contains("is-visible")) {
                    showBanner(i);
                } else if (
                    i > indexToShow &&
                    (scrollPosition - indexResetPoint) >= vhUnit * i &&
                    i > STATE.lastIndexHidden
                ) {
                    hideBanner(i);
                    STATE.lastIndexHidden = i;
                }
            }
        }

        // -----------------------------
        // Distance-based fade
        // -----------------------------
        function writeOpacityIfChanged(el, value, key, epsilon = 0.003) {
            // value expected 0..1
            const prev = STATE[key];
            if (prev !== null && Math.abs(value - prev) < epsilon) return;
            STATE[key] = value;
            el.style.opacity = value.toFixed(3);
        }

        function cacheBannerHeight() {
            if (!banner) return;
            // One layout read; we use it everywhere else.
            const h = banner.getBoundingClientRect().height || 0;
            // Avoid tiny jitter updates
            if (STATE.bannerHeightPx !== null && Math.abs(h - STATE.bannerHeightPx) < 0.5) return;
            STATE.bannerHeightPx = h;
        }

        function updateFade() {
            if (!banner || !firstSectionWipe) return;

            // One layout pass: read geometry together
            const bannerRect = banner.getBoundingClientRect();
            const wipeRect = firstSectionWipe.getBoundingClientRect();

            // Cache banner height for reuse (observer + fade range)
            const bannerH = bannerRect.height || STATE.bannerHeightPx || 1;
            STATE.bannerHeightPx = bannerH;

            const bannerBottom = bannerRect.bottom;
            const wipeTop = wipeRect.top;

            // Distance between wipe top and banner bottom (viewport coords)
            const distance = wipeTop - bannerBottom;

            // Fade over ~3x banner height (same as your intent)
            const fadeRangePx = bannerH * 3;

            let opacity;
            if (distance >= fadeRangePx) opacity = 1;
            else if (distance <= 0) opacity = 0;
            else opacity = distance / fadeRangePx;

            writeOpacityIfChanged(banner, opacity, "lastBannerOpacity");

            // Buttons invert opacity
            const btnOpacity = 1 - opacity;

            if (navOpenBtn) {
                // separate cache key so one doesn't suppress the other
                const prev = STATE.lastBtnOpacity;
                if (prev === null || Math.abs(btnOpacity - prev) >= 0.003) {
                    navOpenBtn.style.opacity = btnOpacity.toFixed(3);
                }
            }

            if (floatingCartBtn) {
                // keep same cache key for both buttons
                const prev = STATE.lastBtnOpacity;
                if (prev === null || Math.abs(btnOpacity - prev) >= 0.003) {
                    floatingCartBtn.style.opacity = btnOpacity.toFixed(3);
                    STATE.lastBtnOpacity = btnOpacity;
                }

                // Only toggle visibility state when it actually changes
                const shouldShow = btnOpacity > 0.001;
                if (STATE.cartShown !== shouldShow) {
                    STATE.cartShown = shouldShow;

                    const cartAPI = window.hrSite?.cart;
                    if (cartAPI?.show && cartAPI?.hide) {
                        shouldShow ? cartAPI.show() : cartAPI.hide();
                    } else {
                        floatingCartBtn.classList.toggle("is-hidden", !shouldShow);
                    }
                }
            }
        }

        // -----------------------------
        // Recolor observer
        // -----------------------------
        function teardownRecolorObserver() {
            if (recolorObserver) recolorObserver.disconnect();
            recolorObserver = null;
        }

        function setupRecolorObserver() {
            if (!firstSectionWipe || !banner || !banners.length) return;

            // If banner height changed, rebuild the observer so rootMargin stays correct.
            cacheBannerHeight();
            const marginTop = -(Math.round(STATE.bannerHeightPx || 0));

            teardownRecolorObserver();

            recolorObserver = new IntersectionObserver(
                (entries) => {
                    entries.forEach((e) => {
                        if (!e.isIntersecting && e.boundingClientRect.top < 0) {
                            banner.style.backgroundColor = "rgba(0,0,0,1)";
                            banners.forEach((b) => (b.style.color = "darkorange"));
                        } else {
                            banner.style.backgroundColor = "";
                            banners.forEach((b) => (b.style.color = ""));
                        }
                    });
                },
                {
                    root: null,
                    threshold: 0,
                    rootMargin: `${marginTop}px 0px 0px 0px`
                }
            );

            recolorObserver.observe(firstSectionWipe);
        }

        // Expose real implementations
        bannerAPI.setBannerState = setBannerState;
        bannerAPI.setupRecolorObserver = setupRecolorObserver;
        bannerAPI.updateFade = updateFade;

        // Initial run
        cacheBannerHeight();
        setupRecolorObserver();

        const initialScroll = window.scrollY;
        setBannerState(initialScroll);
        updateFade();

        // If banner height can change due to font loads, rebuild observer once fonts settle
        document.fonts?.ready?.then?.(() => {
            cacheBannerHeight();
            setupRecolorObserver();
            updateFade();
        });

        // If viewport changes, banner height / geometry changes
        window.addEventListener("resize", () => {
            cacheBannerHeight();
            setupRecolorObserver();
            updateFade();
        }, { passive: true });

        window.visualViewport?.addEventListener("resize", () => {
            cacheBannerHeight();
            setupRecolorObserver();
            updateFade();
        }, { passive: true });
    });
})();
