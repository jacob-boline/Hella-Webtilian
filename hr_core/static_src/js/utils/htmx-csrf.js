// hr_core/static_src/js/utils/htmx-csrf.js

export function getCsrfTokenFromCookie() {
    const m = document.cookie.match(/(^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[2]) : '';
}

(function () {
    document.body.addEventListener('htmx:configRequest', function (event) {
        const token = getCsrfTokenFromCookie();
        if (token) {
            event.detail.headers['X-CSRFToken'] = token;
        }
    });
})();
