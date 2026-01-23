# hr_core/media_jobs.py

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CropSpec:
    ar_w: int
    ar_h: int


@dataclass(frozen=True)
class Recipe:
    src_rel_dir: str
    out_subdir: str
    widths: tuple[int, ...]
    crop: Optional[CropSpec]  # None = resize-only (native aspect)
    quality: int = 82
    webp_method: int = 6


RECIPES: dict[str, Recipe] = {
    "post_hero": Recipe(
        src_rel_dir="posts/hero",
        out_subdir="opt",
        widths=(640, 960, 1280, 1600),
        crop=CropSpec(16, 9)
    ),
    "variant": Recipe(
        src_rel_dir="variants",
        out_subdir="opt_webp",
        widths=(256, 512, 768),
        crop=CropSpec(1, 1)
    ),
    "about": Recipe(
        src_rel_dir="hr_about",
        out_subdir="opt_webp",
        widths=(640, 960, 1280, 1600, 1920),
        crop=CropSpec(3, 2)
    ),
    "background": Recipe(
        src_rel_dir="backgrounds",
        out_subdir="bg_opt",
        widths=(960, 1920),
        crop=None
    ),
    "wipe": Recipe(
        src_rel_dir="wipes",
        out_subdir="opt_webp",
        widths=(960, 1440, 1920, 2560),
        crop=None,
    )
}


def _run_imagemagick_convert(args: list[str]) -> None:
    """
    Always use ImageMagick 7 entrypoint to avoid Windows `convert.exe` conflict.
    """
    env = os.environ.copy()
    env.setdefault("MAGICK_THREAD_LIMIT", "1")

    try:
        subprocess.run(
            ["magick", "convert", *args],
            check=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.exception("ImageMagick failed", extra={"stdout": e.stdout, "stderr": e.stderr})
        raise


def _target_size(w: int, crop: CropSpec) -> tuple[int, int]:
    h = (w * crop.ar_h) // crop.ar_w
    return w, h


def _out_path_for(src: Path, out_dir: Path, w: int) -> Path:
    # unified naming scheme: <stem>-<w>w.webp
    return out_dir / f"{src.stem}-{w}w.webp"


def _is_up_to_date(src: Path, out: Path) -> bool:
    return out.exists() and out.stat().st_mtime >= src.stat().st_mtime


def generate_variants_for_file(recipe_key: str, src_rel_or_abs_path: str) -> dict:
    """
    Generate variants for ONE source file, idempotently.
    - recipe_key: one of RECIPES keys
    - src_rel_or_abs_path: absolute path OR path relative to MEDIA_ROOT
    """
    logger.info(
        "media_job.invoked",
        extra={
            "cwd":                 os.getcwd(),
            "MEDIA_ROOT":          str(settings.MEDIA_ROOT),
            "MEDIA_URL":           getattr(settings, "MEDIA_URL", None),
            "recipe_key":          recipe_key,
            "src_rel_or_abs_path": src_rel_or_abs_path,
        },
    )
    if recipe_key not in RECIPES:
        raise ValueError(f"Unknown recipe_key: {recipe_key!r}")

    recipe = RECIPES[recipe_key]
    media_root = Path(settings.MEDIA_ROOT)

    src = Path(src_rel_or_abs_path)
    if not src.is_absolute():
        src = media_root / src

    if not src.exists():
        return {"ok": False, "reason": "missing_source", "src": str(src)}

    src_dir = (media_root / recipe.src_rel_dir).resolve()
    out_dir = (src_dir / recipe.out_subdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    made = 0
    skipped = 0
    failed = 0

    for w in recipe.widths:
        out_path = _out_path_for(src, out_dir, w)

        if _is_up_to_date(src, out_path):
            skipped += 1
            continue

        if recipe.crop is None:
            # resize-only: preserve aspect
            args = [
                str(src),
                "-auto-orient",
                "-strip",
                "-resize", f"{w}x",
                "-quality", str(recipe.quality),
                "-define", f"webp:method={recipe.webp_method}",
                str(out_path),
            ]
        else:
            tw, th = _target_size(w, recipe.crop)
            size = f"{tw}x{th}"
            args = [
                str(src),
                "-auto-orient",
                "-strip",
                "-resize", f"{size}^",
                "-gravity", "center",
                "-extent", size,
                "-quality", str(recipe.quality),
                "-define", f"webp:method={recipe.webp_method}",
                str(out_path),
            ]

        try:
            _run_imagemagick_convert(args)
            made += 1
        except subprocess.CalledProcessError as e:
            failed += 1
            logger.exception(
                "media_job.convert_failed",
                extra={
                    "recipe":     recipe_key,
                    "src":        str(src),
                    "out":        str(out_path),
                    "returncode": e.returncode,
                    "stderr":     (e.stderr.decode("utf-8", "ignore") if e.stderr else None),
                    "stdout":     (e.stdout.decode("utf-8", "ignore") if e.stdout else None),
                    "args":       e.cmd,
                },
            )
            # keep going; you might still get some sizes
            continue

    return {
        "ok": failed == 0,
        "recipe": recipe_key,
        "src": str(src),
        "out_dir": str(out_dir),
        "made": made,
        "skipped": skipped,
        "failed": failed,
    }
