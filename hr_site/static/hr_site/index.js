$(() => {

    $("span.inline-block.banner").hide()

    let viewportHeight = $(window).height();

    $(window).resize(function () {
        viewportHeight = $(window).height();
    });

    let scrolled = false;
    let buffer = 76;
    let index = 0;

    const trigger = 76;


    $(document).on("scroll", function () {

        let loadingHeader = $('#header-end').css('display') === 'none';
        let header = document.getElementById("page-header");

        if (loadingHeader) {

            let sticky = header.offsetTop;

            if (window.scrollY > sticky - 400) {
                header.classList.add("sticky");
            } else {
                //$('#page-header').slideUp(500);
                // $('#page-header').removeClass("sticky", 1500);
                // header.classList.remove("sticky");
            }

            if (!scrolled) {
                scrolled = true;
                let toTop = $(window).scrollTop();
                toTop = Math.round(toTop);
                let quotient = Math.floor(toTop / trigger);

                if ((toTop >= trigger) && (quotient > index)) {
                    index = buffer / trigger;
                    $(`span.inline-block.banner:nth-child(${index})`)
                        .addClass('burn')
                        .fadeIn(1000)
                        .removeClass("hidden");
                    buffer += trigger;
                }
                if (index === 2) $('span.inline-block.banner.blink').css('animation', 'none');   //  remove

                scrolled = false;
                return scrolled;
            }
            scrolled = false;
            return scrolled;
        } else {
            $('#page-header').addClass("unstick");
        }
    });

});

$(document).ready(function () {
    let scrollSpeed = 1.0;
    let parallaxSpeed = 0.5;
    let scrollHeightRatio = parallaxSpeed / scrollSpeed;
    let viewportHeight = window.innerHeight;
    let wipes = document.querySelectorAll(".section-wipe");
    let wipeData = {}; // Store scrollSpeedRatio & height for each wipe
    let activeWipe = null; // Currently intersecting wipe
    let ticking = false; // For requestAnimationFrame optimization

    function initializeParallax() {
        document.querySelectorAll('.parallax-section').forEach(section => {
            let content = section.querySelector('.parallax-content');
            let background = section.querySelector('.parallax-background');

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
            let wipeOffset = wipe.getBoundingClientRect().top + window.scrollY;
            wipeData[wipe.id] = {
                scrollSpeedRatio: (viewportHeight + wipe.offsetHeight) / viewportHeight,
                wipeOffset: wipeOffset,
            };
        });
    }

    function positionSectionWipes() {
        document.querySelectorAll('.section-wipe').forEach(wipe => {
            let nextSection = wipe.nextElementSibling;
            if (nextSection && nextSection.classList.contains('parallax-section')) {
                wipe.style.top = `${nextSection.offsetTop}px`;
            }
        });
    }

    function handleScroll() {
        if (!activeWipe || !wipeData[activeWipe.id]) return;

        let scrollPosition = window.scrollY;
        let { scrollSpeedRatio, wipeOffset } = wipeData[activeWipe.id];

        let progress = (scrollPosition - wipeOffset + viewportHeight) / viewportHeight;
        if (progress >= 0) {
            let fasterScroll = (scrollPosition - wipeOffset + viewportHeight) / scrollSpeedRatio;
            activeWipe.style.transform = `translateY(-${fasterScroll}px)`;
        }
    }

    function observeWipes() {
        let observerOptions = { root: null, threshold: 0 };
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
        }, observerOptions);

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

    initializeParallax();
    positionSectionWipes();
    calculateWipeData();
    observeWipes();
    observeElements();

    window.addEventListener('scroll', onScroll);
    window.addEventListener('resize', debounce(() => {
        positionSectionWipes();
        calculateWipeData();
    }));
});
