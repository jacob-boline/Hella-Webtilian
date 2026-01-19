# CSS Value Inventory Summary (Vite Build)

This summary is based on the machine-readable inventory at `tools/refactor/01_style_value_inventory.json` and covers project-authored CSS files imported by `hr_core/static_src/css/main.css` (17 files).【F:tools/refactor/01_style_value_inventory.json†L6986-L7004】

---

## 1) Observed Values (Highlights)

### Spacing + sizing
- **Most frequent values:** `0` (unitless), `100%`, `0.5rem`, `1rem`, `0.75rem`, `0.25rem`, `1.25rem`, `1.5rem`, `2rem`, `0.35rem` (top 10 by frequency).【F:tools/refactor/01_style_value_inventory.json†L7005-L9989】
- **Units present:** `%`, `ch`, `cqw`, `em`, `px`, `rem`, `unitless`, `vh`, `vmin`, `vw`.【F:tools/refactor/01_style_value_inventory.json†L1632-L6651】

### Radii
- **Common:** `0.75rem`, `1rem`, `12px`, `8px`, `100vmax` (rounded pills/circles).【F:tools/refactor/01_style_value_inventory.json†L7005-L9989】
- **Units present:** `px`, `rem`, `unitless`, `vmax`.【F:tools/refactor/01_style_value_inventory.json†L1632-L6651】

### Borders / outlines
- **Common widths:** `1px`, `2px`, and `0` (unitless).【F:tools/refactor/01_style_value_inventory.json†L7005-L9989】

### Typography
- **Font-size (rem):** heavy clustering at `0.7`, `0.75`, `0.85`, `0.9`, `1`, `1.25`, `1.5`.【F:tools/refactor/01_style_value_inventory.json†L6652-L6985】
- **Line-height (unitless):** `1`, `1.1`, `1.125`, `1.2`, `1.25`, `1.45`, `1.5`.【F:tools/refactor/01_style_value_inventory.json†L6652-L6985】
- **Font-weight:** `700` and `600` dominate usage.【F:tools/refactor/01_style_value_inventory.json†L7005-L9989】

### Time + motion
- **Durations (s):** `.2`, `.5`, `0.125`, `1`, `2.5`, `5`, plus some outliers (`3`, `6.5`, `9999`).【F:tools/refactor/01_style_value_inventory.json†L1632-L6651】
- **Easings:** `ease` is dominant; `ease-in`, `ease-in-out`, `ease-out`, and one `cubic-bezier(0.22, 1, 0.36, 1)` appear.【F:tools/refactor/01_style_value_inventory.json†L279-L394】

### Layering (z-index)
- **Common:** `1`, `2`, `10`, `20`, `50` plus higher layers (`500`, `1001`, `1500`, `1600`, `2000`).【F:tools/refactor/01_style_value_inventory.json†L1632-L6651】

### Colors
- **CSS color vars:** 55 distinct `--*` variables used for color (e.g., `--text`, `--muted-text`, `--neon-blue`, `--white-alpha-15`).【F:tools/refactor/01_style_value_inventory.json†L2-L59】
- **Hex colors:** multiple raw hex values (e.g., `#111`, `#0b0b0b`, `#ffb36b`, `#39ff14`, `#fecaca`).【F:tools/refactor/01_style_value_inventory.json†L60-L115】
- **RGBA:** tracked by base RGB with alpha ladders; see `color_usage.rgba`.【F:tools/refactor/01_style_value_inventory.json†L118-L278】

---

## 2) Suggested Scales (from observed clusters)

### Spacing scale (rem)
- `0.25`, `0.35`, `0.5`, `0.75`, `1`, `1.25`, `1.5`, `2`【F:tools/refactor/01_style_value_inventory.json†L6652-L6985】

### Radius scale
- **px:** `2`, `4`, `6`, `8`, `12`, `14`, `16`, `24`
- **rem:** `0.5`, `0.65`, `0.75`, `1`, `1.25`
- **vmax:** `100` (pill/circle)
- **unitless:** `0`【F:tools/refactor/01_style_value_inventory.json†L6652-L6985】

### Font-size scale (rem)
- `0.7`, `0.75`, `0.85`, `0.9`, `1`, `1.25`, `1.5`【F:tools/refactor/01_style_value_inventory.json†L6652-L6985】

### Line-height scale
- **unitless:** `0`, `1`, `1.1`, `1.125`, `1.2`, `1.25`, `1.45`, `1.5`【F:tools/refactor/01_style_value_inventory.json†L6652-L6985】

### Duration scale (s)
- `0`, `0.125`, `.2`, `.5`, `0.6`, `1`, `2.5`, `5`【F:tools/refactor/01_style_value_inventory.json†L6652-L6985】

### Alpha scales
- Derived per RGB base color (see `proposed_scales.alpha_scales`).【F:tools/refactor/01_style_value_inventory.json†L6652-L6985】

---

## 3) Mapping Guidance (high-level)

- **Safe to normalize:** repeated spacing steps in the `0.25–2rem` band and common radii (`2–16px`, `0.5–1.25rem`).【F:tools/refactor/01_style_value_inventory.json†L6652-L6985】
- **Risky to normalize:** line-height and letter-spacing (typography-sensitive).【F:tools/refactor/01_style_value_inventory.json†L1632-L6651】
- **Likely to keep exact:** `1px` borders/hairlines, precise transform offsets, and outlier long durations (`9999s`).【F:tools/refactor/01_style_value_inventory.json†L1632-L6651】

Full mapping tables are available in `mapping_recommendations` in the JSON for audit and tooling use.【F:tools/refactor/01_style_value_inventory.json†L395-L1631】
