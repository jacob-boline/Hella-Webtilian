document.body.addEventListener('htmx:afterSwap', (e) => {
    if (e.detail.target.id === 'modal') {
        document.getElementById('modal').classList.remove('hidden');
        document.getElementById('modal').focus();
    }
});
document.addEventListener('click', (e) => {
    if (e.target.matches('[data-close-modal], #modal .backdrop')) {
        document.getElementById('modal').classList.add('hidden');
        document.getElementById('modal').innerHTML = '';
    }
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelector('#modal')?.classList.add('hidden');
        document.getElementById('modal').innerHTML = '';
    }
});
