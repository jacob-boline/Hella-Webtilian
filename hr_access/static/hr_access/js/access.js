// hr_access/static/hr_access/js/access.js

document.addEventListener('passwordChanged', (e) => {
    const detail = e.detail || {};
    const msg = detail.message || detail.text || 'Password updated.';
    hrSite.hideModal();
    hrSite.showGlobalMessage(msg, 5000);
});

// replace usages of above with below

document.addEventListener('closeModalShowGlobalMessage', (e) => {
    const detail = e.detail || {};
    const msg = detail.message || detail.text || 'Success;';
    const duration = detail.duration || 5000;

    if (typeof hrSite?.hideModal === 'function') {
        hrSite.hideModal();
    }

    if (typeof hrSite?.showGlobalMessage === 'function') {
        hrSite.showGlobalMessage(msg, duration);
    }
});

