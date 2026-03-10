// hr_core/static_src/js/main.js

import feather from 'feather-icons';
import * as htmx from 'htmx.org';
import './modules/ui-global.js';
import './utils/globals.js';
import './utils/htmx-csrf.js';
import {renderIcons} from './utils/icons.js';
import {initVhFix} from './utils/vh-fix.js';


let nonCriticalBootPromise = null;
let coreInteractionModulesPromise = null;

window.htmx = htmx?.default ?? htmx;

function fireAndForget (makePromise, label = 'async task') {
    try {
        Promise.resolve(makePromise()).catch(err => console.error(`[main] ${label} failed`, err));
    } catch (err) {
        console.error(`[main] ${label} failed (sync)`, err);
    }
}

function deferUntilAfterFirstPaint (fn) {
    requestAnimationFrame(() => requestAnimationFrame(fn));
}

function removePrepaintAfterFirstFrame () {
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            document.documentElement.classList.remove('prepaint');
            document.dispatchEvent(new Event('hr:prepaintCleared'));
        });
    });
}

function ensureCoreInteractionModules () {
    if (!coreInteractionModulesPromise) {
        coreInteractionModulesPromise = Promise.all([
            import('./modules/events.js'),
            import('./meta-init.js')
        ]).catch((err) => {
            coreInteractionModulesPromise = null; // don't cache failed imports
            throw err;
        });
    }
    return coreInteractionModulesPromise;
}

function loadNonCriticalAssets () {
    if (!nonCriticalBootPromise) {
        nonCriticalBootPromise = Promise.all([
            ensureCoreInteractionModules(),
            import('./modules/account.js'),
            import('./modules/neon-sequencer.js'),
            import('./modules/scroll-effects.js')
        ]).catch((err) => {
            nonCriticalBootPromise = null; // allow retry
            throw err;
        });
    }
    return nonCriticalBootPromise;
}

/** @param {() => void} task */
function schedule (task) {
    if ('requestIdleCallback' in window) {
        window.requestIdleCallback(task, {timeout: 1200});
    } else {
        setTimeout(() => task(), 200);
    }
}

function scheduleNonCriticalBoot () {
    deferUntilAfterFirstPaint(() =>
        schedule(() => fireAndForget(() => loadNonCriticalAssets(), 'loadNonCriticalAssets'))
    );
}

async function bootstrapApp () {
    const params = new URLSearchParams(window.location.search);
    const isHandoff = params.has('handoff');
    const shouldRunIntro = document.documentElement.classList.contains('intro-pending');
    if (isHandoff) {
        const url = new URL(location.href);
        url.searchParams.delete('handoff');
        history.replaceState({}, '', url);
    }
    if (!shouldRunIntro) {
        await ensureCoreInteractionModules();
        scheduleNonCriticalBoot();
        removePrepaintAfterFirstFrame();
        return;
    }

    // Safety: if intro never signals done, don’t black-screen forever
    const failSafe = setTimeout(() => {
        document.documentElement.classList.remove('intro-pending');
        document.getElementById('intro-overlay')?.classList.add('complete');
        removePrepaintAfterFirstFrame();
    }, 6000);

    document.addEventListener('hr:introDone', () => {
        clearTimeout(failSafe);
        document.documentElement.classList.remove('intro-pending');

        // Now fade/transition to main page
        removePrepaintAfterFirstFrame();
    }, {once: true});

    await import('./modules/intro.js');
    scheduleNonCriticalBoot();

}

document.addEventListener('DOMContentLoaded', () => {
    renderIcons(document);
    feather.replace();
});

deferUntilAfterFirstPaint(initVhFix);
fireAndForget(async () => {
    try {
        await bootstrapApp();
    } catch (err) {
        removePrepaintAfterFirstFrame();
        throw err;
    }
}, 'bootstrapApp');
