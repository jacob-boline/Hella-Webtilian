// hr_core/static_src/js/main.js

import feather from "feather-icons";
import * as htmx from "htmx.org";
import "../css/main.css";

import "./meta-init.js";
import './modules/account.js'
import './modules/banner.js'
import './modules/events.js'
import './modules/neon-sequencer.js'
import './modules/scroll-effects.js'

import './modules/ui-global.js'

import './utils/core-utils.js';

import './utils/globals.js';
import './utils/htmx-csrf.js';
import './utils/vh-fix.js';

window.htmx = htmx?.default ?? htmx;
window.addEventListener("DOMContentLoaded", () => feather.replace());


