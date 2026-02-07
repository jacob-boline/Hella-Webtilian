// hr_core/static_src/js/modules/bulletin.js

export function initBulletin () {
    if (document.body._bulletinInitDone) return;
    document.body._bulletinInitDone = true;

    // Handle "Read more" toggle for long posts
    document.addEventListener('click', function (e) {
        const toggle = e.target.closest('.bulletin-toggle');
        if (!toggle) return;

        const post = toggle.closest('.bulletin-post.is-collapsible');
        if (!post) return;

        const expanded = post.classList.toggle('is-expanded');
        post.classList.toggle('is-collapsed', !expanded);

        const label = toggle.querySelector('.bulletin-toggle-label');
        if (!label) return;

        if (expanded) {
            label.firstChild && (label.firstChild.textContent = 'Hide');
            toggle.setAttribute('aria-expanded', 'true');
        } else {
            label.firstChild && (label.firstChild.textContent = 'Read more');
            toggle.setAttribute('aria-expanded', 'false');
        }
        requestAnimationFrame(() => window.hrSite?.reflowParallax?.());
    });

    // Handle tag ellipsis expansion
    document.addEventListener('click', function (e) {
        const tagsContainer = e.target.closest('.bulletin-tags.has-overflow');
        if (!tagsContainer) return;

        // Only toggle if clicking on the ellipsis area (::after pseudo-element)
        const rect = tagsContainer.getBoundingClientRect();
        const clickX = e.clientX - rect.left;

        // Check if click is in the right area where ellipsis would be
        if (clickX > rect.width - 60) {
            tagsContainer.classList.toggle('expanded');
            e.preventDefault();
            e.stopPropagation();
        }
    });

    // Initialize tag overflow detection
    function checkTagOverflow() {
        document.querySelectorAll('.bulletin-tags').forEach(tagsContainer => {
            // Skip if already processed
            if (tagsContainer.dataset.overflowChecked === 'true') return;

            const tags = tagsContainer.querySelectorAll('.bulletin-tag');
            if (tags.length === 0) return;

            // Temporarily remove flex-wrap to check natural width
            tagsContainer.style.flexWrap = 'nowrap';
            const scrollWidth = tagsContainer.scrollWidth;
            const clientWidth = tagsContainer.clientWidth;
            tagsContainer.style.flexWrap = '';

            // If content overflows, add the overflow class
            if (scrollWidth > clientWidth) {
                tagsContainer.classList.add('has-overflow');
            }

            tagsContainer.dataset.overflowChecked = 'true';
        });
    }

    // Run on load and after new content is added
    checkTagOverflow();

    document.body.addEventListener("htmx:afterSwap", (e) => {
        // Reset overflow check flags for new content
        const target = e.detail?.target;
        if (target) {
            target.querySelectorAll('.bulletin-tags').forEach(el => {
                el.dataset.overflowChecked = 'false';
            });
            checkTagOverflow();
        }
    });

    document.body.addEventListener("htmx:afterSwap", (e) => {
        const target = e.detail?.target || e.target;
        if (!target) return;

        // If anything swapped into the feed, kill the loading message
        if (target.id === "bulletin-feed") {
            const root = document.getElementById("bulletin-root");
            const loading = root?.querySelector(".bulletin-loading");
            if (loading) loading.remove();

            requestAnimationFrame(() => {
                requestAnimationFrame(() => window.hrSite?.reflowParallax?.());
            });
        }
    });

    document.body.addEventListener("htmx:afterSwap", (e) => {
        const target = e.detail?.target;
        if (!target || target.id !== "bulletin-feed") return;

        requestAnimationFrame(() => window.hrSite?.reflowParallax?.());
    });

}

