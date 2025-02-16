const backgrounds = document.querySelectorAll('.parallax-background');

document.addEventListener('DOMContentLoaded', function() {

    let lastIndexHidden = -1;
    const buffer = 2; // 2vh buffer
    const banners = document.querySelectorAll('.banner-letter');
    const step = 8; // Show one banner for every 8vh scrolled
    const banner = document.querySelector('#banner');

    function showBanner(index) {
        if (index >= 0 && index < banners.length) {
            banners[index].style.display = 'inline-block';
            banners[index].classList.add('burn');
        }
    }

    function hideBanner(index) {
        if (index >= 0 && index < banners.length) {
            banners[index].style.color = 'black';
        }
        if (index === banners.length) {
            banner.style.background = 'transparent';
            banners.style.color = 'transparent';
        }
    }

    const handleScroll = (() => {
        const ret = { active: false }
        let timeout;

        ret.activate = function activate() {
            if (ret.active) clearTimeout(timeout)
            else {
                ret.active = true
                requestAnimationFrame(updateParallaxBackgroundPosition);
            }
            timeout = setTimeout(() => ret.active = false, 25)
        }
        return ret
    })()

    const setBannerState = () => {
        const scrollPosition = Math.floor(window.scrollY);
        const vh = Math.floor(window.innerHeight / 100);
        const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
        const indexResetPoint = Math.floor((banners.length * step * vh) + (buffer ** buffer * vh));

        if (indexToShow < banners.length) {
            showBanner(indexToShow);
        } else {
            for (let index = 0; index < banners.length; index++) {
                const threshold = 3 * vh * index + 10 * vh;
                if ((scrollPosition - indexResetPoint) >= threshold && index > lastIndexHidden) {
                    hideBanner(index);
                    lastIndexHidden = index;
                }
            }
        }
    }

    function recolorBanner() {
        const firstSectionWipe = document.getElementById('first-wipe')
        const recolorBannerObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.boundingClientRect.top < 0) {
                    document.querySelector('#banner').style.backgroundColor = 'rgba(0,0,0,1)';
                    banners.forEach(banner => {
                        banner.style.color = "darkorange";
                    });
                }
            });
        });
        recolorBannerObserver.observe(firstSectionWipe)
    }

    function observeForeground() {
        const foregrounds = document.querySelectorAll('.parallax-foreground');

        foregrounds.forEach(foreground => {
            const observer = new IntersectionObserver(entries => {
                entries.forEach(entry => {
                    const section = entry.target.closest('section');
                    if (!section) return;
                    if (entry.intersectionRatio > 0) {
                        const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
                        const distanceFromBottom = vh - entry.boundingClientRect.bottom;
                        if (distanceFromBottom >= 15 * vh / 100) {
                            section.classList.remove('sticky');
                        }
                    }
                });
            }, {
                threshold: 0 // Trigger when any part of the foreground enters the viewport
            });

            observer.observe(foreground);
        });
    }

    const updateParallaxBackgroundPosition = (() => {
        let lastScrollY = 0;  // Track last scroll position to avoid redundant updates

        return () => {
            let windowYOffset = window.scrollY;
            if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if there's little movement

            backgrounds.forEach(function(background) {
                let backgroundPos = windowYOffset * 0.5;
                background.style.backgroundPosition = `50% ${backgroundPos}px`;

                let foreground = background.querySelector('.parallax-foreground');
                if (foreground) {
                    let foregroundPos = windowYOffset * 0.75;
                    foreground.style.backgroundPosition = `50% ${foregroundPos}px`;
                    let foregroundHeight = foreground.clientHeight;
                    background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
                }
            });

            lastScrollY = windowYOffset;  // Update last scroll position

            if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition);
        }
    })();

    updateParallaxBackgroundPosition();

    window.addEventListener('scroll', handleScroll.activate);
    document.addEventListener('DOMContentLoaded', observeForeground);
    recolorBanner();
    window.addEventListener('scroll', setBannerState);

});
