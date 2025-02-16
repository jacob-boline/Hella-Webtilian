/* jshint esversion: 6 */
//
// const smoothFactor = 0.1; //0.1;       // A factor to smooth the transition (higher = more smoothing)
// let lastIndexHidden = -1;
// const buffer = 2;
// const banners = document.querySelectorAll('.banner-letter');
// const step = 6;//8;
// const banner = document.querySelector('#banner');
//
// const backgrounds = document.querySelectorAll('.parallax-background');

const smoothFactor = 0.1; // Smoothing factor
// const cumulativeOffsets = {}; // Store cumulative offsets globally
let lastBackgroundPos = 0; // Store smoothed background positions
let lastForegroundPos = 0; // Store smoothed foreground positions
let lastScrollY = 0; // Track the last scroll position
let cumulativeOffset = 0; // The global offset for the parallax effect
let activeSection = null; // The currently active section

let lastIndexHidden = -1;
const buffer = 2;
const banners = document.querySelectorAll('.banner-letter');
const step = 6;//8;
const banner = document.querySelector('#banner');



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

//
// // Observer to track cumulative offset and active section
// const observer = new IntersectionObserver((entries) => {
//     entries.forEach((entry) => {
//         const rect = entry.target.getBoundingClientRect();
//
//         if (entry.isIntersecting) {
//             if (rect.top >= 0) {
//                 cumulativeOffset = window.scrollY - rect.bottom;
//             }
//
//             // Update active section only for parallax-background
//             if (entry.target.classList.contains('parallax-background')) {
//                 activeSection = entry.target;
//             }
//         } else if (!entry.isIntersecting && rect.top < 0) {
//             // Update cumulative offset for exited element
//             cumulativeOffset = window.scrollY - rect.bottom;
//
//             // Reset active section if parallax-background fully exits
//             if (entry.target === activeSection) {
//                 activeSection = null;
//             }
//         }
//     });
// });
//
// // Observe .parallax-background and .section-wipe
// document.querySelectorAll('.parallax-background, .section-wipe').forEach((element) => {
//     observer.observe(element);
// });

function getSectionWipeHeightsBefore(section) {
    const wipes = Array.from(document.querySelectorAll('.section-wipe'));
    let totalHeight = 0;

    for (const wipe of wipes) {
        if (wipe.compareDocumentPosition(section) & Node.DOCUMENT_POSITION_FOLLOWING) {
            break; // Stop if we reach the target section
        }
        totalHeight += wipe.offsetHeight;
    }

    return totalHeight;
}

const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        const rect = entry.target.getBoundingClientRect();

        if (entry.isIntersecting) {
            // When the section enters the viewport, calculate the offset
            cumulativeOffset = getSectionWipeHeightsBefore(entry.target) + window.scrollY - rect.bottom;
            activeSection = entry.target;
        } else if (!entry.isIntersecting && rect.top < 0) {
            // When the section exits the viewport at the top
            cumulativeOffset = getSectionWipeHeightsBefore(entry.target) + window.scrollY - rect.bottom;
            activeSection = null; // Reset if fully exited
        }
    });
});

// Observe only .parallax-background elements


// const observer = new IntersectionObserver((entries) => {
//     entries.forEach((entry) => {
//         const rect = entry.target.getBoundingClientRect();
//
//         if (entry.isIntersecting) {
//             // Section entered the viewport
//             if (rect.top >= 0) {
//                 cumulativeOffset = window.scrollY - rect.bottom;
//             }
//             activeSection = entry.target;
//         } else if (rect.top < 0 && rect.bottom <= 0) {
//             // Section exited the viewport at the top
//             cumulativeOffset = window.scrollY - rect.bottom;
//             activeSection = null; // Reset active section if fully exited
//         }
//     });
// });
//
// // Observe all parallax backgrounds
// document.querySelectorAll('.parallax-background').forEach((background) => {
//     observer.observe(background);
// });



// // Observer to track cumulative offsets and active section
// const observer = new IntersectionObserver((entries) => {
//     entries.forEach((entry) => {
//         const sectionId = entry.target.dataset.section;
//
//         if (!entry.isIntersecting && entry.boundingClientRect.top < 0) {
//             cumulativeOffsets[sectionId] = parseFloat(
//                 (entry.target.style.backgroundPosition || "50% 0px").split(" ")[1]
//             ) || 0;
//         }
//
//         if (entry.isIntersecting) {
//             activeSection = entry.target;
//         } else if (entry.boundingClientRect.top < 0 && activeSection === entry.target) {
//             activeSection = null; // Reset if it scrolls out
//         }
//     });
// });

//
// const observer = new IntersectionObserver((entries) => {
//     entries.forEach((entry) => {
//         const rect = entry.target.getBoundingClientRect();
//
//         if (entry.isIntersecting) {
//             // Section entered the viewport from the top
//             if (rect.top >= 0) {
//                 cumulativeOffset = window.scrollY - rect.bottom;
//             }
//             activeSection = entry.target;
//         } else if (rect.top < 0 && rect.bottom <= 0) {
//             // Section exited the viewport at the top
//             cumulativeOffset = window.scrollY - rect.bottom;
//             activeSection = null; // Reset active section if it fully exits
//         }
//     });
// });
//
// // Observe all parallax backgrounds
// document.querySelectorAll('.parallax-background').forEach((background) => {
//     observer.observe(background);
// });

