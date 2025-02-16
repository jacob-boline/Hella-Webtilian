// /* jshint esversion: 6 */
//
// const smoothFactor = 0.1; // Smoothing factor
//
// let lastBackgroundPos = 0; // Store smoothed background positions
// let lastForegroundPos = 0; // Store smoothed foreground positions
// let lastScrollY = 0; // Track the last scroll position
// let cumulativeOffset = 0; // The global offset for the parallax effect
// let activeSection = null; // The currently active section
//
// let lastIndexHidden = -1;
// const buffer = 2;
// const banners = document.querySelectorAll('.banner-letter');
// const step = 6;//8;
// const banner = document.querySelector('#banner');
//
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
//     recolorBannerObserver.observe(firs tSectionWipe);
// }
//
//
// const setBannerState = () => {
//     console.log('top of setBannerState');
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
//
// function getSectionWipeHeightsBefore(section) {
//     const wipes = Array.from(document.querySelectorAll('.section-wipe'));
//     let totalHeight = 0;
//
//     for (const wipe of wipes) {
//         if (wipe.compareDocumentPosition(section) & Node.DOCUMENT_POSITION_FOLLOWING) {
//             break; // Stop if we reach the target section
//         }
//         totalHeight += wipe.offsetHeight;
//     }
//
//     return totalHeight;
// }
//
// const observer = new IntersectionObserver((entries) => {
//     entries.forEach((entry) => {
//         const rect = entry.target.getBoundingClientRect();
//
//         if (entry.isIntersecting) {
//             // When the section enters the viewport, calculate the offset
//             cumulativeOffset = getSectionWipeHeightsBefore(entry.target) + window.scrollY - rect.bottom;
//             activeSection = entry.target;
//         } else if (!entry.isIntersecting && rect.top < 0) {
//             // When the section exits the viewport at the top
//             cumulativeOffset = getSectionWipeHeightsBefore(entry.target) + window.scrollY - rect.bottom;
//             activeSection = null; // Reset if fully exited
//         }
//     });
// });
//
//
// const UpdateParallaxBackgroundPosition = () => {
//     if (!activeSection) return; // Skip if no active section
//
//     const windowYOffset = window.scrollY;
//     const backgroundPos = windowYOffset * 0.5 + cumulativeOffset;
//
//     const smoothedBackgroundPos =
//         lastBackgroundPos + (backgroundPos - lastBackgroundPos) * smoothFactor;
//     lastBackgroundPos = smoothedBackgroundPos;
//
//     activeSection.style.backgroundPosition = `50% ${smoothedBackgroundPos}px`;
//
//     const foreground = activeSection.querySelector('.parallax-foreground');
//     if (foreground) {
//         const foregroundPos = windowYOffset * 0.75 + cumulativeOffset;
//
//         const smoothedForegroundPos =
//             lastForegroundPos + (foregroundPos - lastForegroundPos) * smoothFactor;
//         lastForegroundPos = smoothedForegroundPos;
//
//         foreground.style.backgroundPosition = `50% ${smoothedForegroundPos}px`;
//     }
// };
//
//
// document.addEventListener('DOMContentLoaded', () => {
//     // Attach scroll event
//     window.addEventListener('scroll', () => {
//         requestAnimationFrame(() => {
//             UpdateParallaxBackgroundPosition();
//             setBannerState();
//         });w
//     });
//
//     // Observe only .parallax-background elements
//     document.querySelectorAll('.parallax-background').forEach((background) => {
//         observer.observe(background);
//     });
//     window.addEventListener('resize', setRootFontSize);
//     // Initial setup
//     UpdateParallaxBackgroundPosition(); // Ensure the initial state is set
//     recolorBanner();
//     setRootFontSize();
// });
