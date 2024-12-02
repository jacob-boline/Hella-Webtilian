// Select all sticky containers
const stickyContainers = document.querySelectorAll('.sticky-container');

// Function to handle parallax and sticky behavior
function updateParallax() {
    stickyContainers.forEach((container) => {
        const content = container.querySelector('.content');
        const image = container.querySelector('.parallax-image');
        const text = container.querySelector('.text');

        // Get container and image dimensions
        const containerRect = container.getBoundingClientRect();
        const imageHeight = image.offsetHeight;
        const textHeight = text.offsetHeight; // Height of the text
        const viewportHeight = window.innerHeight; // Height of the viewport

        // Calculate the maximum scroll range
        const maxScroll = Math.max(textHeight - viewportHeight, 1); // Avoid division by 0
        const padding = 50; // Adjust padding as needed
        const maxTransform = imageHeight - viewportHeight + padding;

        // Debug output
        console.log({ maxScroll, maxTransform, imageHeight });

        if (containerRect.top <= 0 && containerRect.bottom > imageHeight) {
            // Sticky phase: adjust parallax effect
            const scrollOffset = Math.abs(containerRect.top);
            const scrollFraction = Math.min(scrollOffset / maxScroll, 1); // Ensure it doesn't exceed 1
            const transformValue = scrollFraction * maxTransform;

            image.style.transform = `translateY(-${transformValue}px)`;
            content.style.position = 'sticky';
        } else if (containerRect.bottom <= imageHeight) {
            // After sticky phase: stop sticky behavior
            content.style.position = 'relative';
            image.style.transform = `translateY(-${maxTransform}px)`;
        } else {
            // Before sticky phase: reset
            content.style.position = 'relative';
            image.style.transform = `translateY(0)`;
        }
    });
}

// Adjust spacing for content below sticky containers
function adjustSpacing() {
    stickyContainers.forEach(container => {
        const nextContent = container.nextElementSibling;
        if (nextContent) {
            const containerHeight = container.offsetHeight;
            nextContent.style.marginTop = `${containerHeight}px`;
        }
    });
}

// Run on load and scroll
window.addEventListener('load', () => {
    adjustSpacing();
    updateParallax();
});
window.addEventListener('scroll', updateParallax);
window.addEventListener('resize', adjustSpacing);
