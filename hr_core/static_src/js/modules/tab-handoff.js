// hr_core/static/hr_core/js/modules/tab-handoff.js

const CHANNEL_NAME = 'hr_site_handoff_v1';
const bc = ('BroadcastChannel' in window) ? new BroadcastChannel(CHANNEL_NAME) : null;

function parseHandoffParams () {
    const params = new URLSearchParams(window.location.search);
    const handoff = params.get('handoff'); // e.g. "email_confirmed"
    if (!handoff) return null;

    return {
        type: handoff,
        hash: window.location.hash || '',
        modal: params.get('modal') || '',
        modalUrl: params.get('modal_url') || ''
    };
}

function cleanUrlKeepHash () {
    const clean = window.location.pathname + window.location.hash;
    window.history.replaceState({}, '', clean);
}

export function initTabHandoff (root = document) {
    // only on full page load
    if (root !== document) return;
    if (!bc) return;

    // Listener: if we're the "existing tab", respond + act
    bc.onmessage = (ev) => {
        const msg = ev.data || {};

        if (msg.kind === 'ping') {
            bc.postMessage({kind: 'pong', ts: Date.now()});
            return;
        }

        if (msg.kind === 'handoff' && msg.payload) {
            if (msg.payload.hash) {
                const el = document.querySelector(msg.payload.hash);
                if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
            }

            if (msg.payload.modal === 'email_confirmed') {
                const loader = document.getElementById('modal-loader');
                if (!loader || !window.htmx) {
                    console.warn('[tab-handoff] modal-loader or htmx missing in receiving tab');
                    return;
                }

                loader.setAttribute('hx-get', msg.payload.url);
                htmx.process(loader);
                htmx.trigger(loader, 'hr:loadModal');
            }
        }

    };

    // Sender: if this tab was opened from an email link with ?handoff=...
    const payload = parseHandoffParams();
    if (!payload) return;

    // ping existing tabs; if one answers, hand off and close
    let gotPong = false;

    const pingId = crypto?.randomUUID?.() || String(Date.now());
    bc.postMessage({kind: 'ping', pingId});

    const timer = setTimeout(() => {
        // nobody answered, stay in this tab
        if (!gotPong) cleanUrlKeepHash();
    }, 250);

    const onMessage = (ev) => {
        const msg = ev.data || {};
        if (msg.kind === 'pong') {
            gotPong = true;
            clearTimeout(timer);

            // send actual handoff instruction
            bc.postMessage({
                kind: 'handoff',
                payload: {
                    modal: payload.modal,
                    hash: payload.hash,
                    url: payload.modalUrl
                }
            });

            // Stop listening; we only need one pong
            bc.removeEventListener('message', onMessage);

            // try to close this tab
            window.close();
        }
    };

    bc.addEventListener('message', onMessage);
}
