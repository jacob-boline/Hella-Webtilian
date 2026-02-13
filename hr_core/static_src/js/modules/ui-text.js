// hr_core/static_src/js/modules/ui-text.js


// -----------------------------
// Defaults
// -----------------------------
const DEFAULTS = {
    force: false,
    allowMarkup: false,
    wrappedAttr: "data-hr-wrapped",
    preserveOriginal: true,
    useNbspForSpaces: true,
};

// -----------------------------
// Helpers
// -----------------------------
function resolveRoot (root) {
    return root && root.querySelectorAll ? root : document;
}

function hasElementChildren (el) {
    for (let i = 0; i < el.childNodes.length; i++) {
        if (el.childNodes[i].nodeType === Node.ELEMENT_NODE) return true;
    }
    return false;
}

function getRawText (el, opts) {
    if (opts.preserveOriginal && el.dataset && el.dataset.hrOriginalText != null) {
        return el.dataset.hrOriginalText;
    }
    return (el.textContent || "").trim();
}

function preserveOriginal (el, text, opts) {
    if (!opts.preserveOriginal) return;
    if (!el.dataset) return;
    if (el.dataset.hrOriginalText == null) el.dataset.hrOriginalText = text;
}

function getWrappedKeys (el, opts) {
    const attr = opts.wrappedAttr || DEFAULTS.wrappedAttr;
    return (el.getAttribute(attr) || "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
}

function markWrapped (el, key, opts) {
    const attr = opts.wrappedAttr || DEFAULTS.wrappedAttr;
    const current = getWrappedKeys(el, opts);

    if (!current.includes(key)) current.push(key);
    el.setAttribute(attr, current.join(","));
}

function isWrapped (el, key, opts) {
    return getWrappedKeys(el, opts).includes(key);
}

function toSpanText (ch, opts) {
    if (ch === " " && opts.useNbspForSpaces) return "\u00A0";
    return ch;
}

function mergeOpts (options) {
    return Object.assign({}, DEFAULTS, options || {});
}

// -----------------------------
// Public API
// -----------------------------
export function wrapChars (root, selector, className, options = {}) {
    const opts = mergeOpts(options);
    const r = resolveRoot(root);
    if (!selector || !className) return;

    r.querySelectorAll(selector).forEach((el) => {
        if (!el) return;

        const key = String(className);

        if (!opts.force && isWrapped(el, key, opts)) return;
        if (!opts.allowMarkup && hasElementChildren(el)) return;

        const text = getRawText(el, opts);
        if (!text) return;

        preserveOriginal(el, text, opts);

        el.replaceChildren();
        for (const ch of text) {
            const span = document.createElement("span");
            span.className = className;
            span.textContent = toSpanText(ch, opts);
            el.appendChild(span);
        }

        markWrapped(el, key, opts);
    });
}

export function applyStitchedLetters (root, selector, options = {}) {
    const opts = mergeOpts(options);
    const r = resolveRoot(root);
    if (!selector) return;

    r.querySelectorAll(selector).forEach((el) => {
        if (!el) return;

        const key = "letters";

        if (!opts.force && isWrapped(el, key, opts)) return;
        if (!opts.allowMarkup && hasElementChildren(el)) return;

        const text = getRawText(el, opts);
        if (!text) return;

        preserveOriginal(el, text, opts);

        el.replaceChildren();
        for (const ch of text) {
            const span = document.createElement("span");
            span.className = "letter";
            span.textContent = toSpanText(ch, opts);
            el.appendChild(span);
        }

        markWrapped(el, key, opts);
    });
}

export function wrapDateTimeChars (root, options = {}) {
    const opts = mergeOpts(options);
    const r = resolveRoot(root);

    r.querySelectorAll(".date, .time").forEach((el) => {
        if (!el) return;

        const key = el.classList.contains("date")
            ? "datetime-date"
            : "datetime-time";

        if (!opts.force && isWrapped(el, key, opts)) return;
        if (!opts.allowMarkup && hasElementChildren(el)) return;

        const text = getRawText(el, opts);
        if (!text) return;

        preserveOriginal(el, text, opts);

        const spanClass = el.classList.contains("date") ? "date-char" : "time-char";

        el.replaceChildren();
        for (const ch of text) {
            const span = document.createElement("span");
            span.className = spanClass;
            span.textContent = toSpanText(ch, opts);
            el.appendChild(span);
        }

        markWrapped(el, key, opts);
    });
}

export function initUIText (root) {
    wrapDateTimeChars(root);
}
