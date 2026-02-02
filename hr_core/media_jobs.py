# hr_core/media_jobs.py

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CropSpec:
    ar_w: int
    ar_h: int


@dataclass(frozen=True)
class Recipe:
    # NEW: where sources come from
    src_root: str  # "media" | "static_src" | "static"

    # relative to the chosen root
    src_rel_dir: str

    # relative to output root (media or static output)
    out_subdir: str

    widths: tuple[int, ...]
    crop: CropSpec | None  # None = resize-only (native aspect)
    quality: int = 82
    webp_method: int = 6


RECIPES: dict[str, Recipe] = {
    # existing media-based ones stay "media"
    "post_hero":  Recipe(src_root="media", src_rel_dir="posts/hero",  out_subdir="opt",      widths=(640, 960, 1280, 1600),       crop=CropSpec(16, 9)),
    "variant":    Recipe(src_root="media", src_rel_dir="variants",    out_subdir="opt_webp", widths=(256, 512, 768),              crop=CropSpec(1, 1)),
    "about":      Recipe(src_root="media", src_rel_dir="hr_about",    out_subdir="opt_webp", widths=(640, 960, 1280, 1600, 1920), crop=CropSpec(3, 2)),

    # backgrounds + wipes become repo assets
    "bg_section":   Recipe(src_root="repo_static", src_rel_dir="hr_core/images/backgrounds", out_subdir="bg_opt",   widths=(960, 1920),             crop=None),
    "wipe_section": Recipe(src_root="repo_static", src_rel_dir="hr_core/images/wipes",       out_subdir="opt_webp", widths=(960, 1440, 1920, 2560), crop=None),
}


def _run_imagemagick_convert(args: list[str]) -> None:
    env = os.environ.copy()
    env.setdefault("MAGICK_THREAD_LIMIT", "1")
    subprocess.run(["magick", "convert", *args], check=True, env=env, capture_output=True, text=True)


def _target_size(w: int, crop: CropSpec) -> tuple[int, int]:
    h = (w * crop.ar_h) // crop.ar_w
    return w, h


def _out_path_for(src: Path, out_dir: Path, w: int) -> Path:
    return out_dir / f"{src.stem}-{w}w.webp"


def _is_up_to_date(src: Path, out: Path) -> bool:
    return out.exists() and out.stat().st_mtime >= src.stat().st_mtime


def _get_roots(recipe: Recipe) -> tuple[Path, Path]:
    """
    Returns (src_root, out_root) based on recipe.src_root.
    """
    if recipe.src_root == "media":
        src_root = Path(settings.MEDIA_ROOT)
        out_root = Path(settings.MEDIA_ROOT)
    elif recipe.src_root == "static_src":
        src_root = Path(settings.STATIC_SOURCE_ROOT)
        out_root = Path(settings.STATIC_VARIANTS_ROOT)
    elif recipe.src_root == 'repo_static':
        src_root = Path(settings.REPO_STATIC_ROOT)
        out_root = Path(settings.REPO_STATIC_ROOT)
    else:
        raise ValueError(f"Unknown recipe.src_root: {recipe.src_root!r}")
    return src_root, out_root


def generate_variants_for_file(recipe_key: str, src_rel_or_abs_path: str) -> dict:
    logger.info(
        "media_job.invoked",
        extra={
            "recipe_key": recipe_key,
            "src_rel_or_abs_path": src_rel_or_abs_path,
        },
    )

    if recipe_key not in RECIPES:
        raise ValueError(f"Unknown recipe_key: {recipe_key!r}")

    recipe = RECIPES[recipe_key]
    src_root, out_root = _get_roots(recipe)

    src = Path(src_rel_or_abs_path)
    if not src.is_absolute():
        src = (src_root / src).resolve()

    if not src.exists():
        return {"ok": False, "reason": "missing_source", "src": str(src)}

    src_dir = (src_root / recipe.src_rel_dir).resolve()
    out_dir = (out_root / recipe.src_rel_dir / recipe.out_subdir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    made = skipped = failed = 0

    for w in recipe.widths:
        out_path = _out_path_for(src, out_dir, w)

        if _is_up_to_date(src, out_path):
            skipped += 1
            continue

        if recipe.crop is None:
            args = [
                str(src),
                "-auto-orient",
                "-strip",
                "-resize",
                f"{w}x",
                "-quality",
                str(recipe.quality),
                "-define",
                f"webp:method={recipe.webp_method}",
                str(out_path),
            ]
        else:
            tw, th = _target_size(w, recipe.crop)
            size = f"{tw}x{th}"
            args = [
                str(src),
                "-auto-orient",
                "-strip",
                "-resize",
                f"{size}^",
                "-gravity",
                "center",
                "-extent",
                size,
                "-quality",
                str(recipe.quality),
                "-define",
                f"webp:method={recipe.webp_method}",
                str(out_path),
            ]

        try:
            _run_imagemagick_convert(args)
            made += 1
        except subprocess.CalledProcessError:
            failed += 1
            logger.exception("media_job.convert_failed", extra={"recipe": recipe_key, "src": str(src), "out": str(out_path)})
            continue

    return {"ok": failed == 0, "recipe": recipe_key, "src": str(src), "out_dir": str(out_dir), "made": made, "skipped": skipped, "failed": failed}
