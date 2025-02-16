$(document).load(function() {

    // $("span.inline-block.banner").hide();
    //
    // let viewportHeight = $(window).height();
    //
    // $(window).resize(function () {
    //     viewportHeight = $(window).height();
    // });
    //
    // let scrolled = false;
    // let buffer = 76;
    // let index = 0;
    //
    // const trigger = 76;
    //
    // $(document).on("scroll", function () {
    //
    //     let loadingHeader = $('#header-end').css('display') === 'none';
    //     let header = document.getElementById("page-header");
    //
    //     if (loadingHeader) {
    //
    //         let sticky = header.offsetTop;
    //
    //         if (window.scrollY > sticky - 400) {
    //             header.classList.add("sticky");
    //         } else {
    //             //$('#page-header').slideUp(500);
    //             // $('#page-header').removeClass("sticky", 1500);
    //             // header.classList.remove("sticky");
    //         }
    //
    //         if (!scrolled) {
    //             scrolled = true;
    //             let toTop = $(window).scrollTop();
    //             toTop = Math.round(toTop);
    //             let quotient = Math.floor(toTop / trigger);
    //
    //             if ((toTop >= trigger) && (quotient > index)) {
    //                 index = buffer / trigger;
    //                 $(`span.inline-block.banner:nth-child(${index})`)
    //                     .addClass('burn')
    //                     .fadeIn(1000)
    //                     .removeClass("hidden");
    //                 buffer += trigger;
    //             }
    //             scrolled = false;
    //             return scrolled;
    //         }
    //         scrolled = false;
    //         return scrolled;
    //     } else {
    //         $('#page-header').addClass("unstick");
    //     }
    // });

    document.addEventListener('DOMContentLoaded', () => {
        setupWipeEffects();
        window.addEventListener('scroll', handleScroll);
    });


    function handleScroll() {
        handleStickySections();
        handleParallaxEffects();
    }

    function handleStickySections() {
        const sections = document.querySelectorAll('.sticky-section');
        sections.forEach(section => {
            const sectionTop = section.getBoundingClientRect().top;
            if (sectionTop <= 0) {
                section.classList.add('sticky')
            } else {
                section.classList.remove('sticky');
            }
        });
    }

    function setupWipeEffects() {
        const wipeSections = document.querySelectorAll('.wipe-section');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, {threshold: [0.5]});

        wipeSections.forEach(section => {
            observer.observe(section);
        })
    }

    function handleParallaxEffects() {
        const parallaxSections = document.querySelectorAll('.parallax-section');
        parallaxSections.forEach(section => {
            const offset = window.scrollY - section.offsetTop;
            section.querySelector('.parallax-background').style.transform = `translateY(${offset * 0.5}px)`;
        });
    }

});