// const UpdateParallaxBackgroundPosition = () => {
//     if (!activeSection) return;
//
//     const windowYOffset = window.scrollY;
//     const sectionId = activeSection.dataset.section;
//     const cumulativeOffset = cumulativeOffsets[sectionId] || 0;
//
//     // Calculate smoothed background position
//     const backgroundPos = windowYOffset * 0.5 + cumulativeOffset;
//     const smoothedBackgroundPos =
//         (lastBackgroundPos[sectionId] || 0) + (backgroundPos - (lastBackgroundPos[sectionId] || 0)) * smoothFactor;
//     lastBackgroundPos[sectionId] = smoothedBackgroundPos;
//
//     // Update background position
//     activeSection.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
//
//     const foreground = activeSection.querySelector('.parallax-foreground');
//     if (foreground) {
//         const foregroundPos = windowYOffset * 0.75 + cumulativeOffset;
//
//         // Calculate smoothed foreground position
//         const smoothedForegroundPos =
//             (lastForegroundPos[sectionId] || 0) + (foregroundPos - (lastForegroundPos[sectionId] || 0)) * smoothFactor;
//         lastForegroundPos[sectionId] = smoothedForegroundPos;
//
//         // Update foreground position
//         foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//     }
// };
//
// const UpdateParallaxBackgroundPosition = () => {
//     if (!activeSection) return; // No active section, skip
//
//     const windowYOffset = window.scrollY;
//     const backgroundPos = windowYOffset * 0.5 + cumulativeOffset;
//
//     // Smooth the transition
//     const smoothedBackgroundPos =
//         (lastBackgroundPos || 0) + (backgroundPos - (lastBackgroundPos || 0)) * smoothFactor;
//     lastBackgroundPos = smoothedBackgroundPos;
//
//     // Apply the position to the active section
//     activeSection.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
//
//     const foreground = activeSection.querySelector('.parallax-foreground');
//     if (foreground) {
//         const foregroundPos = windowYOffset * 0.75 + cumulativeOffset;
//         const smoothedForegroundPos =
//             (lastForegroundPos || 0) + (foregroundPos - (lastForegroundPos || 0)) * smoothFactor;
//         lastForegroundPos = smoothedForegroundPos;
//
//         foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//     }
// };

const UpdateParallaxBackgroundPosition = () => {
    if (!activeSection) return; // Skip if no active section

    const windowYOffset = window.scrollY;
    const backgroundPos = windowYOffset * 0.5 + cumulativeOffset;

    const smoothedBackgroundPos =
        lastBackgroundPos + (backgroundPos - lastBackgroundPos) * smoothFactor;
    lastBackgroundPos = smoothedBackgroundPos;

    activeSection.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;

    const foreground = activeSection.querySelector('.parallax-foreground');
    if (foreground) {
        const foregroundPos = windowYOffset * 0.75 + cumulativeOffset;

        const smoothedForegroundPos =
            lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor;
        lastForegroundPos = smoothedForegroundPos;

        foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
    }
};


//
// const isElementInViewport = (el) => {
//     const rect = el.getBoundingClientRect();
//     return rect.top < window.innerHeight && rect.bottom > 0;
// };
//
// const UpdateParallaxBackgroundPosition = () => {
//     const cumulativeOffsets = {}; // Store cumulative offsets for each section
//     const lastBackgroundPos = {}; // Store smoothed background positions
//     const lastForegroundPos = {}; // Store smoothed foreground positions
//     let lastScrollY = 0; // Track the last scroll position
//
//
//
//     const observer = new IntersectionObserver(
//         (entries) => {
//             entries.forEach((entry) => {
//                 const sectionId = entry.target.dataset.section;
//
//                 if (!entry.isIntersecting && entry.boundingClientRect.top < 0) {
//                     // The element has exited the viewport at the top
//                     cumulativeOffsets[sectionId] = parseFloat(
//                         (entry.target.style.backgroundPosition || "50% 0px").split(" ")[1]
//                     ) || 0;
//                 }
//             });
//         },
//         { threshold: 0 }
//     );
//
//     // Observe all .parallax-background elements
//     document.querySelectorAll('.parallax-background').forEach((background) => {
//         observer.observe(background);
//     });
//
//     return function () {
//         const windowYOffset = window.scrollY;
//         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if no significant movement
//
//         document.querySelectorAll('.parallax-background').forEach((background) => {
//             if (!isElementInViewport(background)) return;
//
//             const sectionId = background.dataset.section;
//
//             // Use the cumulative offset when calculating background position
//             const cumulativeOffset = cumulativeOffsets[sectionId] || 0;
//             const backgroundPos = windowYOffset * 0.5 + cumulativeOffset;
//
//             const smoothedBackgroundPos =
//                 (lastBackgroundPos[sectionId] || 0) + (backgroundPos - (lastBackgroundPos[sectionId] || 0)) * smoothFactor;
//             lastBackgroundPos[sectionId] = smoothedBackgroundPos;
//
//             // Update the background position
//             background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
//
//             const foreground = background.querySelector('.parallax-foreground');
//             if (foreground) {
//                 const foregroundPos = windowYOffset * 0.75 + cumulativeOffset;
//
//                 const smoothedForegroundPos =
//                     (lastForegroundPos[sectionId] || 0) + (foregroundPos - (lastForegroundPos[sectionId] || 0)) * smoothFactor;
//                 lastForegroundPos[sectionId] = smoothedForegroundPos;
//
//                 // Update foreground position
//                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//
//                 // Adjust background height based on foreground
//                 const foregroundHeight = foreground.clientHeight;
//                 background.style.height = `${foregroundHeight * 1.25}px`;
//             }
//         });
//
//         lastScrollY = windowYOffset; // Update the last scroll position
//     };
// }();
//
//
// // Handle scroll event with throttling
// const handleScroll = (() => {
//     const ret = { active: false };
//     let timeout;
//
//     ret.activate = function activate() {
//         if (ret.active) clearTimeout(timeout);
//         else {
//             ret.active = true;
//             requestAnimationFrame(UpdateParallaxBackgroundPosition);
//         }
//         timeout = setTimeout(() => ret.active = false, 50);  // Throttling to reduce unnecessary calls
//     };
//     return ret;
// })();
document.addEventListener('DOMContentLoaded', () => {
    // Attach scroll event
    window.addEventListener('scroll', () => {
        requestAnimationFrame(() => {
            UpdateParallaxBackgroundPosition();
            setBannerState();
        });w
    });

    // Observe only .parallax-background elements
    document.querySelectorAll('.parallax-background').forEach((background) => {
        observer.observe(background);
    });
    window.addEventListener('resize', setRootFontSize);
    // Initial setup
    UpdateParallaxBackgroundPosition(); // Ensure the initial state is set
    recolorBanner();
    setRootFontSize();
});


