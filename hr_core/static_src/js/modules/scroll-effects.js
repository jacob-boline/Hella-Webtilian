// hr_site/static/hr_site/js/scroll-effects.js

import { wrapDateTimeChars, applyStitchedLetters } from "./ui-text.js";

(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const config = (window.hrSite && window.hrSite.config) || {};
    const utils = (window.hrSite && window.hrSite.utils) || {};
    const bannerAPI = (window.hrSite && window.hrSite.banner) || {};

    const defaultGetVH = () =>
      window.visualViewport?.height ||
      window.innerHeight ||
      document.documentElement.clientHeight;

    const getVH = utils.getVH || defaultGetVH;
    const debounce =
      utils.debounce ||
      function (fn, wait = 200) {
        let t;
        return function (...args) {
          clearTimeout(t);
          t = setTimeout(() => fn.apply(this, args), wait);
        };
      };

    const PARALLAX_SCROLL_RATIO = config.PARALLAX_SCROLL_RATIO ?? 0.5;
    const REDUCED_MOTION = !!config.REDUCED_MOTION;

    const parallaxSpeed = REDUCED_MOTION ? 0 : PARALLAX_SCROLL_RATIO;

    const wipes = document.querySelectorAll(".section-wipe");
    const parallaxSections = document.querySelectorAll(".parallax-section");

    const STATE = {
      wipeData: new Map(),
      activeWipe: null,
      rafId: null,
      rafLayout: null,
      observers: {
        wipe: null,
        section: null,
      },
    };

    function initializeParallax() {
      const viewportHeight = getVH();
      parallaxSections.forEach((section) => {
        const content = section.querySelector(".parallax-content");
        const background = section.querySelector(".parallax-background");
        if (!content || !background) return;

        const adjusted = Math.max(content.getBoundingClientRect().height, viewportHeight);
        section.style.height = `${adjusted}px`;
        background.style.height = `${adjusted}px`;
      });
    }

    function positionSectionWipes() {
      wipes.forEach((wipe) => {
        const next = wipe.nextElementSibling;
        if (next && next.classList.contains("parallax-section")) {
          const top = next.getBoundingClientRect().top + window.scrollY;
          wipe.style.top = `${top}px`;
        }
        delete wipe.dataset.baseHeight;
      });
    }

    function calculateWipeData() {
      const viewportHeight = getVH();
      STATE.wipeData.clear();

      wipes.forEach((wipe) => {
        const rect = wipe.getBoundingClientRect();
        const wipeHeight = rect.height;
        const scrollSpeedRatio = (viewportHeight + wipeHeight) / viewportHeight;
        const wipeOffset = rect.top + window.scrollY + 50;
        STATE.wipeData.set(wipe, { scrollSpeedRatio, wipeOffset });
      });
    }

    function updateParallax(scrollTop) {
      if (parallaxSpeed === 0) return;
      document.querySelectorAll(".parallax-section.in-view").forEach((section) => {
        const sectionOffset = section.getBoundingClientRect().top + scrollTop;
        const background = section.querySelector(".parallax-background");
        if (!background) return;
        background.style.transform = `translate3d(0, ${(scrollTop - sectionOffset) * parallaxSpeed}px, 0)`;
      });
    }

    function handleScroll() {
      if (!STATE.activeWipe) return;
      const data = STATE.wipeData.get(STATE.activeWipe);
      if (!data) return;

      const { scrollSpeedRatio, wipeOffset } = data;
      const scrollPosition = window.scrollY;
      const viewportHeight = getVH();
      const progress = (scrollPosition - wipeOffset + viewportHeight) / viewportHeight;
      if (progress >= 0) {
        const fasterScroll = (scrollPosition - wipeOffset + viewportHeight) / scrollSpeedRatio;
        STATE.activeWipe.style.transform = `translate3d(0, -${fasterScroll}px, 0)`;
      }
    }

    function observeWipes() {
      if (STATE.observers.wipe) STATE.observers.wipe.disconnect();

      STATE.observers.wipe = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              STATE.activeWipe = entry.target;
              window.addEventListener("scroll", handleScroll, { passive: true });
            } else if (STATE.activeWipe === entry.target) {
              STATE.activeWipe = null;
              window.removeEventListener("scroll", handleScroll);
            }
          });
        },
        { threshold: 0 }
      );

      wipes.forEach((wipe) => STATE.observers.wipe.observe(wipe));
    }

    function observeElements() {
      if (STATE.observers.section) STATE.observers.section.disconnect();

      STATE.observers.section = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) entry.target.classList.add("in-view");
            else entry.target.classList.remove("in-view");
          });
        },
        { threshold: 0 }
      );

      parallaxSections.forEach((section) => STATE.observers.section.observe(section));
    }

    function onScrollRaf() {
      if (STATE.rafId) return;
      STATE.rafId = requestAnimationFrame(() => {
        const scrollTop = window.scrollY;
        updateParallax(scrollTop);
        if (typeof bannerAPI.setBannerState === "function") bannerAPI.setBannerState(scrollTop);
        if (typeof bannerAPI.updateFade === "function") bannerAPI.updateFade(scrollTop);
        STATE.rafId = null;
      });
    }

    function reflowParallax() {
      if (STATE.rafLayout) return;
      STATE.rafLayout = requestAnimationFrame(() => {
        document
          .querySelectorAll(".parallax-background, .section-wipe")
          .forEach((el) => {
            el.style.transform = "translate3d(0,0,0)";
          });

        initializeParallax();
        positionSectionWipes();
        calculateWipeData();
        STATE.activeWipe = null;

        const scrollTop = window.scrollY;
        updateParallax(scrollTop);
        if (typeof bannerAPI.setBannerState === "function") bannerAPI.setBannerState(scrollTop);

        STATE.rafLayout = null;
      });
    }

    const reflowDebounced = debounce(reflowParallax, 80);

    // ✅ Correct: pass a root
    wrapDateTimeChars(document);
    applyStitchedLetters(document, "#parallax-section-1 .act-name");

    initializeParallax();
    positionSectionWipes();
    calculateWipeData();
    observeWipes();
    observeElements();

    const initialScroll = window.scrollY;
    updateParallax(initialScroll);
    if (typeof bannerAPI.setBannerState === "function") bannerAPI.setBannerState(initialScroll);
    if (typeof bannerAPI.updateFade === "function") bannerAPI.updateFade(initialScroll);
    if (typeof bannerAPI.setupRecolorObserver === "function") bannerAPI.setupRecolorObserver();

    window.addEventListener("scroll", onScrollRaf, { passive: true });

    window.addEventListener("resize", reflowDebounced);
    window.addEventListener("orientationchange", reflowDebounced);
    if (window.visualViewport) window.visualViewport.addEventListener("resize", reflowDebounced);

    if (document.fonts && document.fonts.ready) document.fonts.ready.then(reflowParallax);
    window.addEventListener("load", reflowParallax);

    window.hrSite = window.hrSite || {};
    window.hrSite.reflowParallax = reflowParallax;
  });
})();
