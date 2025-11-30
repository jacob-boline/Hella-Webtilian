/* hr_about/static/hr_about/js/carousel.js */

export function initAboutCarousel(root = document) {
    const container = root.querySelector('#about-carousel');
    if (!container) return;

    const stage = container.querySelector('.about-stage') || container;
    const stageImg = container.querySelector('.about-stage-img');

    const thumbsUl = container.querySelector('.about-thumbs');
    const thumbs = thumbsUl ? Array.from(thumbsUl.querySelectorAll('button.about-thumb')) : [];

    const prevBtn = container.querySelector('.about-nav.prev');
    const nextBtn = container.querySelector('.about-nav.next');
    const thumbsPrev = container.querySelector('.thumbs-prev');
    const thumbsNext = container.querySelector('.thumbs-next');

    if (!stageImg || !thumbs.length) return;

    const mod = (n, m) => ((n % m) + m) % m;

    function centerThumb(thumb, rail) {
        if (!thumb || !rail) return;
        const railRect = rail.getBoundingClientRect();
        const liRect = thumb.getBoundingClientRect();
        const current = rail.scrollLeft;
        const target =
            current +
            (liRect.left - railRect.left) -
            (railRect.width / 2 - liRect.width / 2);
        rail.scrollTo({ left: target, behavior: 'smooth' });
    }

    function swipeBinder(el, onSwipe) {
        let x0 = null;
        let t0 = 0;

        const onTouchStart = (e) => {
            if (!e.touches || !e.touches.length) return;
            x0 = e.touches[0].clientX;
            t0 = Date.now();
        };

        const onTouchEnd = (e) => {
            if (x0 == null || !e.changedTouches || !e.changedTouches.length) return;
            const dx = e.changedTouches[0].clientX - x0;
            const dt = Date.now() - t0;
            x0 = null;
            if (Math.abs(dx) > 40 && dt < 600) {
                onSwipe(dx < 0 ? 'next' : 'prev');
            }
        };

        el.addEventListener('touchstart', onTouchStart, { passive: true });
        el.addEventListener('touchend', onTouchEnd);

        return () => {
            el.removeEventListener('touchstart', onTouchStart);
            el.removeEventListener('touchend', onTouchEnd);
        };
    }

    // ------------------ STATE ---------------------
    const itemCount = thumbs.length;
    let index = 0;
    let cleanupSwipe = null;

    // ----------------- ARIA setup ------------------

    if (thumbsUl) {
        thumbsUl.setAttribute('role', 'tablist');
    }

    stage.setAttribute('role', 'group');

    thumbs.forEach((li, i) => {
        li.setAttribute('role', 'tab');
        li.setAttribute('aria-selected', 'false');
        li.setAttribute('tabindex', '-1');

        li.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setActive(i, true);
            }
            if (e.key === 'ArrowRight') {
                e.preventDefault();
                setActive(i + 1, true);
            }
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                setActive(i - 1, true);
            }
        });
    });

    // --------------- DATA ACCESS -----------------
    function getItemData(i) {
        const thumb = thumbs[i];
        if (!thumb) return null;

        const { src, alt } = thumb.dataset;
        if (!src) return null;

        return { src, alt: alt || '' };
    }

    function render(i) {
        const data = getItemData(i);
        if (!data || !data.src) return;
        stageImg.src = data.src;
        stageImg.alt = data.alt || '';
    }

    function highlightThumb(i) {
    if (!thumbs.length) return;

    thumbs.forEach((btn, idx) => {
        const active = idx === i;
        btn.classList.toggle('is-active', active);
        btn.setAttribute('aria-selected', active ? 'true' : 'false');
        btn.setAttribute('tabindex', active ? '0' : '-1');
    });

    const thumbBtn = thumbs[i];
    if (!thumbBtn) return;
    const scrollTarget = thumbBtn.closest('li') || thumbBtn;
    centerThumb(scrollTarget, thumbsUl);
}


    function setActive(i, userInitiated = false) {
        if (!itemCount) return;
        index = mod(i, itemCount);

        render(index);
        highlightThumb(index);

        if (userInitiated) {
            stage.focus?.({ preventScroll: true });
        }
    }

    // ---------- nav helpers ----------
    const scrollOne = (dir) => {
        if (!thumbsUl) return;
        const amount = thumbsUl.clientWidth / 3 || 100;
        thumbsUl.scrollBy({ left: dir * amount, behavior: 'smooth' });
    };

    const goPrev = () => {
        setActive(index - 1, true);
        scrollOne(-1);
    };

    const goNext = () => {
        setActive(index + 1, true);
        scrollOne(1);
    };

    // ---------- hook up events ----------

    // Thumb clicks
    thumbs.forEach((thumb, i) => {
        thumb.addEventListener('click', () => setActive(i, true));
    });

    // Prev/Next buttons
    if (prevBtn) prevBtn.addEventListener('click', goPrev);
    if (nextBtn) nextBtn.addEventListener('click', goNext);

    // Thumb rail prev/next
    if (thumbsPrev) {
        thumbsPrev.addEventListener('click', () => {
            setActive(index - 1, true);
            scrollOne(-1);
        });
    }
    if (thumbsNext) {
        thumbsNext.addEventListener('click', () => {
            setActive(index + 1, true);
            scrollOne(1);
        });
    }

    // Keyboard nav on the whole about region
    container.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') {
            e.preventDefault();
            goNext();
        }
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            goPrev();
        }
    });

    // Touch swipe on the stage
    cleanupSwipe = swipeBinder(stage, (dir) => {
        if (dir === 'next') goNext();
        else goPrev();
    });

    // Keep active thumb centered on resize
    const onResize = () => {
        if (!thumbs.length) return;
        highlightThumb(index);
    };
    window.addEventListener('resize', onResize);

    // ---------- auto-rotation (your original showNext) ----------
    if (itemCount > 1) {
        const intervalMs = 4000;
        setInterval(() => {
            setActive(index + 1, false);
        }, intervalMs);
    }

    // ---------- initial render ----------
    setActive(0, false);

    // (optional) return tiny API
    return {
        next: goNext,
        prev: goPrev,
        go: (i) => setActive(i, true),
        destroy() {
            if (prevBtn) prevBtn.removeEventListener('click', goPrev);
            if (nextBtn) nextBtn.removeEventListener('click', goNext);
            window.removeEventListener('resize', onResize);
            if (cleanupSwipe) cleanupSwipe();
        }
    };
}

/* ----------------------------------------------------------
   AUTO-INITIALIZER (outside the function)
---------------------------------------------------------- */

function tryInitCarousel(root = document) {
    try {
        initAboutCarousel(root);
        if (window.hrSite && typeof window.hrSite.reflowParallax === 'function') {
            window.hrSite.reflowParallax();
        } else {
            alert('Failed to call reflow from carousel.');
        }
    } catch (err) {
        console.error('Carousel init error:', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    tryInitCarousel(document);
});

document.addEventListener('htmx:afterSwap', (e) => {
    if (
        e.target?.id === 'about-carousel-container' ||
        e.target?.closest?.('#about-carousel-container')
    ) {
        tryInitCarousel(e.target);
    }
});

