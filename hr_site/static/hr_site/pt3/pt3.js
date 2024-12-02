/* jshint esversion: 6 */

// Check screen orientation
function setRootFontSize() {
    const root = document.documentElement;
    if (window.innerHeight > window.innerWidth) {
        // Portrait orientation
        root.style.setProperty('--root-font-size', '10px');
    } else {
        // Landscape orientation
        root.style.setProperty('--root-font-size', '20px');
    }
}

// Call setRootFontSize initially and on orientation change
setRootFontSize();
window.addEventListener('resize', setRootFontSize);

const backgrounds = document.querySelectorAll('.parallax-background');

document.addEventListener('DOMContentLoaded', function() {

    let lastIndexHidden = -1;
    const buffer = 2;
    const banners = document.querySelectorAll('.banner-letter');
    const step = 8;
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

const setBannerState = () => {
    const scrollPosition = Math.floor(window.scrollY);
    const vh = Math.floor(window.innerHeight / 100);
    const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
    const indexResetPoint = Math.floor((banners.length * step * vh) + (buffer ** buffer * vh));

    // Show the banner for the current index and all preceding indexes that haven't been shown yet
    if (indexToShow < banners.length) {
        for (let i = 0; i <= indexToShow; i++) {
            if (banners[i].style.display !== 'inline-block') {
                showBanner(i);
            }
        }
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
        const firstSectionWipe = document.getElementById('first-wipe');
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
        recolorBannerObserver.observe(firstSectionWipe);
    }

    function observeForeground() {
        const foregrounds = document.querySelectorAll('.parallax-foreground');

        foregrounds.forEach(foreground => {
            const observer = new IntersectionObserver(entries => {
                entries.forEach(entry => {
                    const section = entry.target.closest('section');
                    if (!section) return; // If no section ancestor found, exit
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

    // The main parallax update function with smoothing and throttling
    const updateParallaxBackgroundPosition = (() => {
        let lastScrollY = 0;            // Track last scroll position to avoid redundant updates
        let lastBackgroundPos = 0;      // For smoothing the background position
        let lastForegroundPos = 0;      // For smoothing the foreground position

        const smoothFactor = 0.3; //0.1;       // A factor to smooth the transition (higher = more smoothing)

        return () => {
            let windowYOffset = window.scrollY;
            if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if there's little movement

            // Smooth transition for background position
            let backgroundPos = windowYOffset * 0.5;
            let smoothedBackgroundPos = lastBackgroundPos + (backgroundPos - lastBackgroundPos) * smoothFactor;
            lastBackgroundPos = smoothedBackgroundPos;

            // Update the background position
            backgrounds.forEach(function(background) {
                background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;

                let foreground = background.querySelector('.parallax-foreground');
                if (foreground) {
                    // Smooth transition for foreground position
                    let foregroundPos = windowYOffset * 0.75;
                    let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor;
                    lastForegroundPos = smoothedForegroundPos;

                    // Update foreground position
                    foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;

                    // Optionally adjust height for smoother scrolling
                    let foregroundHeight = foreground.clientHeight;
                    background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
                }
            });

            lastScrollY = windowYOffset;  // Update last scroll position

            // Request the next animation frame if needed
            if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition);
        }
    })();

    // Handle scroll event with throttling
    const handleScroll = (() => {
        const ret = { active: false };
        let timeout;

        ret.activate = function activate() {
            if (ret.active) clearTimeout(timeout);
            else {
                ret.active = true;
                requestAnimationFrame(updateParallaxBackgroundPosition);
            }
            timeout = setTimeout(() => ret.active = false, 50);  // Throttling to reduce unnecessary calls
        };
        return ret;
    })();

    // Attach the scroll event listener
    window.addEventListener('scroll', handleScroll.activate);

    // Initialize the parallax effect when the page is loaded
    document.addEventListener('DOMContentLoaded', () => {
        updateParallaxBackgroundPosition();
    });

    updateParallaxBackgroundPosition();

    window.addEventListener('scroll', handleScroll.activate);

    document.addEventListener('DOMContentLoaded', observeForeground);
    recolorBanner();
    window.addEventListener('scroll', setBannerState);
});
