// hr_core/static_src/js/main.js

import feather from "feather-icons";
import * as htmx from "htmx.org";
import "../css/critical.css";
import './modules/intro.js';
import './modules/ui-global.js';

import './utils/core-utils.js';
import './utils/globals.js';
import './utils/htmx-csrf.js';
import {initVhFix} from './utils/vh-fix.js';

window.htmx = htmx?.default ?? htmx;

function removePrepaintAfterFirstFrame () {
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            document.documentElement.classList.remove("prepaint");
            document.dispatchEvent(new Event("hr:prepaintCleared"));
        });
    });
}

removePrepaintAfterFirstFrame();

function deferUntilAfterFirstPaint (fn) {
    requestAnimationFrame(() => requestAnimationFrame(fn));
}

deferUntilAfterFirstPaint(initVhFix);

window.addEventListener("DOMContentLoaded", () => feather.replace());

let nonCriticalBooted = false;

async function loadNonCriticalAssets () {
    if (nonCriticalBooted) return;
    nonCriticalBooted = true;

    await Promise.all([
        import('../css/noncritical.css'),
        import('./meta-init.js'),
        import('./modules/account.js'),
        import('./modules/banner.js'),
        import('./modules/events.js'),
        import('./modules/neon-sequencer.js'),
        import('./modules/scroll-effects.js'),
    ]);
}

function scheduleNonCriticalBoot () {
    const start = () => {
        if ('requestIdleCallback' in window) {
            window.requestIdleCallback(() => {
                loadNonCriticalAssets();
            }, {timeout: 1200});
            return;
        }

        setTimeout(() => {
            loadNonCriticalAssets();
        }, 200);
    };

    requestAnimationFrame(() => requestAnimationFrame(start));
}

scheduleNonCriticalBoot();
