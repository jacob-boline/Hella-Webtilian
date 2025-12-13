document.addEventListener('click', function (e) {
    const toggle = e.target.closest('.bulletin-toggle');
    if (!toggle) return;

    const post = toggle.closest('.bulletin-post.is-collapsible');
    if (!post) return;

    const expanded = post.classList.toggle('is-expanded');
    post.classList.toggle('is-collapsed', !expanded);

    const label = toggle.querySelector('.bulletin-toggle-label');
    if (!label) return;

    // Swap label text
    const arrow = label.querySelector('.bulletin-arrow');
    if (expanded) {
        label.firstChild && (label.firstChild.textContent = 'Hide');
        toggle.setAttribute('aria-expanded', 'true');
        hrSite.reflowParallax();
    } else {
        label.firstChild && (label.firstChild.textContent = 'Read more');
        toggle.setAttribute('aria-expanded', 'false');
        hrSite.reflowParallax();
    }
});

