// hr_core/static_src/js/modules/carousel.js

export function initCarousel(root = document) {
    const container = root.querySelector('#about-carousel');
    if (!container) return;

    // If already initialized, destroy and re-init (idempotent)
    if (container._carouselInstance?.destroy) {
        container._carouselInstance.destroy();
    }

    const stage = container.querySelector('.about-stage') || container;
    const stageImg = container.querySelector('.about-stage-img');

    const thumbsUl = container.querySelector('.about-thumbs');
    const thumbs = thumbsUl ? Array.from(thumbsUl.querySelectorAll('button.about-thumb')) : [];
    const thumbLis = thumbsUl ? Array.from(thumbsUl.querySelectorAll('li')) : [];

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

    // Touch swipe binder with cleanup
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
    let intervalId = null;

    // ----------------- ARIA setup ------------------
    if (thumbsUl) thumbsUl.setAttribute('role', 'tablist');
    stage.setAttribute('role', 'group');

    thumbs.forEach((btn, i) => {
        btn.setAttribute('role', 'tab');
        btn.setAttribute('aria-selected', 'false');
        btn.setAttribute('tabindex', '-1');

        btn.addEventListener('keydown', (e) => {
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

    // --------------- THUMB VISIBILITY + HIGHLIGHT ---------------
    function highlightThumb(i) {
        const count = thumbs.length;
        const prevIndex = mod(i - 1, count);
        const nextIndex = mod(i + 1, count);

        thumbs.forEach((btn, idx) => {
            const isActive = idx === i;
            btn.classList.toggle('is-active', isActive);
            btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
            btn.setAttribute('tabindex', isActive ? '0' : '-1');
        });

        if (thumbLis.length === thumbs.length) {
            thumbLis.forEach((li, idx) => {
                const visible = idx === i || idx === prevIndex || idx === nextIndex;
                li.classList.toggle('is-visible', visible);
            });
        } else {
            const thumbBtn = thumbs[i];
            const scrollTarget = thumbBtn.closest('li') || thumbBtn;
            centerThumb(scrollTarget, thumbsUl);
        }
    }

    function setActive(i, userInitiated = false) {
        if (!itemCount) return;
        index = mod(i, itemCount);

        render(index);
        highlightThumb(index);

        if (userInitiated) stage.focus?.({ preventScroll: true });
    }

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
    thumbs.forEach((thumb, i) => {
        thumb.addEventListener('click', () => setActive(i, true));
    });

    if (prevBtn) prevBtn.addEventListener('click', goPrev);
    if (nextBtn) nextBtn.addEventListener('click', goNext);

    if (thumbsPrev) thumbsPrev.addEventListener('click', () => { setActive(index - 1, true); scrollOne(-1); });
    if (thumbsNext) thumbsNext.addEventListener('click', () => { setActive(index + 1, true); scrollOne(1); });

    const onKeydown = (e) => {
        if (e.key === 'ArrowRight') { e.preventDefault(); goNext(); }
        if (e.key === 'ArrowLeft') { e.preventDefault(); goPrev(); }
    };
    container.addEventListener('keydown', onKeydown);

    cleanupSwipe = swipeBinder(stage, (dir) => {
        if (dir === 'next') goNext();
        else goPrev();
    });

    const onResize = () => highlightThumb(index);
    window.addEventListener('resize', onResize);

    // ---------- auto-rotation (cleanable) ----------
    if (itemCount > 1) {
        const intervalMs = 4000;
        intervalId = window.setInterval(() => {
            setActive(index + 1, false);
        }, intervalMs);
    }

    // ---------- initial render ----------
    setActive(0, false);

    const instance = {
        next: goNext,
        prev: goPrev,
        go: (i) => setActive(i, true),
        destroy() {
            if (prevBtn) prevBtn.removeEventListener('click', goPrev);
            if (nextBtn) nextBtn.removeEventListener('click', goNext);
            container.removeEventListener('keydown', onKeydown);
            window.removeEventListener('resize', onResize);

            if (cleanupSwipe) cleanupSwipe();
            if (intervalId) window.clearInterval(intervalId);
        }
    };

    container._carouselInstance = instance;
    return instance;
}
