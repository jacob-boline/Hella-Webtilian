// hr_core/static/hr_core/js/htmx-csrf.js

(function () {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    document.body.addEventListener('htmx:configRequest', function (event) {
        const csrfToken = getCookie('csrftoken');
        if (csrfToken) {
            event.detail.headers['X-CSRFToken'] = csrfToken;
        }
    });
})();
