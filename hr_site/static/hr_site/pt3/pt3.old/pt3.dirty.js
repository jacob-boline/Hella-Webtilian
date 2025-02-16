/* jshint esversion: 6 */


// // // Check screen orientation
// // function setRootFontSize() {
// //   const root = document.documentElement;
// //   if (window.innerHeight > window.innerWidth) {
// //     // Portrait orientation
// //     root.style.setProperty('--root-font-size', '10px');
// //   } else {
// //     // Landscape orientation
// //     root.style.setProperty('--root-font-size', '20px');
// //   }
// // }
// //
// // // Call setRootFontSize initially and on orientation change
// // setRootFontSize();
// // window.addEventListener('resize', setRootFontSize);
//
// let lastIndexHidden = -1;
// const buffer = 2; // represents 2vh
// const banners = document.querySelectorAll('.banner-letter');
// const step = 8; // Show one banner for every 8vh scrolled
// const banner = document.querySelector('#banner');
//
//
//
// document.addEventListener('DOMContentLoaded', function() {
//     // const banners = document.querySelectorAll('.banner-letter');
//     // const buffer = 2; // 2vh buffer at the beginning
//     // const step = 8; // Show one banner for every 8vh scrolled
//
//
//
//     function showBanner(index) {
//         if (index >= 0 && index < banners.length) {
//             banners[index].style.display = 'inline-block';
//             banners[index].classList.add('burn');
//         }
//     }
//
//     function hideBanner(index) {
//         if (index >= 0 && index < banners.length) {
//             banners[index].style.color = 'black';
//         }
//         if (index === banners.length) {
//             banner.style.background = 'transparent';
//             banners.style.color = 'transparent';
//         }
//     }
//
//     function handleScroll() {
//         const scrollPosition = Math.floor(window.scrollY);
//         const vh = Math.floor(window.innerHeight / 100);
//         const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
//         const indexResetPoint = Math.floor((banners.length * step * vh) + (buffer**buffer * vh));
//
//         if (indexToShow < banners.length) {
//             showBanner(indexToShow);
//         } else {
//             for (let index = 0; index < banners.length; index++) {
//                 const threshold = 2.5 * vh * index;
//                 if (((scrollPosition - indexResetPoint) >= threshold) && (index > lastIndexHidden)) {
//                     hideBanner(index);
//                     lastIndexHidden = index;
//                 }
//             }
//         }
//     }
//
//     // function observeContentSections(callback) {
//     //     const contentSections = document.querySelectorAll('.content-section');
//     //
//     //     const contentSectionObserver = new IntersectionObserver(entries => {
//     //         entries.forEach(entry => {
//     //             if (entry.isIntersecting) {
//     //                 console.log('Observing: ', entry.prop('id'));
//     //                 callback(entry.target, true); // Element entered viewport
//     //             } else {
//     //                 console.log('Leaving observation: ', entry.prop('id'));
//     //                 callback(entry.target, false); // Element exited viewport
//     //             }
//     //         });
//     //     });
//     //
//     //     contentSections.forEach(element => {
//     //         contentSectionObserver.observe(element);
//     //     });
//     // }
//
// // Example usage:
// //     observeContentSections((element, enteredViewport) => {
// //         if (enteredViewport) {
// //             console.log('Element entered viewport:', element);
// //             let parallaxBackground = element.querySelector('.parallax-background');
// //             let parallaxForeground = parallaxBackground.querySelector('.parallax-foreground');
// //             // let parallaxForeground = element.querySelector('.parallax-foregroound');
// //             parallaxBackground.style.setProperty('--translateY', '10px');
// //             parallaxForeground.style.setProperty('--translateY', '15px');
// //             // Do something when element enters viewport
// //         } else {
// //             console.log('Element exited viewport:', element);
// //             // Do something when element exits viewport
// //     }
// // });
// //     function showBanner(index) {
// //         if (index < banners.length) {
// //             banners[index].style.display = 'inline-block';
// //         }
// //     }
// //
// //     function handleScroll() {
// //         const scrollPosition = window.scrollY || window.pageYOffset;
// //         const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
// //         const scrolledVh = scrollPosition / vh;
// //         const indexToShow = Math.floor(scrolledVh / step) - buffer;
// //
// //         showBanner(indexToShow);
// //     }
//
// // function makeSticky(entries, observer) {
// //         entries.forEach(entry => {
// //             if (entry.isIntersecting) {
// //                 const section = entry.target;
// //                 section.classList.add('sticky');
// //                 observer.unobserve(section);
// //             }
// //         });
// //     }
//
// function makeSticky(entries, observer) {
//     entries.forEach(entry => {
//         if (entry.isIntersecting) {
//             const background = entry.target;
//             background.classList.add('sticky');
//             //background.style.top = '10vh';
//             observer.unobserve(background);
//         }
//     });
// }
//
// function observeBackground() {
//     const backgrounds = document.querySelectorAll('.parallax-background');
//     const observer = new IntersectionObserver(makeSticky, { threshold: 1 });
//     backgrounds.forEach(background => {
//         observer.observe(background);
//     });
// }
//
// function observeForeground() {
//     const foregrounds = document.querySelectorAll('.parallax-foreground');
//
//     foregrounds.forEach(foreground => {
//         const observer = new IntersectionObserver(entries => {
//             entries.forEach(entry => {
//                 const section = entry.target.closest('section');
//                 if (!section) return; // If no section ancestor found, exit
//                 if (entry.intersectionRatio > 0) {
//                     const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
//                     const distanceFromBottom = vh - entry.boundingClientRect.bottom;
//                     if (distanceFromBottom >= 15 * vh / 100) {
//                         section.classList.remove('sticky');
//                     }
//                 }
//             });
//         }, {
//             threshold: 0 // Trigger when any part of the foreground enters the viewport
//         });
//
//         observer.observe(foreground);
//     });
// }
//
//     function observeWipe() {
//         // console.log('observeWipe called');
//         // const firstSectionWipe = document.querySelector('.img-wrapper:first-of-type img');
//         const firstSectionWipe = document.querySelector('#page-wrapper > div:first-of-type img');
//         if (!firstSectionWipe) {
//             console.error('could not find the target element for intersection observation');
//         }
//         const firstWipeObserver = new IntersectionObserver(entries => {
//             // console.log('callback firstWipeObserver called');
//             entries.forEach(entry => {
//                 if (entry.isIntersecting) {
//                     const bannerLetters = document.querySelectorAll('.banner-letter');
//                     // bannerLetters.style.color = 'darkorange';
//                     bannerLetters.forEach(letter => {
//                         letter.style.color = 'lime';
//                     });
//                     firstWipeObserver.disconnect();
//                 }
//             });
//         }, { threshold: 1 });
//         firstWipeObserver.observe(firstSectionWipe);
//     }
// //
// // function observeSections() {
// //     const sections = document.querySelectorAll('.content-section');
// //     const observer = new IntersectionObserver(makeSticky, { threshold: 1 });
// //
// //     sections.forEach(section => {
// //         observer.observe(section);
// //     });
// // }
//
// function updateParallaxBackgroundPosition() {
//     let windowYOffset = window.scrollY;
//     let backgrounds = document.querySelectorAll('.parallax-background');
//     const colors = ['hotpink', 'lime', 'dodgerblue', 'yellow'];
//     let colorIndex = 0;
//
//     backgrounds.forEach(background => {
//         let scrollPosition = window.scrollY;
//         let backgroundPosition = '50% ' + scrollPosition * 0.5 + 'px';
//         let foregroundPosition = '50% ' + scrollPosition * 0.75 + 'px';
//
//         background.style.backgroundPosition = backgroundPosition;
//         let foreground = background.querySelector('.parallax-foreground');
//         foreground.style.backgroundPosition = foregroundPosition;
//         let vh = Math.max(document.documentElement.clientHeight/100);
//         //background.style.height = 1.25 * foreground.offsetHeight + (1.5 * vh) + 'px'
//     })
//     backgrounds.forEach(function(background) {
//         background.style.backgroundPosition = '50% ' + (windowYOffset * 0.5) + 'px';
//         let foreground = background.querySelector('.parallax-foreground');
//         if (foreground) {
//             console.log('have foreground');
//             foreground.style.backgroundPosition = '50% ' + (windowYOffset * 0.75) + 'px';
//             foreground.style.color = colors.at(colorIndex);
//             colorIndex ++;
//             let foregroundHeight = foreground.offsetHeight;
//             const vh = Math.max(document.documentElement.clientHeight/100);
//             // background.style.height = (foregroundHeight * 1.5) - ((foregroundHeight * (2/3))) + 1.5*vh + 'px';
//             //background.style.height = 1.25 * foregroundHeight + 1.5 * vh + 'px';
//             background.style.height = 1.15 * foregroundHeight + (2 * vh) + 'px';
//         }
//     });
// }
//
// // Update background position on scroll
//
//
// // Initial update
// updateParallaxBackgroundPosition();
//
//     document.addEventListener('DOMContentLoaded', observeBackground);
//     document.addEventListener('DOMContentLoaded', observeForeground);
//     document.addEventListener('DOMContentLoaded', observeWipe);
//     window.addEventListener('scroll', updateParallaxBackgroundPosition);
//     window.addEventListener('scroll', handleScroll);
//
// });

