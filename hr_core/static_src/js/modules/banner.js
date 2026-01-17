// hr_core/static_src/js/modules/banner.js

(function () {
    window.hrSite = window.hrSite || {};
    const bannerAPI = {
        setBannerState: function () {},
        setupRecolorObserver: function () {},
        updateFade: function () {}
    };
    window.hrSite.banner = bannerAPI;

    document.addEventListener('DOMContentLoaded', () => {
        const config = (window.hrSite && window.hrSite.config) || {};
        const utils = (window.hrSite && window.hrSite.utils) || {};
        const getVH = utils.getVH || (() =>
            window.innerHeight || document.documentElement.clientHeight
        );

        const BANNER_BUFFER = config.BANNER_BUFFER ?? 2;
        const BANNER_STEP = config.BANNER_STEP ?? 5;

        const banner = document.querySelector('#banner');
        const bannerScroller = document.querySelector('#banner-scroller');
        const banners = banner
            ? banner.querySelectorAll('.banner-row > span')
            : [];
        const firstSectionWipe = document.querySelector('#section-wipe-0');

        const STATE = {
            lastIndexHidden: -1,
            cartShown: null,
            lastBtnOpacity: null
        };

        const navOpenBtn = document.getElementById('nav-open-btn');
        const floatingCartBtn = document.getElementById('floating-cart-btn');

        let recolorObserver = null;

        // Reset letter state on load
        if (banners.length) {
            banners.forEach(b => {
                b.classList.remove('is-visible', 'burn', 'is-fading', 'hidden-once');
                b.style.opacity = '';
            });
        }

        function showBanner(i) {
            if (!banners.length) return;
            const el = banners[i];
            if (!el || el.classList.contains('burn')) return;
            el.classList.remove('blink', 'is-fading', 'hidden-once');
            el.classList.add('burn', 'is-visible');
        }

        function hideBanner(i) {
            if (!banners.length) return;
            const el = banners[i];
            if (!el || el.classList.contains('hidden-once')) return;
            el.classList.add('hidden-once', 'is-fading');
            el.classList.remove('is-visible');
        }

        function setBannerState(scrollTopOverride) {
            if (!banners.length) return;

            const scrollPosition = typeof scrollTopOverride === 'number'
                ? scrollTopOverride
                : window.scrollY;

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
                if (i <= indexToShow && !banners[i].classList.contains('is-visible')) {
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
        function updateFade() {
            if (!banner || !firstSectionWipe) return;

            // const scrollPosition = typeof scrollTopOverride === 'number'
            //     ? scrollTopOverride
            //     : window.scrollY;

            // We want geometry in *viewport* coordinates, not page coords
            const bannerRect = banner.getBoundingClientRect();
            const wipeRect = firstSectionWipe.getBoundingClientRect();

            const bannerBottom = bannerRect.bottom;  // px from top of viewport
            const wipeTop = wipeRect.top;            // px from top of viewport

            // Distance between wipe top and banner bottom
            const distance = wipeTop - bannerBottom;

            // How far below the banner we start fading (full 1 → 0)
            // tweak this to taste: 1–3x banner height is a good range
            const fadeRangePx = (bannerRect.height || 1) * 3;

            let opacity;
            if (distance >= fadeRangePx) {
                // Wipe is comfortably below → fully visible
                opacity = 1;
            } else if (distance <= 0) {
                // Wipe top has reached or passed banner bottom → fully hidden
                opacity = 0;
            } else {
                // Linear fade: distance in [0, fadeRangePx] → opacity in [0,1]
                opacity = distance / fadeRangePx;
            }

            banner.style.opacity = opacity.toFixed(3);

            if (navOpenBtn || floatingCartBtn) {
                const btnOpacity = 1 - opacity;

                if (navOpenBtn) {
                    navOpenBtn.style.opacity = btnOpacity.toFixed(3);
                }

                if (floatingCartBtn) {
                    floatingCartBtn.style.opacity = btnOpacity.toFixed(3);
                    const shouldShow = btnOpacity > 0.001;

                    if (STATE.cartShown !== shouldShow) {
                        STATE.cartShown = shouldShow;

                        const cartAPI = window.hrSite?.cart;
                        if (cartAPI?.show && cartAPI?.hide) {
                            shouldShow ? cartAPI.show() : cartAPI.hide();
                        } else {
                            floatingCartBtn.classList.toggle('is-hidden', !shouldShow);
                        }
                    }
                }
            }
        }

        function setupRecolorObserver() {
            if (!firstSectionWipe || !banner || !banners.length) return;
            if (recolorObserver) return; // already set

            recolorObserver = new IntersectionObserver(entries => {
                entries.forEach(e => {
                    if (!e.isIntersecting && e.boundingClientRect.top < 0) {
                        // wipe has scrolled past the top -> solid banner + orange text
                        banner.style.backgroundColor = 'rgba(0,0,0,1)';
                        banners.forEach(b => {
                            b.style.color = 'darkorange';
                        });
                    } else {
                        // wipe is at/above banner again -> revert
                        banner.style.backgroundColor = '';
                        banners.forEach(b => {
                            b.style.color = '';
                        });
                    }
                });
            }, {
                root: null,
                threshold: 0,
                rootMargin: `-${banner.offsetHeight || 0}px 0px 0px 0px`
            });

            recolorObserver.observe(firstSectionWipe);
        }

        // expose real implementations
        bannerAPI.setBannerState = setBannerState;
        bannerAPI.setupRecolorObserver = setupRecolorObserver;
        bannerAPI.updateFade = updateFade;

        // initial run
        setupRecolorObserver();
        const initialScroll = window.scrollY;
        setBannerState(initialScroll);
        updateFade(initialScroll);
    });
})();
