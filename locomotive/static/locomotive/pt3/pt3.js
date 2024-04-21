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

let lastIndexHidden = -1;
const buffer = 2; // represents 2vh
const banners = document.querySelectorAll('.banner-letter');
const step = 8; // Show one banner for every 8vh scrolled
const banner = document.querySelector('#banner');



document.addEventListener('DOMContentLoaded', function() {
    // const banners = document.querySelectorAll('.banner-letter');
    // const buffer = 2; // 2vh buffer at the beginning
    // const step = 8; // Show one banner for every 8vh scrolled



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

    function handleScroll() {
        const scrollPosition = Math.floor(window.scrollY);
        const vh = Math.floor(window.innerHeight / 100);
        const indexToShow = Math.floor((scrollPosition / (step * vh))) - buffer;
        const indexResetPoint = Math.floor((banners.length * step * vh) + (buffer**buffer * vh));

        if (indexToShow < banners.length) {
            showBanner(indexToShow);
        } else {
            for (let index = 0; index < banners.length; index++) {
                const threshold = 2.5 * vh * index;
                if (((scrollPosition - indexResetPoint) >= threshold) && (index > lastIndexHidden)) {
                    hideBanner(index);
                    lastIndexHidden = index;
                }
            }
        }
    }
//     function showBanner(index) {
//         if (index < banners.length) {
//             banners[index].style.display = 'inline-block';
//         }
//     }
//
//     function handleScroll() {
//         const scrollPosition = window.scrollY || window.pageYOffset;
//         const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
//         const scrolledVh = scrollPosition / vh;
//         const indexToShow = Math.floor(scrolledVh / step) - buffer;
//
//         showBanner(indexToShow);
//     }

// function makeSticky(entries, observer) {
    //     entries.forEach(entry => {
    //         if (entry.isIntersecting) {
    //             const section = entry.target;
    //             section.classList.add('sticky');
    //             observer.unobserve(section);
    //         }
    //     });
    // }

    function makeSticky(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const background = entry.target;
                background.classList.add('sticky');
                //background.style.top = '10vh';
                observer.unobserve(background);
            }
        });
    }

    function observeBackground() {
        const backgrounds = document.querySelectorAll('.parallax-background');
        const observer = new IntersectionObserver(makeSticky, { threshold: 1 });
        backgrounds.forEach(background => {
            observer.observe(background);
        });
    }

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

    function observeWipe() {
        // console.log('observeWipe called');
        // const firstSectionWipe = document.querySelector('.img-wrapper:first-of-type img');
        const firstSectionWipe = document.querySelector('#page-wrapper > div:first-of-type img');
        if (!firstSectionWipe) {
            console.error('could not find the target element for intersection observation');
        }
        const firstWipeObserver = new IntersectionObserver(entries => {
            // console.log('callback firstWipeObserver called');
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const bannerLetters = document.querySelectorAll('.banner-letter');
                    // bannerLetters.style.color = 'darkorange';
                    bannerLetters.forEach(letter => {
                        letter.style.color = 'lime';
                    });
                    firstWipeObserver.disconnect();
                }
            });
        }, { threshold: 1 });
        firstWipeObserver.observe(firstSectionWipe);
    }

    // function observeSections() {
    //     const sections = document.querySelectorAll('.content-section');
    //     const observer = new IntersectionObserver(makeSticky, { threshold: 1 });
    //
    //     sections.forEach(section => {
    //         observer.observe(section);
    //     });
    // }

    function updateParallaxBackgroundPosition() {
        let windowYOffset = window.scrollY;
        let backgrounds = document.querySelectorAll('.parallax-background');
        const colors = ['hotpink', 'lime', 'dodgerblue', 'yellow'];
        let colorIndex = 0;

        backgrounds.forEach(background => {
            let scrollPosition = window.scrollY;
            let backgroundPosition = '50% ' + scrollPosition * 0.5 + 'px';
            let foregroundPosition = '50% ' + scrollPosition * 0.75 + 'px';

            background.style.backgroundPosition = backgroundPosition;
            let foreground = background.querySelector('.parallax-foreground');
            foreground.style.backgroundPosition = foregroundPosition;
            let vh = Math.max(document.documentElement.clientHeight/100);
            background.style.height = 1.25 * foreground.offsetHeight + (1.5 * vh) + 'px'
        })
        // backgrounds.forEach(function(background) {
        //     background.style.backgroundPosition = '50% ' + (windowYOffset * 0.5) + 'px';
        //     let foreground = background.querySelector('.parallax-foreground');
        //     if (foreground) {
        //         console.log('have foreground');
        //         foreground.style.backgroundPosition = '50% ' + (windowYOffset * 0.75) + 'px';
        //         foreground.style.color = colors.at(colorIndex);
        //         colorIndex ++;
        //         let foregroundHeight = foreground.offsetHeight;
        //         const vh = Math.max(document.documentElement.clientHeight/100);
        //         // background.style.height = (foregroundHeight * 1.5) - ((foregroundHeight * (2/3))) + 1.5*vh + 'px';
        //         //background.style.height = 1.25 * foregroundHeight + 1.5 * vh + 'px';
        //         background.style.height = 1.15 * foregroundHeight + (2 * vh) + 'px';
        //     }
        // });
    }

    // Update background position on scroll


    // Initial update
    updateParallaxBackgroundPosition();

    document.addEventListener('DOMContentLoaded', observeBackground);
    // document.addEventListener('DOMContentLoaded', observeForeground);
    document.addEventListener('DOMContentLoaded', observeWipe);
    window.addEventListener('scroll', updateParallaxBackgroundPosition);
    window.addEventListener('scroll', handleScroll);

});




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
// document.addEventListener('DOMContentLoaded', function() {
//     let lastIndexHidden = -1;
//     const buffer = 2; // represents 2vh
//     const banners = document.querySelectorAll('.banner-letter');
//     const step = 8; // Show one banner for every 8vh scrolled
//     const banner = document.querySelector('#banner');
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
//                 const threshold = 2 * vh * index;
//                 if ((scrollPosition - indexResetPoint) >= threshold && index > lastIndexHidden) {
//                     hideBanner(index);
//                     lastIndexHidden = index;
//                 }
//             }
//         }
//     }
//
//     function makeSticky(entries, observer) {
//         entries.forEach(entry => {
//             if (entry.isIntersecting) {
//                 const background = entry.target;
//                 background.classList.add('sticky');
//                 background.style.top = '10vh';
//                 observer.unobserve(background);
//             }
//         });
//     }
//
//     function observeBackground() {
//         const backgrounds = document.querySelectorAll('.parallax-background');
//         const observer = new IntersectionObserver(makeSticky, { threshold: 1 });
//         backgrounds.forEach(background => {
//             observer.observe(background);
//         });
//     }
//
//     // function observeForeground() {
//     //     const foreground = document.querySelector('.parallax-foreground');
//     //     const observer = new IntersectionObserver(entries => {
//     //         entries.forEach(entry => {
//     //             if (entry.intersectionRatio > 0) {
//     //                 const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
//     //                 const distanceFromBottom = vh - entry.boundingClientRect.bottom;
//     //                 if (distanceFromBottom >= 15 * vh / 100) {
//     //                     section.classList.remove('sticky');
//     //                 }
//     //             }
//     //         });
//     //     }, {
//     //         threshold: 0 // Trigger when any part of the foreground enters the viewport
//     //     });
//     //
//     //     observer.observe(foreground);
//     // }
//
//     function observeForeground() {
//         const foregrounds = document.querySelectorAll('.parallax-foreground');
//
//         foregrounds.forEach(foreground => {
//             const observer = new IntersectionObserver(entries => {
//                 entries.forEach(entry => {
//                     const section = entry.target.closest('section');
//                     if (!section) return; // If no section ancestor found, exit
//                     if (entry.intersectionRatio > 0) {
//                         const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
//                         const distanceFromBottom = vh - entry.boundingClientRect.bottom;
//                         if (distanceFromBottom >= 15 * vh / 100) {
//                             section.classList.remove('sticky');
//                         }
//                     }
//                 });
//             }, {
//                 threshold: 0 // Trigger when any part of the foreground enters the viewport
//             });
//
//             observer.observe(foreground);
//         });
//     }
//
//     // function observeWipe() {
//     //     // console.log('observeWipe called');
//     //     const firstSectionWipe = document.querySelector('.img-wrapper:first-of-type img');
//     //     // const firstSectionWipe = document.querySelector('#page-wrapper > div:first-of-type img');
//     //     if (!firstSectionWipe) {
//     //         console.error('could not find the target element for intersection observation');
//     //     }
//     //     const firstWipeObserver = new IntersectionObserver(entries => {
//     //         // console.log('callback firstWipeObserver called');
//     //         entries.forEach(entry => {
//     //             if (entry.isIntersecting) {
//     //                 const bannerLetters = document.querySelectorAll('.banner-letter');
//     //                 // bannerLetters.style.color = 'darkorange';
//     //                 bannerLetters.forEach(letter => {
//     //                     letter.style.color = 'lime';
//     //                 });
//     //                 firstWipeObserver.disconnect();
//     //             }
//     //         });
//     //     }, { threshold: 1 });
//     //     firstWipeObserver.observe(firstSectionWipe);
//     // }
//
//     function updateParallaxBackgroundPosition() {
//         // console.log('top updateParallaxBackgroundPosition');
//         let windowYOffset = window.scrollY;
//         let backgrounds = document.querySelectorAll('.parallax-background');
//
//         backgrounds.forEach(function(background) {
//             background.style.backgroundPosition = '50% ' + (windowYOffset * 0.5) + 'px';
//             // console.log('style.backgroundPosition = ', background.style.backgroundPosition);
//             let foreground = background.querySelector('.parallax-foreground');
//             if (foreground) {
//                 foreground.style.backgroundPosition = '50% ' + (windowYOffset * 0.75) + 'px';
//                 let foregroundHeight = foreground.clientHeight;
//                 const vh = window.innerHeight / 100;
//                 background.style.height = (foregroundHeight * 1.5) - ((foregroundHeight * (2/3))) + 20*vh + 'px';  // was 1.5*vh
//                 //console.log('backgroun.style.height = ', background.style.height);
//             }
//         });
//     }
//     window.addEventListener('scroll', updateParallaxBackgroundPosition);
//     updateParallaxBackgroundPosition();
//
//     document.addEventListener('DOMContentLoaded', observeBackground);
//     document.addEventListener('DOMContentLoaded', observeForeground);
//     //document.addEventListener('DOMContentLoaded', observeWipe);
//     window.addEventListener('scroll', handleScroll);
//
//
// });
//
