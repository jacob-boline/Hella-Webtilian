//import lax from '../../../../../node_modules/lax.js/lib/lax.js';
import lax from 'lax.js';

const parallaxConfig = {
    textSpeed: 1.5,
    bgSpeed: 1.0
};


function setParallaxHeights(wrapperSelector, textSelector, bgSelector) {

    const wrappers = document.querySelectorAll(wrapperSelector);

    const calculateHeights = () => {
        wrappers.forEach((wrapper) => {
            const text = wrapper.querySelector(textSelector);
            const bg = wrapper.querySelector(bgSelector);

            if (text && bg) {
                //const textHeight = text.offsetHeight;
                const textHeight = text.getBoundingClientRect().height;
                const parallaxHeight = textHeight * (parallaxConfig.textSpeed/parallaxConfig.bgSpeed);
                // wrapper.style.height = bg.style.height = `${parallaxHeight}px`;
                wrapper.style.height = `${parallaxHeight}px`;
                bg.style.height = `${paralaxHeight}px`;
            }
        });
    };

    //const textResizeObserver = new MutationObserver(calculateHeights);
    const resizeObserver = new ResizeObserver(calculateHeights);

    wrappers.forEach(wrapper => {
        const text = wrapper.querySelector(textSelector);
        //if (text) textResizeObserver.observe(text, { childList: true, subtree: true, characterData: true });
        if (text) resizeObserver.observe(text);
    });

    calculateHeights();
    window.addEventListener("resize", calculateHeights);
}


document.addEventListener("DOMContentLoaded", function() {

    //setParallaxHeights(".parallax-wrapper", ".text-container", ".parallax-bg");
    setParallaxHeights(".parallax-wrapper", ".parallax-content", ".parallax-background");

    try {
        lax.init();
        lax.addDriver("scrollY", () => window.scrollY);
    } catch (error) {
        console.error(`Lax.js failed to initialize: ${error}`);
    }


    const sections = document.querySelectorAll(".parallax-wrapper");

    const observedElements = new Set();

    const parallaxObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                const bg = entry.target.querySelector(".parallax-background");
                const text = entry.target.querySelector(".parallax-content");
                const wipe = entry.target.querySelector('.section-wipe')

                if (entry.isIntersecting && !observedElements.has(entry.target)) {
                    if (bg) {
                        lax.addElements(entry.target.querySelector('.parallax-background'), {
                            scrollY: {
                                translateY: [
                                    ["elInY", "elOutY"],
                                    [0, -200 * parallaxConfig.bgSpeed], // Background moves slower
                                ],
                            },
                        });
                    }
                    if (text) {
                        lax.addElements(text, {
                            scrollY: {
                                translateY: [
                                    ["elInY", "elOutY"],
                                    [0, 200 * parallaxConfig.textSpeed], // Move text
                                ],
                                opacity: [
                                    ["elInY", "elCenterY"],
                                    [0, 1], // Fade in text correctly
                                ],
                            },
                        });
                        console.log(`Lax.js applied opacity to:`, text);
                    }

                    if (wipe) {
                        lax.addElements(wipe, {
                            scrollY: {
                                translateY: [
                                    ["elInY", "elOutY"],
                                    [0, -500],
                                ],
                                opacity: [
                                    ["elInY", "elCenterY"],
                                    [1, 0]
                                ]
                            }
                        });
                    }
                    observedElements.add(entry.target);

                    // if (text) {
                    //      lax.addElements(entry.querySelector(".text-container"), {
                    //         scrollY: {
                    //             translateY: [
                    //                 ["elInY", "elOutY"],
                    //                 [0, 200 * parallaxConfig.textSpeed], // Text moves faster
                    //             ],
                    //             opacity: [
                    //                 ["elInY", "elCenterY"],
                    //                 //["elInY", "elInY+300"],
                    //                 [0, 1], // Fade in text
                    //             ],
                    //         },
                    //     });
                    //     console.log(`Lax.js applied opacity to: ${text}`);
                    // }

                }
            });
        },
        {
            // root: null, // Use standard viewport as the root
            //threshold: 0,
            rootMargin: "100%",
            threshold: 0.1
        }
    );

    // Normal Wipe (First Section Wipe)
    lax.addElements(".section-wipe:not(.flash-wipe)", {
        scrollY: {
            translateY: [
                ["elInY", "elOutY"],
                [0, -500]
            ],
            opacity: [
                ["elInY", "elOutY"],
                [1, 0]
            ]
        }
    });

    // Flash Effect Wipe (Second Wipe)
    lax.addElements(".flash-wipe", {
        scrollY: {
            translateY: [
                ["elInY", "elOutY"],
                [0, -500]
            ],
            opacity: [
                ["elInY", "elInY+200"],  // Quickly flash bright
                [0, 1],                  // 0 -> 100% brightness
                ["elInY+200", "elOutY"], // Then fade out
                [1, 0]                   // 100% -> 0% opacity
            ],
            blur: [
                ["elInY", "elOutY"],
                [20, 0] // Reduce blur as it fades
            ]
        }
    });

    const lazyBackgrounds = document.querySelectorAll("[data-bg]");

    const bgImageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const bgElement = entry.target;
                const bgImage = bgElement.dataset.bg;

                if (bgImage) {
                    const img = new Image();
                    img.src = bgImage;
                    img.onload = () => {
                        bgElement.style.backgroundImage = `url('${bgImage}')`;
                        bgElement.removeAttribute("data-bg");
                        bgElement.classList.add("loaded");
                    }
                    setTimeout(() => observer.unobserve(bgElement), 500);
                }
            }
        });
    }, {
        root: null,
        rootMargin: "100%",
        threshold: 0.01
    });

    sections.forEach(section => parallaxObserver.observe(section));
    lazyBackgrounds.forEach(bg => bgImageObserver.observe(bg));
});