// // Check screen orientation
// function setRootFontSize() {
//   const root = document.documentElement;
//   if (window.innerHeight > window.innerWidth) {
//     // Portrait orientation
//     root.style.setProperty('--root-font-size', '10px');
//   } else {
//     // Landscape orientation
//     root.style.setProperty('--root-font-size', '20px');
//   }
// }
//
// // Call setRootFontSize initially and on orientation change
// setRootFontSize();
// window.addEventListener('resize', setRootFontSize);

const backgrounds = document.querySelectorAll('.parallax-background');

document.addEventListener('DOMContentLoaded', function() {

    let lastIndexHidden = -1;
    // represents 2vh
    // Show one banner for every 8vh scrolled
    const
        buffer = 2,
        banners = document.querySelectorAll('.banner-letter'),
        step = 8,
        banner = document.querySelector('#banner');

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


/*    const handleScroll = (() => {
        const ret = { active: false }
        let timeout;

        ret.activate = function activate() {
            if (ret.active) clearTimeout(timeout)
            else {
                ret.active = true
                requestAnimationFrame(updateParallaxBackgroundPosition);
            }
            timeout = setTimeout(() => ret.active = false, 50)
        }
        return ret
    })()*/


    //function handleScroll() {
    const setBannerState = () => {
        const scrollPosition = Math.floor(window.scrollY);
        const vh = Math.floor(window.innerHeight / 100);
        const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
        const indexResetPoint = Math.floor((banners.length * step * vh) + (buffer**buffer * vh));

        if (indexToShow < banners.length) {
            showBanner(indexToShow);
        } else {
            for (let index = 0; index < banners.length; index++) {
                const threshold = 3 * vh * index + 10*vh;
                // const threshold = 2 * vh * index;
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

    // function makeSticky(entries, observer) {
    //     entries.forEach(entry => {
    //         if (entry.isIntersecting) {
    //             const background = entry.target;
    //             background.classList.add('sticky');
    //             background.style.top = '10vh';
    //             observer.unobserve(background);
    //         }
    //     });
    // }
    //
    // function observeBackground() {
    //     const backgrounds = document.querySelectorAll('.parallax-background');
    //     const observer = new IntersectionObserver(makeSticky, { threshold: 1 });
    //     backgrounds.forEach(background => {
    //         observer.observe(background);
    //     });
    // }


    // function observeFirstSectionWipe() {
    //     const sectionWipe = document.getElementById('first-wipe');
    //     const navAudio = document.getElementById('nav-audio');
    //
    //     const observer = new IntersectionObserver(entries => {
    //         entries.forEach(entry => {
    //             if (!entry.isIntersecting && entry.boundingClientRect.top < 0) {
    //                 navAudio.style.display = 'block';
    //             } else {
    //                 navAudio.style.display = 'none';
    //             }
    //         });
    //     }, { threshold: [0] });
    //
    //     observer.observe(sectionWipe);
    // }

    // function observeForeground() {
    //     const foreground = document.querySelector('.parallax-foreground');
    //     const observer = new IntersectionObserver(entries => {
    //         entries.forEach(entry => {
    //             if (entry.intersectionRatio > 0) {
    //                 const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
    //                 const distanceFromBottom = vh - entry.boundingClientRect.bottom;
    //                 if (distanceFromBottom >= 15 * vh / 100) {
    //                     section.classList.remove('sticky');
    //                 }
    //             }
    //         });
    //     }, {
    //         threshold: 0 // Trigger when any part of the foreground enters the viewport
    //     });
    //
    //     observer.observe(foreground);
    // }

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

    // function observeWipe() {
    //     // console.log('observeWipe called');
    //     const firstSectionWipe = document.querySelector('.img-wrapper:first-of-type img');
    //     // const firstSectionWipe = document.querySelector('#page-wrapper > div:first-of-type img');
    //     if (!firstSectionWipe) {
    //         console.error('could not find the target element for intersection observation');
    //     }
    //     const firstWipeObserver = new IntersectionObserver(entries => {
    //         // console.log('callback firstWipeObserver called');
    //         entries.forEach(entry => {
    //             if (entry.isIntersecting) {
    //                 const bannerLetters = document.querySelectorAll('.banner-letter');
    //                 // bannerLetters.style.color = 'darkorange';
    //                 bannerLetters.forEach(letter => {
    //                     letter.style.color = 'lime';
    //                 });
    //                 firstWipeObserver.disconnect();
    //             }
    //         });
    //     }, { threshold: 1 });
    //     firstWipeObserver.observe(firstSectionWipe);
    // }

    //function updateParallaxBackgroundPosition() {
   /* const updateParallaxBackgroundPosition = () => {
        // console.log('top updateParallaxBackgroundPosition');
        let windowYOffset = window.scrollY;
        backgrounds.forEach(function(background) {
            background.style.backgroundPosition = '50% ' + (windowYOffset * 0.5) + 'px';
            // console.log('style.backgroundPosition = ', background.style.backgroundPosition);
            let foreground = background.querySelector('.parallax-foreground');
            if (foreground) {
                foreground.style.backgroundPosition = '50% ' + (windowYOffset * 0.75) + 'px';
                let foregroundHeight = foreground.clientHeight;
                const vh = window.innerHeight / 100;
                background.style.height = (foregroundHeight * 1.25) + 'px';  // was 1.5*vh
                //background.style.height = (foregroundHeight * 1.5) - ((foregroundHeight * (2/3))) + 20*vh + 'px';  // was 1.5*vh
                //console.log('backgroun.style.height = ', background.style.height);
            }
        });
        if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition);
    }*/

/*    const updateParallaxBackgroundPosition = () => {
        let windowYOffset = window.scrollY;
        backgrounds.forEach(function(background) {
            background.style.backgroundPosition = '50% ' + (windowYOffset * 0.5) + 'px';
            let foreground = background.querySelector('.parallax-foreground');
            if (foreground) {
                foreground.style.backgroundPosition = '50% ' + (windowYOffset * 0.75) + 'px';
                let foregroundHeight = foreground.clientHeight;
                const vh = window.innerHeight / 100;
                background.style.height = (foregroundHeight * 1.25) + 'px';  // was 1.5*vh
            }
        });
        if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition);
    }*/


/*    const updateParallaxBackgroundPosition = (() => {
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
    })();*/


    // The main parallax update function with smoothing and throttling
    const updateParallaxBackgroundPosition = (() => {
        let lastScrollY = 0;  // Track last scroll position to avoid redundant updates
        let lastBackgroundPos = 0; // For smoothing the background position
        let lastForegroundPos = 0; // For smoothing the foreground position

        const smoothFactor = 0.1; // A factor to smooth the transition (higher = more smoothing)

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


    //window.addEventListener('scroll', updateParallaxBackgroundPosition);
    // updateParallaxBackgroundPosition();

    // document.addEventListener('DOMContentLoaded', observeBackground);
    document.addEventListener('DOMContentLoaded', observeForeground);
    // document.addEventListener('DOMContentLoaded', recolorBanner);
    //document.addEventListener('DOMContentLoaded', observeWipe);
    recolorBanner()
    //window.addEventListener('scroll', handleScroll);
    window.addEventListener('scroll', setBannerState);

});




/* jshint esversion: 6 */


const smoothFactor = 0.5; //0.1;       // A factor to smooth the transition (higher = more smoothing)
let lastIndexHidden = -1;
const buffer = 2;
const banners = document.querySelectorAll('.banner-letter');
const step = 6;//8;
const banner = document.querySelector('#banner');

const backgrounds = document.querySelectorAll('.parallax-background');


// Check screen orientation
function setRootFontSize() {
    const root = document.documentElement;
    if (window.innerHeight > window.innerWidth) {
        root.style.setProperty('--root-font-size', '10px'); // Portrait orientation
    } else {
        root.style.setProperty('--root-font-size', '20px'); // Landscape orientation
    }
}


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
    const firstSectionWipe = document.getElementById('first-wipe');
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

//
// function observeForeground() {
//     const foregrounds = document.querySelectorAll('.parallax-foreground');
//
//     foregrounds.forEach(foreground => {
//         const observer = new IntersectionObserver(entries => {
//             entries.forEach(entry => {
//                 const section = entry.target.closest('section');
//                 if (!section) return; // If no section ancestor found, exit
//                 if (entry.intersectionRatio > 0) {
//                     const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
//                     const distanceFromBottom = vh - entry.boundingClientRect.bottom;
//                     if (distanceFromBottom >= 15 * vh / 100) {
//                         section.classList.remove('sticky');
//                     }
//                 }
//             });
//         }, {
//             threshold: 0 // Trigger when any part of the foreground enters the viewport
//         });
//
//         observer.observe(foreground);
//     });
// }

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
            const threshold = vh * index + ((10+index) * vh);
            if ((scrollPosition - indexResetPoint) >= threshold && index > lastIndexHidden) {
                hideBanner(index);
                lastIndexHidden = index;
            }
        }
    }
}


// // The main parallax update function with smoothing and throttling
// const updateParallaxBackgroundPosition = (() => {
//     let lastScrollY = 0;            // Track last scroll position to avoid redundant updates
//     let lastBackgroundPos = 0;      // For smoothing the background position
//     let lastForegroundPos = 0;      // For smoothing the foreground position
//
//     // Function to handle parallax updates
//     return () => {
//         let windowYOffset = window.scrollY;
//         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if there's little movement
//
//         // Smooth transition for background position
//         let backgroundPos = windowYOffset * 0.5;
//         let smoothedBackgroundPos = lastBackgroundPos + (backgroundPos - lastBackgroundPos) * smoothFactor; // Use global smoothFactor
//         lastBackgroundPos = smoothedBackgroundPos;
//
//         // Update the background position for all elements with the class 'parallax-background'
//         // document.querySelectorAll('.parallax-background').forEach(function(background) {
//         const activeBackground = document.querySelector('.active-parallax');
//         if (activeBackground) {
//             activeBackground.style.backgroundPosition = '50% 0px';
//
//             let foreground = background.querySelector('.parallax-foreground');
//             if (foreground) {
//                 // Smooth transition for foreground position
//                 let foregroundPos = windowYOffset * 0.75;
//                 let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor; // Use global smoothFactor
//                 lastForegroundPos = smoothedForegroundPos;
//
//                 // Update foreground position
//                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//
//                 // Optionally adjust height for smoother scrolling
//                 let foregroundHeight = foreground.clientHeight;
//                 background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
//             }
//         }
//         background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
//
//         let foreground = background.querySelector('.parallax-foreground');
//         if (foreground) {
//             // Smooth transition for foreground position
//             let foregroundPos = windowYOffset * 0.75;
//             let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor; // Use global smoothFactor
//             lastForegroundPos = smoothedForegroundPos;
//
//             // Update foreground position
//             foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//
//             // Optionally adjust height for smoother scrolling
//             let foregroundHeight = foreground.clientHeight;
//             background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
//         }
//
//         lastScrollY = windowYOffset;  // Update last scroll position
//
//         // Request the next animation frame if needed
//         if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition); // Ensures smooth rendering
//     }
// })();


//
// const updateParallaxBackgroundPosition = (() => {
//     let lastScrollY = 0;
//     let lastBackgroundPos = 0;
//     let lastForegroundPos = 0;
//
//     return () => {
//         let windowYOffset = window.scrollY;
//         if (Math.abs(windowYOffset - lastScrollY) < 1) return;
//
//         let backgroundPos = windowYOffset * 0.5;
//         let smoothedBackgroundPos = lastBackgroundPos + (backgroundPos - lastBackgroundPos) * smoothFactor;
//         lastBackgroundPos = smoothedBackgroundPos;
//
//         const activeBackground = document.querySelector('.active-parallax');
//         if (activeBackground) {
//             activeBackground.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
//
//             let foreground = activeBackground.querySelector('.parallax-foreground');
//             if (foreground) {
//                 let foregroundPos = windowYOffset * 0.75;
//                 let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor;
//                 lastForegroundPos = smoothedForegroundPos;
//
//                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//
//                 let foregroundHeight = foreground.clientHeight;
//                 activeBackground.style.height = `${foregroundHeight * 1.25}px`;
//             }
//         }
//
//         lastScrollY = windowYOffset;
//
//         if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition);
//     };
// })();




// Handle scroll event with throttling
// const handleScroll = (() => {
//     const ret = { active: false };
//     let timeout;
//
//     ret.activate = function activate() {
//         if (ret.active) clearTimeout(timeout); // Prevent multiple calls in quick succession
//         else {
//             ret.active = true;
//             requestAnimationFrame(updateParallaxBackgroundPosition); // Efficiently handle the scroll event
//         }
//         timeout = setTimeout(() => ret.active = false, 100);  // **Throttle** the calls to reduce unnecessary updates
//     };
//     return ret;
// })();

// Attach the scroll event listener to the window
//window.addEventListener('scroll', handleScroll.activate); // Handles the scroll event efficiently




// The main parallax update function with smoothing and throttling
const updateParallaxBackgroundPosition = (() => {
    let lastScrollY = 0;            // Track last scroll position to avoid redundant updates
    let lastBackgroundPos = 0;      // For smoothing the background position
    let lastForegroundPos = 0;      // For smoothing the foreground position



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
        timeout = setTimeout(() => ret.active = false, 100);  // Throttling to reduce unnecessary calls
    };
    return ret;
})();


// Variables to store the state of the scroll direction
// let lastScrollY = window.scrollY;
// let scrollDirection = 'down'; // Default scroll direction
//
// // Intersection Observer callback to track when .section-wipe is at the bottom of the viewport
// const sectionObserver = new IntersectionObserver((entries, observer) => {
//     entries.forEach(entry => {
//         if (entry.isIntersecting) {
//             // Determine the direction of scrolling
//             if (window.scrollY > lastScrollY) {
//                 // Scrolling down
//                 handleScrollingDown(entry.target);
//             } else {
//                 // Scrolling up
//                 handleScrollingUp(entry.target);
//             }
//
//             // Update last scroll position for future scroll direction checks
//             lastScrollY = window.scrollY;
//         }
//     });
// }, {
//     root: null, // Observe in the viewport
//     threshold: 1.0, // Trigger when the bottom of the .section-wipe element is fully in view
// });
//
// // Observe all .section-wipe elements
// document.querySelectorAll('.section-wipe').forEach(section => {
//     sectionObserver.observe(section);
// });
//
// // Function to handle scrolling down
// function handleScrollingDown(section) {
//     // Find the next .parallax-background element
//     const nextParallax = section.nextElementSibling && section.nextElementSibling.classList.contains('parallax-background')
//         ? section.nextElementSibling
//         : null;
//
//     // Remove active class from all .parallax-background elements
//     document.querySelectorAll('.parallax-background').forEach(background => {
//         background.classList.remove('active-parallax');
//     });
//
//     // Add active class to the next .parallax-background if it exists
//     if (nextParallax) {
//         nextParallax.classList.add('active-parallax');
//     }
// }
//
// // Function to handle scrolling up
// function handleScrollingUp(section) {
//     // Find the previous .parallax-background element
//     const previousParallax = section.previousElementSibling && section.previousElementSibling.classList.contains('parallax-background')
//         ? section.previousElementSibling
//         : null;
//
//     // Remove active class from all .parallax-background elements
//     document.querySelectorAll('.parallax-background').forEach(background => {
//         background.classList.remove('active-parallax');
//     });
//
//     // Add active class to the previous .parallax-background if it exists
//     if (previousParallax) {
//         previousParallax.classList.add('active-parallax');
//     }
// }





document.addEventListener('DOMContentLoaded', function() {

    window.addEventListener('scroll', handleScroll.activate);
    window.addEventListener('scroll', setBannerState);
    window.addEventListener('resize', setRootFontSize);
    // Set up event listener for scrolling (optional, but useful to track scroll direction)
    // window.addEventListener('scroll', () => {
    //     // Determine scroll direction
    //     scrollDirection = (window.scrollY > lastScrollY) ? 'down' : 'up';
    //     lastScrollY = window.scrollY;
    // });

    updateParallaxBackgroundPosition();
    //observeForeground();
    recolorBanner();
    setRootFontSize();
});




/*document.addEventListener('DOMContentLoaded', function() {

    // Attach the scroll event listener
    window.addEventListener('scroll', handleScroll.activate);

    // Initialize the parallax effect when the page is loaded
    document.addEventListener('DOMContentLoaded', () => {
        updateParallaxBackgroundPosition();
    });
    //updateParallaxBackgroundPosition();

/!*    window.addEventListener('scroll', handleScroll.activate);*!/

    document.addEventListener('DOMContentLoaded', observeForeground);

    recolorBanner();

    window.addEventListener('scroll', setBannerState);

    // Call setRootFontSize initially and on orientation change
    setRootFontSize();
    window.addEventListener('resize', setRootFontSize);
});*/





















// /* jshint esversion: 6 */
//
//
// const smoothFactor = 0.1; //0.1;       // A factor to smooth the transition (higher = more smoothing)
// let lastIndexHidden = -1;
// const buffer = 2;
// const banners = document.querySelectorAll('.banner-letter');
// const step = 6;//8;
// const banner = document.querySelector('#banner');
//
// const backgrounds = document.querySelectorAll('.parallax-background');
//
//
// // Check screen orientation
// function setRootFontSize() {
//     const root = document.documentElement;
//     if (window.innerHeight > window.innerWidth) {
//         root.style.setProperty('--root-font-size', '10px'); // Portrait orientation
//     } else {
//         root.style.setProperty('--root-font-size', '20px'); // Landscape orientation
//     }
// }
//
//
// function showBanner(index) {
//     if (0 <= index && index < banners.length) {
//         banners[index].style.display = 'inline-block';
//         banners[index].classList.add('burn');
//         banners[index].style.transition = 'color 0.25s ease-in, text-shadow 0.25.s ease-in-out';
//     }
// }
//
//
// function hideBanner(index) {
//     if (0 <= index && index < banners.length) {
//         // Apply initial flash effect
//         banners[index].style.color =  'rgb(0, 212, 255)'; // Flash color
//         banners[index].style.transition = 'color 0.3s ease-out, opacity 0.5s ease-out, text-shadow 0.25s ease-out'; // Quick flash transition
//         banners[index].style.textShadow = '0 0 10px rgba(255, 255, 255, 0.9)';
//
//         // After a short time, transition to the next effect
//         setTimeout(() => {
//             banners[index].style.color = 'rgb(255, 255, 255)';
//             banners[index].style.transition = 'color 3s ease, opacity 3s ease-out, text-shadow 3s ease-out'; // Longer smooth transition
//
//             // After another time, apply the final transition effect
//             setTimeout(() => {
//                 banners[index].style.color = 'rgb(0,0,0)';
//                 banners[index].style.opacity = '0';
//                 banners[index].style.textShadow = '0 0 10px rgba(255, 255, 255, 0.8)';
//             }, 500); // Delay before final fade-out
//         }, 250); // Short delay before applying the second effect
//     }
//     if (index === banners.length) {
//         banner.style.background = 'transparent';
//         banners.style.color = 'transparent';
//     }
// }
//
//
// function recolorBanner() {
//     const firstSectionWipe = document.getElementById('first-wipe');
//     const recolorBannerObserver = new IntersectionObserver(entries => {
//         entries.forEach(entry => {
//             if (entry.boundingClientRect.top < 0) {
//                 document.querySelector('#banner').style.backgroundColor = 'rgba(0,0,0,1)';
//                 banners.forEach(banner => {
//                     banner.style.color = "darkorange";
//                     banner.style.opacity = '1';
//                 });
//             }
//         });
//     });
//     recolorBannerObserver.observe(firstSectionWipe);
// }
//
//
// // function observeForeground() {
// //     const foregrounds = document.querySelectorAll('.parallax-foreground');
// //
// //     foregrounds.forEach(foreground => {
// //         const observer = new IntersectionObserver(entries => {
// //             entries.forEach(entry => {
// //                 const section = entry.target.closest('section');
// //                 if (!section) return; // If no section ancestor found, exit
// //                 if (entry.intersectionRatio > 0) {
// //                     const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
// //                     const distanceFromBottom = vh - entry.boundingClientRect.bottom;
// //                     if (distanceFromBottom >= 15 * vh / 100) {
// //                         section.classList.remove('sticky');
// //                     }
// //                 }
// //             });
// //         }, {
// //             threshold: 0 // Trigger when any part of the foreground enters the viewport
// //         });
// //
// //         observer.observe(foreground);
// //     });
// // }
//
// const setBannerState = () => {
//     const scrollPosition = Math.floor(window.scrollY);
//     const vh = Math.floor(window.innerHeight / 100);
//     const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
//     const indexResetPoint = Math.floor((banners.length * step * vh) + (buffer ** buffer * vh));
//
//     // Show the banner for the current index and all preceding indexes that haven't been shown yet
//     if (indexToShow < banners.length) {
//         for (let i = 0; i <= indexToShow; i++) {
//             if (banners[i].style.display !== 'inline-block') {
//                 showBanner(i);
//             }
//         }
//     } else {
//         for (let index = 0; index < banners.length; index++) {
//             const threshold = vh * index + ((10+index) * vh);
//             if ((scrollPosition - indexResetPoint) >= threshold && index > lastIndexHidden) {
//                 hideBanner(index);
//                 lastIndexHidden = index;
//             }
//         }
//     }
// }
//
//
// // The main parallax update function with smoothing and throttling
// const updateParallaxBackgroundPosition = (() => {
//     let lastScrollY = 0;            // Track last scroll position to avoid redundant updates
//     let lastBackgroundPos = 0;      // For smoothing the background position
//     let lastForegroundPos = 0;      // For smoothing the foreground position
//
//     // Function to handle parallax updates
//     return () => {
//         let windowYOffset = window.scrollY;
//         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if there's little movement
//
//         // Smooth transition for background position
//         let backgroundPos = windowYOffset * 0.5;
//         let smoothedBackgroundPos = lastBackgroundPos + (backgroundPos - lastBackgroundPos) * smoothFactor; // Use global smoothFactor
//         lastBackgroundPos = smoothedBackgroundPos;
//
//         // Update the background position for all elements with the class 'parallax-background'
//         // document.querySelectorAll('.parallax-background').forEach(function(background) {
//         const activeBackground = document.querySelector('.active-parallax');
//         if (activeBackground) {
//             activeBackground.style.backgroundPosition = '50% 0px';
//
//             let foreground = background.querySelector('.parallax-foreground');
//             if (foreground) {
//                 // Smooth transition for foreground position
//                 let foregroundPos = windowYOffset * 0.75;
//                 let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor; // Use global smoothFactor
//                 lastForegroundPos = smoothedForegroundPos;
//
//                 // Update foreground position
//                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//
//                 // Optionally adjust height for smoother scrolling
//                 let foregroundHeight = foreground.clientHeight;
//                 background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
//             }
//         //}
//             //background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
//
//             // let foreground = background.querySelector('.parallax-foreground');
//             // if (foreground) {
//             //     // Smooth transition for foreground position
//             //     let foregroundPos = windowYOffset * 0.75;
//             //     let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor; // Use global smoothFactor
//             //     lastForegroundPos = smoothedForegroundPos;
//             //
//             //     // Update foreground position
//             //     foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//             //
//             //     // Optionally adjust height for smoother scrolling
//             //     let foregroundHeight = foreground.clientHeight;
//             //     background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
//             // }
//         //});
//
//         lastScrollY = windowYOffset;  // Update last scroll position
//
//         // Request the next animation frame if needed
//         if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition); // Ensures smooth rendering
//     }
// })();
//
// // Handle scroll event with throttling
// const handleScroll = (() => {
//     const ret = { active: false };
//     let timeout;
//
//     ret.activate = function activate() {
//         if (ret.active) clearTimeout(timeout); // Prevent multiple calls in quick succession
//         else {
//             ret.active = true;
//             requestAnimationFrame(updateParallaxBackgroundPosition); // Efficiently handle the scroll event
//         }
//         timeout = setTimeout(() => ret.active = false, 100);  // **Throttle** the calls to reduce unnecessary updates
//     };
//     return ret;
// })();
//
// // Attach the scroll event listener to the window
// window.addEventListener('scroll', handleScroll.activate); // Handles the scroll event efficiently
//
//
//
// //
// // // The main parallax update function with smoothing and throttling
// // const updateParallaxBackgroundPosition = (() => {
// //     let lastScrollY = 0;            // Track last scroll position to avoid redundant updates
// //     let lastBackgroundPos = 0;      // For smoothing the background position
// //     let lastForegroundPos = 0;      // For smoothing the foreground position
// //
// //
// //
// //     return () => {
// //         let windowYOffset = window.scrollY;
// //         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if there's little movement
// //
// //         // Smooth transition for background position
// //         let backgroundPos = windowYOffset * 0.5;
// //         let smoothedBackgroundPos = lastBackgroundPos + (backgroundPos - lastBackgroundPos) * smoothFactor;
// //         lastBackgroundPos = smoothedBackgroundPos;
// //
// //         // Update the background position
// //         backgrounds.forEach(function(background) {
// //             background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
// //
// //             let foreground = background.querySelector('.parallax-foreground');
// //             if (foreground) {
// //                 // Smooth transition for foreground position
// //                 let foregroundPos = windowYOffset * 0.75;
// //                 let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor;
// //                 lastForegroundPos = smoothedForegroundPos;
// //
// //                 // Update foreground position
// //                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
// //
// //                 // Optionally adjust height for smoother scrolling
// //                 let foregroundHeight = foreground.clientHeight;
// //                 background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
// //             }
// //         });
// //
// //         lastScrollY = windowYOffset;  // Update last scroll position
// //
// //         // Request the next animation frame if needed
// //         if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition);
// //     }
// // })();
// //
// //
// // // Handle scroll event with throttling
// // const handleScroll = (() => {
// //     const ret = { active: false };
// //     let timeout;
// //
// //     ret.activate = function activate() {
// //         if (ret.active) clearTimeout(timeout);
// //         else {
// //             ret.active = true;
// //             requestAnimationFrame(updateParallaxBackgroundPosition);
// //         }
// //         timeout = setTimeout(() => ret.active = false, 100);  // Throttling to reduce unnecessary calls
// //     };
// //     return ret;
// // })();
//
//
// // Variables to store the state of the scroll direction
// let lastScrollY = window.scrollY;
// let scrollDirection = 'down'; // Default scroll direction
//
// // Intersection Observer callback to track when .section-wipe is at the bottom of the viewport
// const sectionObserver = new IntersectionObserver((entries, observer) => {
//     entries.forEach(entry => {
//         if (entry.isIntersecting) {
//             // Determine the direction of scrolling
//             if (window.scrollY > lastScrollY) {
//                 // Scrolling down
//                 handleScrollingDown(entry.target);
//             } else {
//                 // Scrolling up
//                 handleScrollingUp(entry.target);
//             }
//
//             // Update last scroll position for future scroll direction checks
//             lastScrollY = window.scrollY;
//         }
//     });
// }, {
//     root: null, // Observe in the viewport
//     threshold: 1.0, // Trigger when the bottom of the .section-wipe element is fully in view
// });
//
// // Observe all .section-wipe elements
// document.querySelectorAll('.section-wipe').forEach(section => {
//     sectionObserver.observe(section);
// });
//
// // Function to handle scrolling down
// function handleScrollingDown(section) {
//     // Find the next .parallax-background element
//     const nextParallax = section.nextElementSibling && section.nextElementSibling.classList.contains('parallax-background')
//         ? section.nextElementSibling
//         : null;
//
//     // Remove active class from all .parallax-background elements
//     document.querySelectorAll('.parallax-background').forEach(background => {
//         background.classList.remove('active-parallax');
//     });
//
//     // Add active class to the next .parallax-background if it exists
//     if (nextParallax) {
//         nextParallax.classList.add('active-parallax');
//     }
// }
//
// // Function to handle scrolling up
// function handleScrollingUp(section) {
//     // Find the previous .parallax-background element
//     const previousParallax = section.previousElementSibling && section.previousElementSibling.classList.contains('parallax-background')
//         ? section.previousElementSibling
//         : null;
//
//     // Remove active class from all .parallax-background elements
//     document.querySelectorAll('.parallax-background').forEach(background => {
//         background.classList.remove('active-parallax');
//     });
//
//     // Add active class to the previous .parallax-background if it exists
//     if (previousParallax) {
//         previousParallax.classList.add('active-parallax');
//     }
// }
//
//
//
//
//
// document.addEventListener('DOMContentLoaded', function() {
//
//     window.addEventListener('scroll', handleScroll.activate);
//     window.addEventListener('scroll', setBannerState);
//     window.addEventListener('resize', setRootFontSize);
//     // Set up event listener for scrolling (optional, but useful to track scroll direction)
//     window.addEventListener('scroll', () => {
//         // Determine scroll direction
//         scrollDirection = (window.scrollY > lastScrollY) ? 'down' : 'up';
//         lastScrollY = window.scrollY;
//     });
//
//     updateParallaxBackgroundPosition();
//     //observeForeground();
//     recolorBanner();
//     setRootFontSize();
// });
//
//
//
//
// /*document.addEventListener('DOMContentLoaded', function() {
//
//     // Attach the scroll event listener
//     window.addEventListener('scroll', handleScroll.activate);
//
//     // Initialize the parallax effect when the page is loaded
//     document.addEventListener('DOMContentLoaded', () => {
//         updateParallaxBackgroundPosition();
//     });
//     //updateParallaxBackgroundPosition();
//
// /!*    window.addEventListener('scroll', handleScroll.activate);*!/
//
//     document.addEventListener('DOMContentLoaded', observeForeground);
//
//     recolorBanner();
//
//     window.addEventListener('scroll', setBannerState);
//
//     // Call setRootFontSize initially and on orientation change
//     setRootFontSize();
//     window.addEventListener('resize', setRootFontSize);
// });*/
