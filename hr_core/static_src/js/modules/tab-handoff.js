// hr_core/static_src/js/modules/tab-handoff.js

const CHANNEL_NAME = 'hr_site_handoff_v1';
const bc = ('BroadcastChannel' in window) ? new BroadcastChannel(CHANNEL_NAME) : null;

/**
 * Consistent “wait until HTMX is available” hook.
 * Safe even if this module is evaluated before HTMX is loaded.
 */
function whenHtmxReady (cb) {
    if (typeof cb !== 'function') return;

    // Fast path: already present
    if (window.htmx) {
        Promise.resolve().then(cb);
        return;
    }

    // Prefer the htmx:load event if it fires later
    const onLoad = () => {
        window.removeEventListener('htmx:load', onLoad);
        Promise.resolve().then(cb);
    };
    window.addEventListener('htmx:load', onLoad, {once: true});

    // Fallback: poll briefly (covers cases where htmx:load never fires on first paint)
    let tries = 0;
    const t = setInterval(() => {
        tries += 1;
        if (window.htmx) {
            clearInterval(t);
            window.removeEventListener('htmx:load', onLoad);
            Promise.resolve().then(cb);
        } else if (tries >= 80) { // ~2s
            clearInterval(t);
            window.removeEventListener('htmx:load', onLoad);
            // console.warn('[tab-handoff] htmx never became ready');
        }
    }, 25);
}

function parseHandoffParams () {
    const params = new URLSearchParams(window.location.search);
    const handoff = params.get('handoff'); // e.g. "email_confirmed"
    if (!handoff) return null;

    return {
        type: handoff,
        hash: window.location.hash || '',
        modal: params.get('modal') || '',
        modalUrl: decodeURIComponent(params.get('modal_url') || '')
    };
}

function tryOpenModal (payload, attempts = 30) {
    const loader = document.getElementById('modal-loader');
    const h = window.htmx;

    if (loader && h && payload?.modalUrl) {
        const url = payload.modalUrl;
        window.htmx.trigger(document.body, 'loadModal', {url});
        return true;
    }

    if (attempts <= 0) {
        return false;
    }

    setTimeout(() => tryOpenModal(payload, attempts - 1), 50);
    return false;
}


// function cleanUrlKeepHash () {
//     console.warn('[tab-handoff] CLEANING URL', window.location.href);
//     console.trace();
//
//     const clean = window.location.pathname + window.location.hash;
//     window.history.replaceState({}, '', clean);
// }

export function initTabHandoff (root = document) {
    console.log('[tab-handoff] init', {
        href: window.location.href,
        search: window.location.search,
        hash: window.location.hash
    });

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

            if (msg.payload.modal && msg.payload.url) {
                // Ensure HTMX/DOM are ready-ish before trying
                whenHtmxReady(() => {
                    tryOpenModal({modalUrl: msg.payload.url});
                });
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
        // nobody answered, stay in this tab and load modal here if available
        if (!gotPong) {
            whenHtmxReady(() => {
                // Prefer using the same modal mechanism as the rest of the app
                // (loader + hr:loadModal). Fall back to htmx.ajax into #modal-root.
                if (payload.modalUrl) {
                    const opened = tryOpenModal(payload);
                    if (!opened && window.htmx) {
                        window.htmx.ajax('GET', payload.modalUrl, {
                            target: '#modal-root',
                            swap: 'innerHTML'
                        });
                    }
                }
            });
        }
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
