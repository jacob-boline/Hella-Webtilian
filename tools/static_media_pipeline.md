# Background/Wipe Media Pipeline (Current Behavior + Recommended Direction)

This note explains where background + wipe images live, how they are seeded, how srcset/image-set URLs are generated, and where generated WebP variants are written.

## 1) Source of truth for base assets

Base images for section wipes and parallax backgrounds are treated as **repo static assets**.

- Expected source location (after seeding):
  - `hr_core/static/hr_core/images/wipes/<file>`
  - `hr_core/static/hr_core/images/backgrounds/<file>`

These paths are rooted by `REPO_STATIC_ROOT` (`BASE_DIR / "hr_core" / "static"`).

## 2) Seeding behavior

`seed_media_assets` copies from `_seed_data/media/{wipes,backgrounds}` into repo static:

- source: `_seed_data/media/wipes`, `_seed_data/media/backgrounds`
- destination: `REPO_STATIC_ROOT / "hr_core" / "images" / {wipes,backgrounds}`

So seeding puts base assets exactly where CSS/static serving expects them.

## 3) Recipe config + media sweep behavior

`RECIPES` in `hr_core/media_jobs.py` define two static recipes:

- `bg_section`: src `hr_core/images/backgrounds`, output subdir `bg_opt`, widths `960,1920`
- `wipe_section`: src `hr_core/images/wipes`, output subdir `opt_webp`, widths `960,1440,1920,2560`

Both use `src_root="repo_static"`, meaning:

- source root = `REPO_STATIC_ROOT`
- output root = `REPO_STATIC_ROOT`

`media_sweep` reads those recipe roots and enqueues jobs for files in those directories.

## 4) Variant output location (important)

For background/wipe recipes, variants are written **alongside static sources** under repo static:

- backgrounds: `hr_core/static/hr_core/images/backgrounds/bg_opt/<stem>-<w>w.webp`
- wipes: `hr_core/static/hr_core/images/wipes/opt_webp/<stem>-<w>w.webp`

This is intentional in current code because `repo_static` recipes set output root equal to `REPO_STATIC_ROOT`.

## 5) CSS/image-set pipeline

`build_responsive_backgrounds` generates CSS at:

- `hr_core/static_src/css/generated/responsive_backgrounds.css`

The generated CSS uses:

- fallback base URLs under `/static/hr_core/images/{wipes|backgrounds}/<file>`
- `image-set(...)` URLs under:
  - `/static/hr_core/images/wipes/opt_webp/<stem>-<w>w.webp`
  - `/static/hr_core/images/backgrounds/bg_opt/<stem>-<w>w.webp`

`main.css` imports that generated file (`@import './generated/responsive_backgrounds.css';`).

## 6) Template usage (`index.html`)

The home template defines structural elements/IDs (`section-wipe-*`, `parallax-section-*`) but does not hardcode image URLs there.

Image assignment is expected to come from generated responsive CSS keyed by IDs from `backgrounds_config.py`.

## 7) What `REPO_STATIC_ROOT` is doing

`REPO_STATIC_ROOT` is the anchor for both:

1. seeding base static background/wipe files, and
2. writing generated WebP variants for those same static files.

In short: for wipes/backgrounds, this pipeline is static-first, not media-first.

## 8) Recommended storage decision (static vs S3)

For **site chrome assets** like parallax backgrounds + section wipes, the cleanest default is:

- keep base images + generated variants in static (repo/static build artifact path),
- serve through static pipeline/CDN in production.

Why:

- these are not user-uploaded assets,
- they are versioned with deploys,
- URLs are deterministic and tied to frontend CSS.

Use S3 for these only if your platform already uses S3 as the static origin/CDN backing store. In that case, treat them as static deploy artifacts (not dynamic media uploads).

## 9) Operational order that should happen

1. `seed_media_assets` (populate base static files)
2. `media_sweep --recipe bg_section` + `media_sweep --recipe wipe_section` (enqueue variants)
3. run RQ worker to generate WebP files
4. `build_responsive_backgrounds` (emit CSS that references generated variants)
5. frontend build/deploy static assets

If step 3 has not completed, CSS can still fall back to base JPEG/PNG URLs.