// document.addEventListener('DOMContentLoaded', function() {
//
//     // window.addEventListener('scroll', handleScroll.activate);
//     // window.addEventListener('scroll', () => {
//     //     requestAnimationFrame(UpdateParallaxBackgroundPosition);
//     // });
//     // window.addEventListener('scroll', setBannerState);
//
//     window.addEventListener('scroll', () => {
//         requestAnimationFrame(() => {
//             UpdateParallaxBackgroundPosition();
//             setBannerState();
//         });
//     });
//     window.addEventListener('resize', setRootFontSize);
//     UpdateParallaxBackgroundPosition();
//     recolorBanner();
//     setRootFontSize();
// });

















//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
// // /* jshint esversion: 6 */
// //
// //
// // const smoothFactor = 0.1; //0.1;       // A factor to smooth the transition (higher = more smoothing)
// // let lastIndexHidden = -1;
// // const buffer = 2;
// // const banners = document.querySelectorAll('.banner-letter');
// // const step = 6;//8;
// // const banner = document.querySelector('#banner');
// //
// // const backgrounds = document.querySelectorAll('.parallax-background');
// //
// //
// // // Check screen orientation
// // function setRootFontSize() {
// //     const root = document.documentElement;
// //     if (window.innerHeight > window.innerWidth) {
// //         root.style.setProperty('--root-font-size', '10px'); // Portrait orientation
// //     } else {
// //         root.style.setProperty('--root-font-size', '20px'); // Landscape orientation
// //     }
// // }
// //
// //
// // function showBanner(index) {
// //     if (0 <= index && index < banners.length) {
// //         banners[index].style.display = 'inline-block';
// //         banners[index].classList.add('burn');
// //         banners[index].style.transition = 'color 0.25s ease-in, text-shadow 0.25.s ease-in-out';
// //     }
// // }
// //
// //
// // function hideBanner(index) {
// //     if (0 <= index && index < banners.length) {
// //         // Apply initial flash effect
// //         banners[index].style.color =  'rgb(0, 212, 255)'; // Flash color
// //         banners[index].style.transition = 'color 0.3s ease-out, opacity 0.5s ease-out, text-shadow 0.25s ease-out'; // Quick flash transition
// //         banners[index].style.textShadow = '0 0 10px rgba(255, 255, 255, 0.9)';
// //
// //         // After a short time, transition to the next effect
// //         setTimeout(() => {
// //             banners[index].style.color = 'rgb(255, 255, 255)';
// //             banners[index].style.transition = 'color 3s ease, opacity 3s ease-out, text-shadow 3s ease-out'; // Longer smooth transition
// //
// //             // After another time, apply the final transition effect
// //             setTimeout(() => {
// //                 banners[index].style.color = 'rgb(0,0,0)';
// //                 banners[index].style.opacity = '0';
// //                 banners[index].style.textShadow = '0 0 10px rgba(255, 255, 255, 0.8)';
// //             }, 500); // Delay before final fade-out
// //         }, 250); // Short delay before applying the second effect
// //     }
// //     if (index === banners.length) {
// //         banner.style.background = 'transparent';
// //         banners.style.color = 'transparent';
// //     }
// // }
// //
// //
// // function recolorBanner() {
// //     const firstSectionWipe = document.getElementById('first-wipe');
// //     const recolorBannerObserver = new IntersectionObserver(entries => {
// //         entries.forEach(entry => {
// //             if (entry.boundingClientRect.top < 0) {
// //                 document.querySelector('#banner').style.backgroundColor = 'rgba(0,0,0,1)';
// //                 banners.forEach(banner => {
// //                     banner.style.color = "darkorange";
// //                     banner.style.opacity = '1';
// //                 });
// //             }
// //         });
// //     });
// //     recolorBannerObserver.observe(firstSectionWipe);
// // }
// //
// //
// // // function observeForeground() {
// // //     const foregrounds = document.querySelectorAll('.parallax-foreground');
// // //
// // //     foregrounds.forEach(foreground => {
// // //         const observer = new IntersectionObserver(entries => {
// // //             entries.forEach(entry => {
// // //                 const section = entry.target.closest('section');
// // //                 if (!section) return; // If no section ancestor found, exit
// // //                 if (entry.intersectionRatio > 0) {
// // //                     const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
// // //                     const distanceFromBottom = vh - entry.boundingClientRect.bottom;
// // //                     if (distanceFromBottom >= 15 * vh / 100) {
// // //                         section.classList.remove('sticky');
// // //                     }
// // //                 }
// // //             });
// // //         }, {
// // //             threshold: 0 // Trigger when any part of the foreground enters the viewport
// // //         });
// // //
// // //         observer.observe(foreground);
// // //     });
// // // }
// //
// // const setBannerState = () => {
// //     const scrollPosition = Math.floor(window.scrollY);
// //     const vh = Math.floor(window.innerHeight / 100);
// //     const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
// //     const indexResetPoint = Math.floor((banners.length * step * vh) + (buffer ** buffer * vh));
// //
// //     // Show the banner for the current index and all preceding indexes that haven't been shown yet
// //     if (indexToShow < banners.length) {
// //         for (let i = 0; i <= indexToShow; i++) {
// //             if (banners[i].style.display !== 'inline-block') {
// //                 showBanner(i);
// //             }
// //         }
// //     } else {
// //         for (let index = 0; index < banners.length; index++) {
// //             const threshold = vh * index + ((10+index) * vh);
// //             if ((scrollPosition - indexResetPoint) >= threshold && index > lastIndexHidden) {
// //                 hideBanner(index);
// //                 lastIndexHidden = index;
// //             }
// //         }
// //     }
// // }
// //
// //
// // // The main parallax update function with smoothing and throttling
// // const updateParallaxBackgroundPosition = (() => {
// //     let lastScrollY = 0;            // Track last scroll position to avoid redundant updates
// //     let lastBackgroundPos = 0;      // For smoothing the background position
// //     let lastForegroundPos = 0;      // For smoothing the foreground position
// //
// //     // Function to handle parallax updates
// //     return () => {
// //         let windowYOffset = window.scrollY;
// //         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if there's little movement
// //
// //         // Smooth transition for background position
// //         let backgroundPos = windowYOffset * 0.5;
// //         let smoothedBackgroundPos = lastBackgroundPos + (backgroundPos - lastBackgroundPos) * smoothFactor; // Use global smoothFactor
// //         lastBackgroundPos = smoothedBackgroundPos;
// //
// //         // Update the background position for all elements with the class 'parallax-background'
// //         // document.querySelectorAll('.parallax-background').forEach(function(background) {
// //         const activeBackground = document.querySelector('.active-parallax');
// //         if (activeBackground) {
// //             activeBackground.style.backgroundPosition = '50% 0px';
// //
// //             let foreground = background.querySelector('.parallax-foreground');
// //             if (foreground) {
// //                 // Smooth transition for foreground position
// //                 let foregroundPos = windowYOffset * 0.75;
// //                 let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor; // Use global smoothFactor
// //                 lastForegroundPos = smoothedForegroundPos;
// //
// //                 // Update foreground position
// //                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
// //
// //                 // Optionally adjust height for smoother scrolling
// //                 let foregroundHeight = foreground.clientHeight;
// //                 background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
// //             }
// //         //}
// //             //background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
// //
// //             // let foreground = background.querySelector('.parallax-foreground');
// //             // if (foreground) {
// //             //     // Smooth transition for foreground position
// //             //     let foregroundPos = windowYOffset * 0.75;
// //             //     let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor; // Use global smoothFactor
// //             //     lastForegroundPos = smoothedForegroundPos;
// //             //
// //             //     // Update foreground position
// //             //     foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
// //             //
// //             //     // Optionally adjust height for smoother scrolling
// //             //     let foregroundHeight = foreground.clientHeight;
// //             //     background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
// //             // }
// //         //});
// //
// //         lastScrollY = windowYOffset;  // Update last scroll position
// //
// //         // Request the next animation frame if needed
// //         if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition); // Ensures smooth rendering
// //     }
// // })();
// //
// // // Handle scroll event with throttling
// // const handleScroll = (() => {
// //     const ret = { active: false };
// //     let timeout;
// //
// //     ret.activate = function activate() {
// //         if (ret.active) clearTimeout(timeout); // Prevent multiple calls in quick succession
// //         else {
// //             ret.active = true;
// //             requestAnimationFrame(updateParallaxBackgroundPosition); // Efficiently handle the scroll event
// //         }
// //         timeout = setTimeout(() => ret.active = false, 100);  // **Throttle** the calls to reduce unnecessary updates
// //     };
// //     return ret;
// // })();
// //
// // // Attach the scroll event listener to the window
// // window.addEventListener('scroll', handleScroll.activate); // Handles the scroll event efficiently
// //
// //
// //
// // //
// // // // The main parallax update function with smoothing and throttling
// // // const updateParallaxBackgroundPosition = (() => {
// // //     let lastScrollY = 0;            // Track last scroll position to avoid redundant updates
// // //     let lastBackgroundPos = 0;      // For smoothing the background position
// // //     let lastForegroundPos = 0;      // For smoothing the foreground position
// // //
// // //
// // //
// // //     return () => {
// // //         let windowYOffset = window.scrollY;
// // //         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if there's little movement
// // //
// // //         // Smooth transition for background position
// // //         let backgroundPos = windowYOffset * 0.5;
// // //         let smoothedBackgroundPos = lastBackgroundPos + (backgroundPos - lastBackgroundPos) * smoothFactor;
// // //         lastBackgroundPos = smoothedBackgroundPos;
// // //
// // //         // Update the background position
// // //         backgrounds.forEach(function(background) {
// // //             background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
// // //
// // //             let foreground = background.querySelector('.parallax-foreground');
// // //             if (foreground) {
// // //                 // Smooth transition for foreground position
// // //                 let foregroundPos = windowYOffset * 0.75;
// // //                 let smoothedForegroundPos = lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor;
// // //                 lastForegroundPos = smoothedForegroundPos;
// // //
// // //                 // Update foreground position
// // //                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
// // //
// // //                 // Optionally adjust height for smoother scrolling
// // //                 let foregroundHeight = foreground.clientHeight;
// // //                 background.style.height = `${foregroundHeight * 1.25}px`; // Less frequent height changes
// // //             }
// // //         });
// // //
// // //         lastScrollY = windowYOffset;  // Update last scroll position
// // //
// // //         // Request the next animation frame if needed
// // //         if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition);
// // //     }
// // // })();
// // //
// // //
// // // // Handle scroll event with throttling
// // // const handleScroll = (() => {
// // //     const ret = { active: false };
// // //     let timeout;
// // //
// // //     ret.activate = function activate() {
// // //         if (ret.active) clearTimeout(timeout);
// // //         else {
// // //             ret.active = true;
// // //             requestAnimationFrame(updateParallaxBackgroundPosition);
// // //         }
// // //         timeout = setTimeout(() => ret.active = false, 100);  // Throttling to reduce unnecessary calls
// // //     };
// // //     return ret;
// // // })();
// //
// //
// // // Variables to store the state of the scroll direction
// // let lastScrollY = window.scrollY;
// // let scrollDirection = 'down'; // Default scroll direction
// //
// // // Intersection Observer callback to track when .section-wipe is at the bottom of the viewport
// // const sectionObserver = new IntersectionObserver((entries, observer) => {
// //     entries.forEach(entry => {
// //         if (entry.isIntersecting) {
// //             // Determine the direction of scrolling
// //             if (window.scrollY > lastScrollY) {
// //                 // Scrolling down
// //                 handleScrollingDown(entry.target);
// //             } else {
// //                 // Scrolling up
// //                 handleScrollingUp(entry.target);
// //             }
// //
// //             // Update last scroll position for future scroll direction checks
// //             lastScrollY = window.scrollY;
// //         }
// //     });
// // }, {
// //     root: null, // Observe in the viewport
// //     threshold: 1.0, // Trigger when the bottom of the .section-wipe element is fully in view
// // });
// //
// // // Observe all .section-wipe elements
// // document.querySelectorAll('.section-wipe').forEach(section => {
// //     sectionObserver.observe(section);
// // });
// //
// // // Function to handle scrolling down
// // function handleScrollingDown(section) {
// //     // Find the next .parallax-background element
// //     const nextParallax = section.nextElementSibling && section.nextElementSibling.classList.contains('parallax-background')
// //         ? section.nextElementSibling
// //         : null;
// //
// //     // Remove active class from all .parallax-background elements
// //     document.querySelectorAll('.parallax-background').forEach(background => {
// //         background.classList.remove('active-parallax');
// //     });
// //
// //     // Add active class to the next .parallax-background if it exists
// //     if (nextParallax) {
// //         nextParallax.classList.add('active-parallax');
// //     }
// // }
// //
// // // Function to handle scrolling up
// // function handleScrollingUp(section) {
// //     // Find the previous .parallax-background element
// //     const previousParallax = section.previousElementSibling && section.previousElementSibling.classList.contains('parallax-background')
// //         ? section.previousElementSibling
// //         : null;
// //
// //     // Remove active class from all .parallax-background elements
// //     document.querySelectorAll('.parallax-background').forEach(background => {
// //         background.classList.remove('active-parallax');
// //     });
// //
// //     // Add active class to the previous .parallax-background if it exists
// //     if (previousParallax) {
// //         previousParallax.classList.add('active-parallax');
// //     }
// // }
// //
// //
// //
// //
// //
// // document.addEventListener('DOMContentLoaded', function() {
// //
// //     window.addEventListener('scroll', handleScroll.activate);
// //     window.addEventListener('scroll', setBannerState);
// //     window.addEventListener('resize', setRootFontSize);
// //     // Set up event listener for scrolling (optional, but useful to track scroll direction)
// //     window.addEventListener('scroll', () => {
// //         // Determine scroll direction
// //         scrollDirection = (window.scrollY > lastScrollY) ? 'down' : 'up';
// //         lastScrollY = window.scrollY;
// //     });
// //
// //     updateParallaxBackgroundPosition();
// //     //observeForeground();
// //     recolorBanner();
// //     setRootFontSize();
// // });
// //
// //
// //
// //
// // /*document.addEventListener('DOMContentLoaded', function() {
// //
// //     // Attach the scroll event listener
// //     window.addEventListener('scroll', handleScroll.activate);
// //
// //     // Initialize the parallax effect when the page is loaded
// //     document.addEventListener('DOMContentLoaded', () => {
// //         updateParallaxBackgroundPosition();
// //     });
// //     //updateParallaxBackgroundPosition();
// //
// // /!*    window.addEventListener('scroll', handleScroll.activate);*!/
// //
// //     document.addEventListener('DOMContentLoaded', observeForeground);
// //
// //     recolorBanner();
// //
// //     window.addEventListener('scroll', setBannerState);
// //
// //     // Call setRootFontSize initially and on orientation change
// //     setRootFontSize();
// //     window.addEventListener('resize', setRootFontSize);
// // });*/
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
// /* jshint esversion: 6 */
// //
// // const smoothFactor = 0.1; // Smoothing factor for animations
// // const buffer = 2; // Buffer for scroll logic
// // const step = 6; // Step value for banner animations
// // const banners = document.querySelectorAll('.banner-letter');
// // const banner = document.querySelector('#banner');
// // const backgrounds = document.querySelectorAll('.parallax-background');
// //
// // let isScrollActive = false;
// // let lastIndexHidden = -1; // Track the last hidden banner index
// //
// //
// // const BannerMgr = {
// //
// //     Show: function(index) {
// //         if (index >= 0 && index < banners.length) {
// //             const banner = banners[index];
// //             banner.style.display = 'inline-block';
// //             banner.classList.add('burn');
// //             banner.style.transition = 'color 0.25s ease-in, text-shadow 0.25s ease-in-out';
// //         }
// //     },
// //
// //     Hide: function(index) {
// //         if (index >= 0 && index < banners.length) {
// //             const banner = banners[index];
// //             banner.style.transition = 'color 0.3s ease-out, opacity 0.5s ease-out, text-shadow 0.25s ease-out';
// //             banner.style.color = 'rgb(0, 212, 255)'; // Initial flash color
// //             banner.style.textShadow = '0 0 10px rgba(255, 255, 255, 0.9)';
// //
// //             setTimeout(() => {
// //                 banner.style.color = 'rgb(255, 255, 255)';
// //                 banner.style.transition = 'color 3s ease, opacity 3s ease-out, text-shadow 3s ease-out';
// //
// //                 setTimeout(() => {
// //                     banner.style.color = 'rgb(0, 0, 0)';
// //                     banner.style.opacity = '0';
// //                     banner.style.textShadow = '0 0 10px rgba(255, 255, 255, 0.8)';
// //                 }, 500);
// //             }, 250);
// //         }
// //
// //         if (index === banners.length) {
// //             banner.style.background = 'transparent';
// //             banners.forEach(banner => banner.style.color = 'transparent');
// //         }
// //     },
// //
// //     Recolor: function() {
// //         const firstSectionWipe = document.getElementById('first-wipe');
// //         const recolorBannerObserver = new IntersectionObserver(entries => {
// //             entries.forEach(entry => {
// //                 if (entry.boundingClientRect.top < 0) {
// //                     document.querySelector('#banner').style.backgroundColor = 'rgba(0, 0, 0, 1)';
// //                     banners.forEach(banner => {
// //                         banner.style.color = 'darkorange';
// //                         banner.style.opacity = '1';
// //                     });
// //                 }
// //             });
// //         });
// //
// //         recolorBannerObserver.observe(firstSectionWipe);
// //     },
// //
// //     SetState: function() {
// //         const scrollPosition = Math.floor(window.scrollY);
// //         const vh = Math.floor(window.innerHeight / 100);
// //         const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
// //         const indexResetPoint = Math.floor((banners.length * step * vh) + (buffer ** buffer * vh));
// //
// //         if (indexToShow < banners.length) {
// //             for (let i = 0; i <= indexToShow; i++) {
// //                 if (banners[i].style.display !== 'inline-block') {
// //                     BannerMgr.Show(i);
// //                 }
// //             }
// //         } else {
// //             for (let index = 0; index < banners.length; index++) {
// //                 const threshold = vh * index + ((10 + index) * vh);
// //                 if ((scrollPosition - indexResetPoint) >= threshold && index > lastIndexHidden) {
// //                     BannerMgr.Hide(index);
// //                     lastIndexHidden = index;
// //                 }
// //             }
// //         }
// //     }
// // };
// //
// //
// // const Page = {
// //
// //     SetRootFontSize: function () {
// //         const root = document.documentElement;
// //         root.style.setProperty('--root-font-size', window.innerHeight > window.innerWidth ? '10px' : '20px');
// //     },
// //
// //     HandleScrollEvents: function () {
// //         Page.HandleScroll();
// //         BannerMgr.SetState();
// //     },
// //
// //     UpdateParallaxBackgroundPosition: function () {
// //         let lastScrollY = 0
// //         const lastBackgroundPos = {}; // Store smoothed background positions
// //         const lastForegroundPos = {}; // Store smoothed foreground positions
// //
// //         const isElementInViewport = (el) => {
// //             const rect = el.getBoundingClientRect();
// //             return rect.top < window.innerHeight && rect.bottom > 0;
// //         };
// //
// //         const windowYOffset = window.scrollY;
// //         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if no significant movement
// //
// //         document.querySelectorAll('.parallax-background').forEach(background => {
// //             if (!isElementInViewport(background)) return;
// //
// //             const sectionId = background.dataset.section;
// //
// //             const backgroundPos = windowYOffset * 0.5;
// //             const smoothedBackgroundPos =
// //                 (lastBackgroundPos[sectionId] || 0) + (backgroundPos - (lastBackgroundPos[sectionId] || 0)) * smoothFactor;
// //             lastBackgroundPos[sectionId] = smoothedBackgroundPos;
// //             background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
// //
// //             const foreground = background.querySelector('.parallax-foreground');
// //             if (foreground) {
// //                 const foregroundPos = windowYOffset * 0.75;
// //                 const smoothedForegroundPos =
// //                     (lastForegroundPos[sectionId] || 0) + (foregroundPos - (lastForegroundPos[sectionId] || 0)) * smoothFactor;
// //                 lastForegroundPos[sectionId] = smoothedForegroundPos;
// //                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
// //
// //                 const foregroundHeight = foreground.clientHeight;
// //                 background.style.height = `${foregroundHeight * 1.25}px`;
// //             }
// //         });
// //
// //         lastScrollY = windowYOffset;
// //     },
// //
// //
// //     // UpdateParallaxBackgroundPosition: function () {
// //     //     let lastScrollY = 0; // Track last scroll position
// //     //     const lastBackgroundPos = {}; // Store smoothed background positions
// //     //     const lastForegroundPos = {}; // Store smoothed foreground positions
// //     //
// //     //     const isElementInViewport = (el) => {
// //     //         const rect = el.getBoundingClientRect();
// //     //         return rect.top < window.innerHeight && rect.bottom > 0;
// //     //     };
// //     //
// //     //     return () => {
// //     //         const windowYOffset = window.scrollY;
// //     //         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if no significant movement
// //     //
// //     //         document.querySelectorAll('.parallax-background').forEach(background => {
// //     //             if (!isElementInViewport(background)) return;
// //     //
// //     //             const sectionId = background.dataset.section;
// //     //
// //     //             const backgroundPos = windowYOffset * 0.5;
// //     //             const smoothedBackgroundPos =
// //     //                 (lastBackgroundPos[sectionId] || 0) + (backgroundPos - (lastBackgroundPos[sectionId] || 0)) * smoothFactor;
// //     //             lastBackgroundPos[sectionId] = smoothedBackgroundPos;
// //     //             background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
// //     //
// //     //             const foreground = background.querySelector('.parallax-foreground');
// //     //             if (foreground) {
// //     //                 const foregroundPos = windowYOffset * 0.75;
// //     //                 const smoothedForegroundPos =
// //     //                     (lastForegroundPos[sectionId] || 0) + (foregroundPos - (lastForegroundPos[sectionId] || 0)) * smoothFactor;
// //     //                 lastForegroundPos[sectionId] = smoothedForegroundPos;
// //     //                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
// //     //
// //     //                 const foregroundHeight = foreground.clientHeight;
// //     //                 background.style.height = `${foregroundHeight * 1.25}px`;
// //     //             }
// //     //         });
// //     //
// //     //         lastScrollY = windowYOffset;
// //     //     };
// //     // },
// //
// //     HandleScroll: function () {
// //         if (!isScrollActive) {
// //             isScrollActive = true;
// //             requestAnimationFrame(() => {
// //                 Page.UpdateParallaxBackgroundPosition();
// //                 isScrollActive = false;
// //             });
// //         }
// //     }
// // };
// //
// //
// // document.addEventListener('DOMContentLoaded', () => {
// //     window.addEventListener('scroll', Page.HandleScrollEvents);
// //     window.addEventListener('resize', Page.SetRootFontSize);
// //     Page.UpdateParallaxBackgroundPosition();
// //     BannerMgr.Recolor();
// //     Page.SetRootFontSize();
// // });
//
// //
// // /** Set root font size based on orientation */
// // // function setRootFontSize() {
// // //     const root = document.documentElement;
// // //     root.style.setProperty('--root-font-size', window.innerHeight > window.innerWidth ? '10px' : '20px');
// // // }
// // //
// // // /** Show a banner letter with animation */
// // // function showBanner(index) {
// // //     if (index >= 0 && index < banners.length) {
// // //         const banner = banners[index];
// // //         banner.style.display = 'inline-block';
// // //         banner.classList.add('burn');
// // //         banner.style.transition = 'color 0.25s ease-in, text-shadow 0.25s ease-in-out';
// // //     }
// // // }
// // //
// // // function hideBanner(index) {
// // //     if (index >= 0 && index < banners.length) {
// // //         const banner = banners[index];
// // //         banner.style.transition = 'color 0.3s ease-out, opacity 0.5s ease-out, text-shadow 0.25s ease-out';
// // //         banner.style.color = 'rgb(0, 212, 255)'; // Initial flash color
// // //         banner.style.textShadow = '0 0 10px rgba(255, 255, 255, 0.9)';
// // //
// // //         setTimeout(() => {
// // //             banner.style.color = 'rgb(255, 255, 255)';
// // //             banner.style.transition = 'color 3s ease, opacity 3s ease-out, text-shadow 3s ease-out';
// // //
// // //             setTimeout(() => {
// // //                 banner.style.color = 'rgb(0, 0, 0)';
// // //                 banner.style.opacity = '0';
// // //                 banner.style.textShadow = '0 0 10px rgba(255, 255, 255, 0.8)';
// // //             }, 500);
// // //         }, 250);
// // //     }
// // //
// // //     if (index === banners.length) {
// // //         banner.style.background = 'transparent';
// // //         banners.forEach(banner => banner.style.color = 'transparent');
// // //     }
// // // }
// // //
// // // /** Recolor banner when scrolling past a specific section */
// // // function recolorBanner() {
// // //     const firstSectionWipe = document.getElementById('first-wipe');
// // //     const recolorBannerObserver = new IntersectionObserver(entries => {
// // //         entries.forEach(entry => {
// // //             if (entry.boundingClientRect.top < 0) {
// // //                 document.querySelector('#banner').style.backgroundColor = 'rgba(0, 0, 0, 1)';
// // //                 banners.forEach(banner => {
// // //                     banner.style.color = 'darkorange';
// // //                     banner.style.opacity = '1';
// // //                 });
// // //             }
// // //         });
// // //     });
// // //
// // //     recolorBannerObserver.observe(firstSectionWipe);
// // // }
// //
// // // function handleScrollEvents() {
// // //     handleScroll();
// // //     BannerMgr.SetState();
// // // }
// //
// // /** Adjust banner state based on scroll position */
// // // function setBannerState() {
// // //     const scrollPosition = Math.floor(window.scrollY);
// // //     const vh = Math.floor(window.innerHeight / 100);
// // //     const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
// // //     const indexResetPoint = Math.floor((banners.length * step * vh) + (buffer ** buffer * vh));
// // //
// // //     if (indexToShow < banners.length) {
// // //         for (let i = 0; i <= indexToShow; i++) {
// // //             if (banners[i].style.display !== 'inline-block') {
// // //                 showBanner(i);
// // //             }
// // //         }
// // //     } else {
// // //         for (let index = 0; index < banners.length; index++) {
// // //             const threshold = vh * index + ((10 + index) * vh);
// // //             if ((scrollPosition - indexResetPoint) >= threshold && index > lastIndexHidden) {
// // //                 hideBanner(index);
// // //                 lastIndexHidden = index;
// // //             }
// // //         }
// // //     }
// // // }
// //
// // /** Update parallax backgrounds only when in the viewport */
// //
// // // let isScrollActive = false;
// //
// // // function handleScroll() {
// // //     if (!isScrollActive) {
// // //         isScrollActive = true;
// // //         requestAnimationFrame(() => {
// // //             updateParallaxBackgroundPosition();
// // //             isScrollActive = false;
// // //         });
// // //     }
// // // }
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
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
// //
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
// //
// // const updateParallaxBackgroundPosition = (() => {
// //     let lastScrollY = 0;            // Track last scroll position to avoid redundant updates
// //     let lastBackgroundPos = {};    // Store smoothed positions per element
// //     let lastForegroundPos = {};    // Store smoothed positions per element
// //
// //     const isElementInViewport = (el) => {
// //         const rect = el.getBoundingClientRect();
// //         return (
// //             rect.top < window.innerHeight && rect.bottom > 0 // Element is partially visible
// //         );
// //     };
// //
// //     return () => {
// //         let windowYOffset = window.scrollY;
// //         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if there's little movement
// //
// //         // Iterate through all parallax backgrounds
// //         document.querySelectorAll('.parallax-background').forEach((background) => {
// //             // Check if the background is in the viewport
// //             if (!isElementInViewport(background)) {
// //                 console.log('not in viewport')
// //                 return;
// //             }
// //             console.log(`IN VIEW: ${background.dataset.section}`);
// //             const sectionId = background.dataset.section;
// //
// //             // Smooth transition for background position
// //             let backgroundPos = windowYOffset * 0.5;
// //             let smoothedBackgroundPos =
// //                 (lastBackgroundPos[sectionId] || 0) + (backgroundPos - (lastBackgroundPos[sectionId] || 0)) * smoothFactor;
// //             lastBackgroundPos[sectionId] = smoothedBackgroundPos;
// //
// //             // Update the background position
// //             background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
// //
// //             let foreground = background.querySelector('.parallax-foreground');
// //             if (foreground) {
// //                 // Smooth transition for foreground position
// //                 let foregroundPos = windowYOffset * 0.75;
// //                 let smoothedForegroundPos =
// //                     (lastForegroundPos[sectionId] || 0) + (foregroundPos - (lastForegroundPos[sectionId] || 0)) * smoothFactor;
// //                 lastForegroundPos[sectionId] = smoothedForegroundPos;
// //
// //                 // Update foreground position
// //                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
// //
// //                 // Optionally adjust height for smoother scrolling
// //                 let foregroundHeight = foreground.clientHeight;
// //                 background.style.height = `${foregroundHeight * 1.25}px`;
// //             }
// //         });
// //
// //         lastScrollY = windowYOffset;  // Update last scroll position
// //
// //         // Request the next animation frame if needed
// //         if (handleScroll.active) requestAnimationFrame(updateParallaxBackgroundPosition);
// //     };
// // })();
//
// UpdateParallaxBackgroundPosition = function () {
//     const cumulativeOffsets = {}; // Store cumulative offsets for each section
//     const lastBackgroundPos = {}; // Store smoothed background positions
//     const lastForegroundPos = {}; // Store smoothed foreground positions
//     let lastScrollY = 0; // Track the last scroll position
//
//     const isElementInViewport = (el) => {
//         const rect = el.getBoundingClientRect();
//         return rect.top < window.innerHeight && rect.bottom > 0;
//     };
//
//     const observer = new IntersectionObserver(
//         (entries) => {
//             entries.forEach((entry) => {
//                 const sectionId = entry.target.dataset.section;
//
//                 if (!entry.isIntersecting && entry.boundingClientRect.top < 0) {
//                     // The element has exited the viewport at the top
//                     cumulativeOffsets[sectionId] = parseFloat(
//                         entry.target.style.backgroundPosition.split(" ")[1]
//                     ) || 0;
//                 }
//             });
//         },
//         { threshold: 0 }
//     );
//
//     // Observe all .parallax-background elements
//     document.querySelectorAll('.parallax-background').forEach((background) => {
//         observer.observe(background);
//     });
//
//     return function () {
//         const windowYOffset = window.scrollY;
//         if (Math.abs(windowYOffset - lastScrollY) < 1) return; // Skip if no significant movement
//
//         document.querySelectorAll('.parallax-background').forEach((background) => {
//             if (!isElementInViewport(background)) return;
//
//             const sectionId = background.dataset.section;
//
//             // Use the cumulative offset when calculating background position
//             const cumulativeOffset = cumulativeOffsets[sectionId] || 0;
//             const backgroundPos = windowYOffset * 0.5 + cumulativeOffset;
//
//             const smoothedBackgroundPos =
//                 (lastBackgroundPos[sectionId] || 0) + (backgroundPos - (lastBackgroundPos[sectionId] || 0)) * smoothFactor;
//             lastBackgroundPos[sectionId] = smoothedBackgroundPos;
//
//             // Update the background position
//             background.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
//
//             const foreground = background.querySelector('.parallax-foreground');
//             if (foreground) {
//                 const foregroundPos = windowYOffset * 0.75 + cumulativeOffset;
//
//                 const smoothedForegroundPos =
//                     (lastForegroundPos[sectionId] || 0) + (foregroundPos - (lastForegroundPos[sectionId] || 0)) * smoothFactor;
//                 lastForegroundPos[sectionId] = smoothedForegroundPos;
//
//                 // Update foreground position
//                 foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//
//                 // Adjust background height based on foreground
//                 const foregroundHeight = foreground.clientHeight;
//                 background.style.height = `${foregroundHeight * 1.25}px`;
//             }
//         });
//
//         lastScrollY = windowYOffset; // Update the last scroll position
//     };
// }();
//
//
//
// // // The main parallax update function with smoothing and throttling
// // const updateParallaxBackgroundPosition = (() => {
// //     let lastScrollY = 0;            // Track last scroll position to avoid redundant updates
// //     let lastBackgroundPos = 0;      // For smoothing the background position
// //     let lastForegroundPos = 0;      // For smoothing the foreground position
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
//
//
// // Handle scroll event with throttling
// const handleScroll = (() => {
//     const ret = { active: false };
//     let timeout;
//
//     ret.activate = function activate() {
//         if (ret.active) clearTimeout(timeout);
//         else {
//             ret.active = true;
//             requestAnimationFrame(updateParallaxBackgroundPosition);
//         }
//         timeout = setTimeout(() => ret.active = false, 0);  // Throttling to reduce unnecessary calls
//     };
//     return ret;
// })();
//
// document.addEventListener('DOMContentLoaded', function() {
//     window.addEventListener('scroll', handleScroll.activate);
//     window.addEventListener('scroll', setBannerState);
//     window.addEventListener('resize', setRootFontSize);
//     updateParallaxBackgroundPosition();
//     recolorBanner();
//     setRootFontSize();
// });
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
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
