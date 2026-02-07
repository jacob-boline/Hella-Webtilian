# Intro Animation Implementation Guide

## Overview

This implementation replaces the current letter-by-letter banner intro with a fast (~2.5s), intentional intro featuring the HR! circled monogram with diagnostic highlight sequence, followed by band name reveal, then yielding to scroll-driven content.

---

## Files Created/Modified

### New Files

1. **`hr_core/static_src/css/intro.css`**
   - All intro-specific styles
   - Overlay, logo, highlights, band name, scroll hint
   - Reduced motion overrides
   - Mobile optimizations

2. **`hr_core/static_src/js/modules/intro.js`**
   - Animation orchestration and timing
   - Skip/accelerate logic
   - Scroll hint control (idle nudge)
   - Reduced motion handling

### Modified Files

1. **`hr_core/static_src/css/main.css`**
   - Added: `@import './intro.css';` (line 12, after components, before sections)

2. **`hr_core/static_src/js/main.js`**
   - Added: `import './modules/intro.js'` (line 7, after meta-init, before other modules)

3. **`hr_common/templates/hr_common/base.html`**
   - Added: `<div id="intro-overlay">` structure with SVG logo and scroll hint
   - Location: Before `<div id="parallax-wrapper">` (around line 37)

---

## Installation Instructions

1. **Copy new files to your project:**
   ```bash
   # From the outputs directory:
   cp intro.css YOUR_PROJECT/hr_core/static_src/css/
   cp intro.js YOUR_PROJECT/hr_core/static_src/js/modules/
   ```

2. **Replace modified files:**
   ```bash
   # Back up your current files first!
   cp YOUR_PROJECT/hr_core/static_src/css/main.css YOUR_PROJECT/hr_core/static_src/css/main.css.backup
   cp YOUR_PROJECT/hr_core/static_src/js/main.js YOUR_PROJECT/hr_core/static_src/js/main.js.backup
   cp YOUR_PROJECT/hr_common/templates/hr_common/base.html YOUR_PROJECT/hr_common/templates/hr_common/base.html.backup
   
   # Then copy the new versions:
   cp main.css YOUR_PROJECT/hr_core/static_src/css/
   cp main.js YOUR_PROJECT/hr_core/static_src/js/
   cp base.html YOUR_PROJECT/hr_common/templates/hr_common/
   ```

3. **Rebuild Vite assets:**
   ```bash
   cd YOUR_PROJECT
   npm run build  # or your build command
   ```

4. **Restart Django dev server:**
   ```bash
   python manage.py runserver
   ```

---

## How It Works

### Animation Timeline

```
0ms        → Logo appears at 35% opacity
150ms      → H highlight pulse (200ms duration)
370ms      → R highlight pulse (200ms duration)
590ms      → ! stroke highlight (150ms)
760ms      → ! dot highlight (150ms)
850ms      → Logo ramps to 100% + name fades in (350ms)
1200ms     → Hold state (500ms)
1700ms     → Yield: overlay fades to transparent (400ms)
2100ms     → Intro complete, scroll hint appears
```

### Skip/Accelerate

User can skip the intro at any time by:
- **Scrolling** (wheel/trackpad)
- **Touching** (mobile)
- **Pressing keys** (ArrowDown, PageDown, Space)

When skipped, the intro jumps directly to the yield phase (still 400ms fade).

### Post-Intro Scroll Hint

After the intro yields:
1. Scroll hint fades in at bottom-center with waveform icon + "Scroll" text
2. If user hasn't interacted within 1200ms, trigger ONE micro-nudge animation (waveform moves down 12px and returns)
3. On first scroll/wheel/touch, hint fades out permanently and overlay is removed

**Important:** The intro never manipulates `scrollTop` or calls `window.scrollTo()`. User must scroll naturally to reveal content.

---

## Integration with Existing System

### Preserved Behaviors

✅ **Scroll-driven wipes** - Completely unaffected, remain scroll-position-driven  
✅ **Parallax sections** - Continue to work as before  
✅ **Banner API** - Old `banner.js` still functions (will be deprecated in future PR)  
✅ **Event system** - No conflicts with `events.js` or HTMX  
✅ **Viewport height handling** - Uses same approach for iOS address bar

### Why It Works

- Intro overlay is **separate DOM layer** (z-index 9999) that sits above everything
- Intro uses **simple setTimeout** for sequencing, not RAF or scroll events
- Skip listeners are **passive** and don't interfere with scroll-effects
- After intro completes, **existing scroll-effects take over normally**
- Page remains at **scrollTop = 0** when intro yields

---

## Testing Checklist

### Desktop Testing
- [ ] Chrome: Animation timing, skip on scroll/wheel/key
- [ ] Firefox: SVG rendering, transitions
- [ ] Safari: Color accuracy, font loading
- [ ] Edge: Overall functionality

### Mobile Testing
- [ ] iPhone Safari 15+: svh units, address bar behavior, touch skip
- [ ] Android Chrome: Touch skip, waveform rendering
- [ ] Landscape orientation: Logo sizing, hint positioning

