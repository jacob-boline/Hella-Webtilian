document.addEventListener("DOMContentLoaded", function () {

    const button = document.querySelector('.text-left button');
    const sidebar = document.querySelector('#drawer-navigation');
    const sidebarCloseButton = document.querySelector('[data-drawer-hide="drawer-navigation"]');
    const drawerTarget = document.querySelector('[data-drawer-target="drawer-navigation"]');

    sidebar.classList.add('-translate-x-full');

    let parallaxSpeed = 0.5;
    let wipes = document.querySelectorAll(".section-wipe");
    let wipeData = {};
    let activeWipe = null;
    let ticking = false;
    let lastIndexHidden = -1;

    const buffer = 2;
    const banners = document.querySelectorAll('.banner-letter');
    const step = 5;//6;//8;
    const banner = document.querySelector('#banner');
    const sectionWipe0 = document.querySelector('#section-wipe-0');
    const bannerRow = document.querySelector('.banner-row');

    let isBannerTransparent = false;

    function showBanner(index) {
        if (0 <= index && index < banners.length) {
            banners[index].style.display = 'inline-block';
            banners[index].classList.add('burn');
            banners[index].style.transition = 'color 0.25s ease-in, text-shadow 0.25.s ease-in-out';
        }
    }

    function hideBanner(index) {
        if (0 <= index && index < banners.length) {
            // Apply initial flash effect
            banners[index].style.color =  'rgb(0, 212, 255)'; // Flash color
            banners[index].style.transition = 'color 0.3s ease-out, opacity 0.5s ease-out, text-shadow 0.25s ease-out'; // Quick flash transition
            banners[index].style.textShadow = '0 0 10px rgba(255, 255, 255, 0.9)';

            // After a short time, transition to the next effect
            setTimeout(() => {
                banners[index].style.color = 'rgb(255, 255, 255)';
                banners[index].style.transition = 'color 3s ease, opacity 3s ease-out, text-shadow 3s ease-out'; // Longer smooth transition

                // After another time, apply the final transition effect
                setTimeout(() => {
                    banners[index].style.color = 'rgb(0,0,0)';
                    banners[index].style.opacity = '0';
                    banners[index].style.textShadow = '0 0 10px rgba(255, 255, 255, 0.8)';
                }, 500); // Delay before final fade-out
            }, 250); // Short delay before applying the second effect
        }
        if (index === banners.length) {
            banner.style.background = 'transparent';
            banners.style.color = 'transparent';
        }
    }

    function recolorBanner() {
        const firstSectionWipe = document.getElementById('section-wipe-0');
        const recolorBannerObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.boundingClientRect.top < 0) {
                    document.querySelector('#banner').style.backgroundColor = 'rgba(0,0,0,1)';
                    banners.forEach(banner => {
                        banner.style.color = "darkorange";
                        banner.style.opacity = '1';
                    });
                }
            });
        });
        recolorBannerObserver.observe(firstSectionWipe);
    }

    const setBannerState = () => {
        console.log('top of setBannerState');
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
                const threshold = vh * index + ((10+index) * vh);
                if ((scrollPosition - indexResetPoint) >= threshold && index > lastIndexHidden) {
                    hideBanner(index);
                    lastIndexHidden = index;
                }
            }
        }
    }

    function initializeParallax() {
        document.querySelectorAll('.parallax-section').forEach(section => {
            let content = section.querySelector('.parallax-content');
            let background = section.querySelector('.parallax-background');
            let viewportHeight = document.documentElement.clientHeight;
            let adjustedHeight = Math.max(content.offsetHeight, viewportHeight);
            section.style.height = `${adjustedHeight}px`;
            background.style.height = `${adjustedHeight}px`;
        });
    }

    function updateParallax(scrollTop) {
        document.querySelectorAll('.parallax-section.in-view').forEach(section => {
            let sectionOffset = section.offsetTop;
            let background = section.querySelector('.parallax-background');
            background.style.transform = `translateY(${(scrollTop - sectionOffset) * parallaxSpeed}px)`;
        });
    }

    function calculateWipeData() {
        wipes.forEach(wipe => {
            let wipeHeight = wipe.getBoundingClientRect().height;
            let viewportHeight = document.documentElement.clientHeight - 30;
            let scrollSpeedRatio = (viewportHeight + wipeHeight) / viewportHeight;
            let wipeOffset = wipe.getBoundingClientRect().top + window.scrollY;
            wipeData[wipe.id] = { scrollSpeedRatio, wipeOffset };
        });
    }

    function positionSectionWipes() {
        document.querySelectorAll('.section-wipe').forEach(wipe => {
            let nextSection = wipe.nextElementSibling;
            if (nextSection && nextSection.classList.contains('parallax-section')) {
                wipe.style.top = `${nextSection.getBoundingClientRect().top + window.scrollY}px`;
                let currentHeight = wipe.offsetHeight;
                wipe.style.height = `${currentHeight + 30}px`;
            }
        });
    }

    function handleScroll() {
        if (!activeWipe || !wipeData[activeWipe.id]) return;

        let scrollPosition = window.scrollY;
        let { scrollSpeedRatio, wipeOffset } = wipeData[activeWipe.id];
        let viewportHeight = document.documentElement.clientHeight;
        let progress = (scrollPosition - wipeOffset + viewportHeight) / viewportHeight;
        if (progress >= 0) {
            let fasterScroll = (scrollPosition - wipeOffset + viewportHeight) / scrollSpeedRatio;
            activeWipe.style.transform = `translateY(-${fasterScroll}px)`;
        }
    }

    function observeWipes() {
        let observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    activeWipe = entry.target;
                    window.addEventListener("scroll", handleScroll);
                } else if (activeWipe === entry.target) {
                    activeWipe = null;
                    window.removeEventListener("scroll", handleScroll);
                }
            });
        }, { threshold: 0 });

        wipes.forEach(wipe => observer.observe(wipe));
    }

    function observeElements() {
        let observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                } else {
                    entry.target.classList.remove('in-view');
                }
            });
        }, { threshold: 0 });

        document.querySelectorAll('.parallax-section').forEach(section => observer.observe(section));
    }

    function onScroll() {
        if (!ticking) {
            ticking = true;
            requestAnimationFrame(() => {
                updateParallax(window.scrollY);
                ticking = false;
            });
        }
    }

    function debounce(func, wait = 200) {
        let timeout;
        return function () {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, arguments), wait);
        };
    }

    function addSidebarListener() {
        drawerTarget.addEventListener('click', function() {
            button.style.opacity = '0';
            button.style.pointerEvents = 'none';
            sidebar.classList.toggle('show');
            sidebar.classList.toggle('-translate-x-full');
            sidebar.classList.toggle('translate-x-0');
        });
    }

    function addCloseSidebarBtnListener() {
        sidebarCloseButton.addEventListener('click', function() {
            button.style.opacity = '1';
            button.style.pointerEvents = 'auto';
            sidebar.classList.remove('show');
            sidebar.classList.add('-translate-x-full');
            sidebar.classList.remove('translate-x-0');
        });
    }


    function addBannerObserver() {
    //const bannerRow = document.querySelector('.banner-row');
    //const sectionWipe0 = document.getElementById('section-wipe-0');

    // Flag to prevent multiple transitions
    //let isBannerTransparent = false;

    const bannerObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!isBannerTransparent && entry.isIntersecting) {
                // When the top of #section-wipe-0 reaches the bottom of .banner-row
                bannerRow.style.transition = 'opacity 0.1s ease-in-out';
                bannerRow.style.opacity = '0';
                banner.style.transition = 'opacity 0.1s ease=in-out';
                banner.style.opacity = '0';
                isBannerTransparent = true;
            }
        });
    }, {
        root: null, // Use the viewport as the root
        threshold: 0, // Trigger when any part of #section-wipe-0 comes into view
        rootMargin: '0px 0px -100% 0px' // Set the bottom margin to trigger when #section-wipe-0 enters after the .banner-row
    });

    bannerObserver.observe(sectionWipe0);
}


    // function addBannerObserver() {
    //     const bannerObserver = new IntersectionObserver(entries => {
    //         entries.forEach(entry => {
    //             if (!isBannerTransparent && entry.isIntersecting) {
    //                 bannerRow.style.transition = 'opacity 0.3s ease';
    //                 bannerRow.style.opacity = '0';
    //                 isBannerTransparent = true;
    //             }
    //         });
    //     }, {
    //         root: null,
    //         threshold: 0
    //     });
    //
    //     bannerObserver.observe(sectionWipe0);
    // }

    initializeParallax();
    positionSectionWipes();
    calculateWipeData();
    observeWipes();
    observeElements();
    recolorBanner();
    addSidebarListener();
    addCloseSidebarBtnListener();
    addBannerObserver();

    window.addEventListener('scroll', () => {
        onScroll();
        setBannerState();
    });

    window.addEventListener('resize', debounce(() => {
        positionSectionWipes();
        calculateWipeData();
    }));
});