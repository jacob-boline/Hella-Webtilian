// hr_core/static_src/js/modules/neon-sequencer.js
(function () {
    const BASE_SEQUENCES = [
        'neon-sequence-a', 'neon-sequence-c', 'neon-sequence-d',
        'neon-sequence-e', 'neon-sequence-f', 'neon-sequence-j'
    ];
    // ,'neon-sequence-g','neon-sequence-l''neon-sequence-i','neon-sequence-b','neon-sequence-h',

    const DEBUG_NEON = false;

    const RARE_SUPERNOVA = 'neon-sequence-k';
    const SUPERNOVA_CHANCE = 0.10;

    // -------------------------
    // Debug label creation
    // -------------------------
    function ensureLabel (el) {
        if (DEBUG_NEON) {
            if (!el._neonLabel) {
                const label = document.createElement('span');
                label.className = 'neon-debug-label';
                el.appendChild(label);
                el._neonLabel = label;
            }
            return el._neonLabel;
        }
        return null
    }

    function updateLabel (el, seq) {
        if (DEBUG_NEON) {
            const lbl = ensureLabel(el);
            lbl.textContent = seq;
            lbl.style.opacity = 1;
        }
    }

    function hideLabel (el) {
        if (DEBUG_NEON) {
            if (el._neonLabel) {
                el._neonLabel.style.opacity = 0;
            }
        }
    }

    // -------------------------
    // Sequence selection
    // -------------------------
    function pickRandomSequence (exclude) {
        if (Math.random() < SUPERNOVA_CHANCE && RARE_SUPERNOVA !== exclude) {
            return RARE_SUPERNOVA;
        }
        const pool = BASE_SEQUENCES.filter(name => name !== exclude);
        return pool[Math.floor(Math.random() * pool.length)];
    }

    function applyRandomNeon (el) {
        const current = el.dataset.neonSeq || null;
        const next = pickRandomSequence(current);
        el.dataset.neonSeq = next;
        el.style.animationName = next;
        updateLabel(el, next);
    }

    function resetNeon (el) {
        el.dataset.neonSeq = '';
        el.style.animationName = 'none';
        el.style.animationPlayState = 'paused';
        hideLabel(el);
    }

    // -------------------------
    // Init per element
    // -------------------------
    function initNeonAct (el) {
        if (el._neonInitialized) return;
        el._neonInitialized = true;

        // Initial clean state
        resetNeon(el);

        el.classList.add('neon-ready');
        ensureLabel(el);

        el.addEventListener('mouseenter', () => {
            applyRandomNeon(el);
            el.style.animationPlayState = 'running';
        });

        el.addEventListener('animationiteration', () => {
            if (el.matches(':hover')) applyRandomNeon(el);
        });

        el.addEventListener('mouseleave', () => {
            resetNeon(el);
        });
    }

    function initAllNeonActs (root = document) {
        if (document.documentElement.classList.contains("prepaint")) return;
        root.querySelectorAll('.act-name').forEach(initNeonAct);
    }

    document.addEventListener("hr:prepaintCleared", () => initAllNeonActs());
    document.addEventListener('htmx:afterSwap', (evt) => initAllNeonActs(evt.target));
})();
