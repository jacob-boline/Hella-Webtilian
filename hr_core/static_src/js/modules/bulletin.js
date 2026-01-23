// hr_core/static_src/js/modules/bulletin.js

export function initBulletin () {
    if (document.body._bulletinInitDone) return;
    document.body._bulletinInitDone = true;

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

    // // ---- Infinite scroll sentinel paging ----
    // document.body.addEventListener("htmx:afterRequest", (e) => {
    //     const elt = e.detail?.elt;
    //     if (!elt || elt.id !== "bulletin-sentinel") return;
    //
    //     const xhr = e.detail?.xhr;
    //     if (!xhr) return;
    //
    //     const nextPage = xhr.getResponseHeader("X-Next-Page");
    //     if (!nextPage) {
    //         elt.remove();
    //         return;
    //     }
    //
    //     const hxGet = elt.getAttribute("hx-get") || "";
    //     const baseUrl = hxGet.split("?")[0];
    //     elt.setAttribute("hx-get", `${baseUrl}?page=${encodeURIComponent(nextPage)}`);
    //
    //     // const fresh = elt.cloneNode(true);
    //     elt.replaceWith(fresh);
    //
    //     // Re-process so HTMX sees the updated attributes
    //     window.htmx?.process?.(fresh);
    //
    //     // 'revealed' fires on becoming visible; after append it might already be visible.
    //     // Nudge another revealed check.
    //     // requestAnimationFrame(() => {
    //     //     window.htmx?.trigger?.(elt, "revealed");
    //     // });
    // });

    document.body.addEventListener("htmx:afterSwap", (e) => {
        const target = e.detail?.target || e.target;
        if (!target) return;

        // If anything swapped into the feed, kill the loading message
        if (target.id === "bulletin-feed") {
            const root = document.getElementById("bulletin-root");
            const loading = root?.querySelector(".bulletin-loading");
            if (loading) loading.remove();

            // optional: reflow after DOM insertion
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


    //
    // document.body.addEventListener("htmx:afterSwap", (e) => {
    //     const target = e.detail?.target || e.target;
    //     if (!target) return;
    //
    //     // We only care about infinite-scroll appends into the feed
    //     if (target.id !== "bulletin-feed") return;
    //
    //     requestAnimationFrame(() => {
    //         requestAnimationFrame(() => window.hrSite?.reflowParallax?.());
    //     });
    // });

}