### Accessibility Testing
- [ ] Reduced motion: Verify instant display, no animations, static hint
- [ ] Screen reader: Logo aria-label readable
- [ ] Keyboard navigation: Skip works with Space/PageDown/ArrowDown
- [ ] High contrast mode: Logo and text remain visible

### Integration Testing
- [ ] Scroll-effects still work after intro completes
- [ ] Section wipes positioned correctly
- [ ] Parallax backgrounds animate smoothly
- [ ] Banner fade-out behavior preserved (old system)
- [ ] Modal/drawer interactions unaffected

### Performance Testing
- [ ] No layout thrashing (check DevTools Performance tab)
- [ ] Smooth 60fps on intro animations
- [ ] GPU-accelerated transforms (check Layers panel)
- [ ] No memory leaks (timeouts cleared properly)

---

## Customization

### Timing Adjustments

Edit `TIMINGS` object in `intro.js`:

```javascript
const TIMINGS = {
    logoFadeIn: 150,        // Initial logo appearance
    highlightH: {
        start: 150,         // When H highlight starts
        duration: 200       // How long it pulses
    },
    // ... etc
    hintIdleDelay: 1200,    // How long to wait before nudge
};
```

### Color Changes

Edit CSS custom properties or direct color values in `intro.css`:

```css
.intro-logo-base {
    color: darkorange;      /* Change logo color */
}

.intro-logo-highlight {
    color: var(--neon-blue, #4ec5ec);  /* Change highlight color */
}

.intro-name {
    color: darkorange;      /* Change name color */
}
```

### Logo Adjustments

SVG paths in `base.html` can be modified to refine the logo appearance. Current paths are optimized for the circled HR! design.

---

## Migration Path (Future PR)

Once the new intro is proven stable:

1. **Remove old banner system:**
   - Delete `banner.js` (or comment out)
   - Delete `banner.css` (or comment out)
   - Remove `#banner` and `#banner-scroller` from `base.html`
   - Remove banner API calls from `scroll-effects.js`

2. **Clean up nav/cart button logic:**
   - Buttons currently fade in based on banner position
   - Will need new logic for when to show nav/cart buttons
   - Could be scroll-based or simply always visible

3. **Optional: Convert intro to TypeScript**
   - Add types for better IDE support
   - Validate timing configurations

---

## Troubleshooting

### Intro doesn't appear
- Check browser console for `[intro]` warnings
- Verify `#intro-overlay` exists in DOM
- Confirm Vite build completed successfully
- Check that CSS and JS files are imported in `main.css` and `main.js`

### Logo looks wrong
- SVG paths may need adjustment for your logo
- Check stroke-width and fill colors match your brand
- Verify viewBox is `0 0 200 200` for proper scaling

### Skip not working
- Check that event listeners are registered (look for `addEventListener` calls in DevTools)
- Verify skip keys: ArrowDown, PageDown, Space
- Test with mouse wheel and touch gestures

### Hint doesn't appear or animate
- Scroll hint shows only after intro completes
- Check for `prefers-reduced-motion` media query (disables nudge)
- Verify `intro-scroll-hint` class exists in DOM

### Conflicts with existing scroll behavior
- Intro should not affect scroll-effects.js
- Verify `scrollTop` remains 0 when intro completes
- Check that wipes are positioned correctly after intro

---

## Browser Support

**Minimum Requirements:**
- Chrome 90+ (2021)
- Firefox 88+ (2021)
- Safari 15+ (2021) - Required for svh units
- Edge 90+ (2021)

**Features Used:**
- CSS `svh` units (viewport height with mobile address bar)
- CSS transforms (translate3d, translateY)
- CSS filters (drop-shadow)
- IntersectionObserver (already in use by scroll-effects)
- Performance API (performance.now())

---

## Performance Notes

**Optimized:**
- All animations use `transform` and `opacity` only (GPU-accelerated)
- SVG complexity kept minimal (simple shapes, strokes)
- No layout reads during animation
- Timeouts cleared properly on skip
- Passive event listeners where possible

**Will-change hints applied to:**
- `.intro-logo-base`
- `.intro-name`
- `.hint-waveform`

**Memory cleanup:**
- All timeouts stored and cleared
- Event listeners removed after intro
- Overlay removed from DOM after hint interaction

---

## Known Limitations

1. **Old banner still present:** The existing `#banner` and `#banner-scroller` elements remain in the DOM. They will be removed in a future cleanup PR.

2. **Font loading race:** If custom fonts load slowly, the band name may render in fallback font briefly. This is acceptable but could be improved with font-display strategies.

3. **No skip button:** Users must discover natural skip methods (scroll/touch/key). This is intentional per design requirements.

---

## Support

For questions or issues:
1. Check browser console for warnings/errors
2. Verify file paths match your project structure
3. Test with reduced motion enabled/disabled
4. Compare timing with the design spec
5. Review integration checklist above

---

## Credits

**Design:** Hella Reptilian brand requirements  
**Implementation:** Claude (Anthropic)  
**Integration:** Preserved existing scroll-effects.js architecture

---

Last updated: 2025-02-05
