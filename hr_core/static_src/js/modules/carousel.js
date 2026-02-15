// hr_core/static_src/js/modules/carousel.js

export function initCarousel (root = document) {
    const container = root.querySelector('#about-carousel');
    if (!container) return;

    // Idempotency — destroy any existing instance before re-initializing
    if (container._carouselInstance?.destroy) {
        container._carouselInstance.destroy();
    }

    // ─── DOM refs ────────────────────────────────────────────────────────────

    const mediaBase = (container.dataset.mediaBase || '/media/').replace(/\/+$/, '');
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

    // ─── State ───────────────────────────────────────────────────────────────

    const itemCount = thumbs.length;
    let index = 0;
    let cleanupSwipe = null;
    let intervalId = null;

    // ─── URL helpers ─────────────────────────────────────────────────────────

    const mod = (n, m) => ((n % m) + m) % m;

    function normalizeToAboutBase (url) {
        const u = String(url || '');
        if (!u) return '';

        const noQuery = u.split('?')[0];
        const noExt = noQuery.replace(/\.(webp|png|jpg|jpeg)$/i, '');
        const noSize = noExt.replace(/-\d+w$/i, '');
        const filename = noSize.split('/').pop() || '';
        if (!filename) return '';

        return `${mediaBase}/hr_about/opt_webp/${filename}`;
    }

    function aboutSrc (base, size) {
        return `${base}-${size}w.webp`;
    }

    function aboutSrcset (base) {
        return [
            `${aboutSrc(base, 640)}   640w`,
            `${aboutSrc(base, 960)}   960w`,
            `${aboutSrc(base, 1280)} 1280w`,
            `${aboutSrc(base, 1600)} 1600w`,
            `${aboutSrc(base, 1920)} 1920w`,
        ].join(', ');
    }

    // ─── Preloading ──────────────────────────────────────────────────────────

    function preloadCarouselImages () {
        const preloadContainer = document.createElement('div');
        preloadContainer.style.cssText =
            'position:absolute;width:0;height:0;overflow:hidden;opacity:0;pointer-events:none;';
        preloadContainer.setAttribute('aria-hidden', 'true');
        document.body.appendChild(preloadContainer);

        thumbs.forEach((thumb) => {
            const base = normalizeToAboutBase(thumb.dataset.src || '');
            if (!base) return;

            const img = document.createElement('img');
            img.srcset = aboutSrcset(base);
            img.sizes =
                '(max-width: 640px) 88vw, (max-width: 1024px) 92vw, (max-width: 1600px) 80vw, 1800px';
            img.loading = 'eager';
            img.alt = '';
            preloadContainer.appendChild(img);
        });
    }

    // ─── Rendering ───────────────────────────────────────────────────────────

    function getItemData (i) {
        const thumb = thumbs[i];
        if (!thumb) return null;
        const {src, alt} = thumb.dataset;
        return src ? {src, alt: alt || ''} : null;
    }

    function render (i) {
        const data = getItemData(i);
        if (!data) return;

        const base = normalizeToAboutBase(data.src);
        if (!base) return;

        stageImg.src = aboutSrc(base, 960);
        stageImg.srcset = aboutSrcset(base);
        stageImg.sizes =
            '(max-width: 640px) 88vw, (max-width: 1024px) 92vw, (max-width: 1600px) 80vw, 1800px';
        stageImg.alt = data.alt;
    }

    // ─── Thumb navigation ────────────────────────────────────────────────────

    function centerThumb (thumb, rail) {
        if (!thumb || !rail) return;
        const railRect = rail.getBoundingClientRect();
        const liRect = thumb.getBoundingClientRect();
        const target =
            rail.scrollLeft + (liRect.left - railRect.left) - (railRect.width / 2 - liRect.width / 2);
        rail.scrollTo({left: target, behavior: 'smooth'});
    }

    function highlightThumb (i) {
        const prevIndex = mod(i - 1, itemCount);
        const nextIndex = mod(i + 1, itemCount);

        thumbs.forEach((btn, idx) => {
            const isActive = idx === i;
            btn.classList.toggle('is-active', isActive);
            btn.setAttribute('aria-selected', String(isActive));
            btn.setAttribute('tabindex', isActive ? '0' : '-1');
        });

        if (thumbLis.length === thumbs.length) {
            thumbLis.forEach((li, idx) => {
                li.classList.toggle('is-visible', idx === i || idx === prevIndex || idx === nextIndex);
            });
        } else {
            const scrollTarget = thumbs[i].closest('li') || thumbs[i];
            centerThumb(scrollTarget, thumbsUl);
        }
    }

    // ─── Active slide management ─────────────────────────────────────────────

    function setActive (i, userInitiated = false) {
        if (!itemCount) return;
        index = mod(i, itemCount);
        render(index);
        highlightThumb(index);
        if (userInitiated) stage.focus?.({preventScroll: true});
    }

    const scrollOne = (dir) => {
        if (!thumbsUl) return;
        thumbsUl.scrollBy({left: dir * (thumbsUl.clientWidth / 3 || 100), behavior: 'smooth'});
    };

    const goPrev = () => {
        setActive(index - 1, true);
        scrollOne(-1);
    };
    const goNext = () => {
        setActive(index + 1, true);
        scrollOne(1);
    };

    // ─── Touch swipe ─────────────────────────────────────────────────────────

    function swipeBinder (el, onSwipe) {
        let x0 = null;
        let t0 = 0;

        const onTouchStart = (e) => {
            if (!e.touches?.length) return;
            x0 = e.touches[0].clientX;
            t0 = Date.now();
        };

        const onTouchEnd = (e) => {
            if (x0 == null || !e.changedTouches?.length) return;
            const dx = e.changedTouches[0].clientX - x0;
            const dt = Date.now() - t0;
            x0 = null;
            if (Math.abs(dx) > 40 && dt < 600) onSwipe(dx < 0 ? 'next' : 'prev');
        };

        el.addEventListener('touchstart', onTouchStart, {passive: true});
        el.addEventListener('touchend', onTouchEnd);
        return () => {
            el.removeEventListener('touchstart', onTouchStart);
            el.removeEventListener('touchend', onTouchEnd);
        };
    }

    // ─── ARIA setup ──────────────────────────────────────────────────────────

    if (thumbsUl) thumbsUl.setAttribute('role', 'tablist');
    stage.setAttribute('role', 'group');

    // <li> elements must be removed from the tab role hierarchy
    thumbLis.forEach((li) => li.setAttribute('role', 'presentation'));

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

    // ─── Event listeners ─────────────────────────────────────────────────────

    thumbs.forEach((thumb, i) => thumb.addEventListener('click', () => setActive(i, true)));

    if (prevBtn) prevBtn.addEventListener('click', goPrev);
    if (nextBtn) nextBtn.addEventListener('click', goNext);
    if (thumbsPrev)
        thumbsPrev.addEventListener('click', () => {
            setActive(index - 1, true);
            scrollOne(-1);
        });
    if (thumbsNext)
        thumbsNext.addEventListener('click', () => {
            setActive(index + 1, true);
            scrollOne(1);
        });

    const onKeydown = (e) => {
        if (e.key === 'ArrowRight') {
            e.preventDefault();
            goNext();
        }
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            goPrev();
        }
    };
    container.addEventListener('keydown', onKeydown);

    cleanupSwipe = swipeBinder(stage, (dir) => (dir === 'next' ? goNext() : goPrev()));

    const onResize = () => highlightThumb(index);
    window.addEventListener('resize', onResize);

    // ─── Auto-rotation ───────────────────────────────────────────────────────

    if (itemCount > 1) {
        intervalId = window.setInterval(() => setActive(index + 1, false), 4000);
    }

    // ─── Init ────────────────────────────────────────────────────────────────

    preloadCarouselImages();
    setActive(0, false);

    // ─── Instance ────────────────────────────────────────────────────────────

    const instance = {
        next: goNext,
        prev: goPrev,
        go: (i) => setActive(i, true),
        destroy () {
            if (prevBtn) prevBtn.removeEventListener('click', goPrev);
            if (nextBtn) nextBtn.removeEventListener('click', goNext);
            container.removeEventListener('keydown', onKeydown);
            window.removeEventListener('resize', onResize);
            if (cleanupSwipe) cleanupSwipe();
            if (intervalId) window.clearInterval(intervalId);
        },
    };

    container._carouselInstance = instance;
    return instance;
}
