/**
 * hr_about/static/hr_about/css/carousel.js
 */

export function initAboutCarousel(root = document) {
    const container = root.querySelector('#about-carousel');
    if (!container) { return; }

    const stageImg = container.querySelector('.about-stage-img');
    const thumbs = Array.from(container.querySelectorAll('.about-thumb'));
    const prevBtn = container.querySelector('.about-nav.prev');
    const nextBtn = container.querySelector('.about-nav.next');

    if (!stageImg || thumbs.length === 0) { return; }

    function showFromThumb(thumb) {
        const { src, alt } = thumb.dataset;

        if (src) { stageImg.src =  src; }
        if (alt) { stageImg.alt = alt; }

        thumbs.forEach(t => t.classList.remove('is-active'));
        thumb.classList.add('is-active');
    }

    function showRelative(delta) {
        const currentIndex = thumbs.findIndex(t =>
            t.classList.contains('is-active')
        );
        const nextIndex = (currentIndex + delta + thumbs.length) % thumbs.length;
        showFromThumb(thumbs[nextIndex]);
    }

    thumbs.forEach(thumb => {
        thumb.addEventListener('click', () => showFromThumb(thumb));
    });

    if (prevBtn) { prevBtn.addEventListener('click', () => showRelative(-1)); }
    if (nextBtn) { nextBtn.addEventListener('click', () => showRelative(1)); }

    const active = thumbs.find(t => t.classList.contains('is-active'));
    if (active) { showFromThumb(active); }
}