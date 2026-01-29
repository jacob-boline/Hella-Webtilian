// hr_core/static_src/js/utils/htmx-csrf.js

export function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    const fromMeta = meta && meta.getAttribute('content');
    if (fromMeta && fromMeta !== 'NOTPROVIDED') return fromMeta;

    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input && input.value) return input.value;

    const m = document.cookie.match(/(^| )csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[2]) : '';
}

(function () {
    document.body.addEventListener('htmx:configRequest', function (event) {
        const csrfToken = getCsrfToken();
        if (csrfToken) {
            event.detail.headers['X-CSRFToken'] = csrfToken;
        }
    });
})();
