# hr_core/media_jobs.py

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

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
    "wipe_section": Recipe(src_root="repo_static", src_rel_dir="hr_core/images/wipes",       out_subdir="opt_webp", widths=(960, 1440, 1920, 2560), crop=None)
}


def _run_imagemagick_convert(args, env=None):
    magick = shutil.which("magick")
    convert = shutil.which("convert")

    if magick:
        cmd = [magick, "convert", *args]   # IM7 style
    elif convert:
        cmd = [convert, *args]            # IM6 style
    else:
        raise FileNotFoundError("Neither 'magick' nor 'convert' found in PATH")

    subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)


def _target_size(w: int, crop: CropSpec) -> tuple[int, int]:
    h = (w * crop.ar_h) // crop.ar_w
    return w, h


def _out_path_for(src: Path, out_dir: Path, w: int) -> Path:
    return out_dir / f"{src.stem}-{w}w.webp"


def _is_up_to_date(src: Path, out: Path) -> bool:
    return out.exists() and out.stat().st_mtime >= src.stat().st_mtime


def _local_storage_path(storage, name: str) -> Path | None:
    try:
        return Path(storage.path(name))
    except (AttributeError, NotImplementedError):
        return None


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


def _build_convert_args(src: Path, out: Path, recipe: Recipe, w: int) -> list[str]:
    if recipe.crop is None:
        return [
            str(src),
            "-auto-orient",
            "-strip",
            "-resize",
            f"{w}x",
            "-quality",
            str(recipe.quality),
            "-define",
            f"webp:method={recipe.webp_method}",
            str(out)
        ]

    tw, th = _target_size(w, recipe.crop)
    size = f"{tw}x{th}"
    return [
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
        str(out)
    ]


def _normalize_media_name(src_rel_or_abs_path: str) -> str:
    src_path = Path(src_rel_or_abs_path)
    if src_path.is_absolute():
        try:
            return str(src_path.relative_to(settings.MEDIA_ROOT))
        except ValueError:
            return src_path.name
    return src_rel_or_abs_path


def _generate_media_variants(recipe_key: str, recipe: Recipe, src_rel_or_abs_path: str) -> dict:
    src_name = _normalize_media_name(src_rel_or_abs_path)

    if not default_storage.exists(src_name):
        return {"ok": False, "reason": "missing_source", "src": src_name}

    src_stem = Path(src_name).stem
    src_suffix = Path(src_name).suffix or ".bin"
    src_local = _local_storage_path(default_storage, src_name)

    made = skipped = failed = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        tmp_src = tmp_root / f"src{src_suffix}"
        tmp_out = tmp_root / "out.webp"

        with default_storage.open(src_name, "rb") as src_handle:
            tmp_src.write_bytes(src_handle.read())

        for w in recipe.widths:
            out_name = f"{recipe.src_rel_dir}/{recipe.out_subdir}/{src_stem}-{w}w.webp"
            out_local = _local_storage_path(default_storage, out_name)

            if src_local and out_local and _is_up_to_date(src_local, out_local):
                skipped += 1
                continue

            try:
                args = _build_convert_args(tmp_src, tmp_out, recipe, w)
                _run_imagemagick_convert(args)
                if default_storage.exists(out_name):
                    default_storage.delete(out_name)
                default_storage.save(out_name, ContentFile(tmp_out.read_bytes()))
                made += 1
            except subprocess.CalledProcessError:
                failed += 1
                logger.exception(
                    "media_job.convert_failed",
                    extra={"recipe": recipe_key, "src": src_name, "out": out_name}
                )
                continue

    return {
        "ok": failed == 0,
        "recipe": recipe_key,
        "src": src_name,
        "out_dir": f"{recipe.src_rel_dir}/{recipe.out_subdir}",
        "made": made,
        "skipped": skipped,
        "failed": failed
    }


def generate_variants_for_file(recipe_key: str, src_rel_or_abs_path: str) -> dict:
    logger.info(
        "media_job.invoked",
        extra={
            "recipe_key": recipe_key,
            "src_rel_or_abs_path": src_rel_or_abs_path
        }
    )

    if recipe_key not in RECIPES:
        raise ValueError(f"Unknown recipe_key: {recipe_key!r}")

    recipe = RECIPES[recipe_key]

    if recipe.src_root == "media":
        return _generate_media_variants(recipe_key, recipe, src_rel_or_abs_path)

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

        try:
            args = _build_convert_args(src, out_path, recipe, w)
            _run_imagemagick_convert(args)
            made += 1
        except subprocess.CalledProcessError:
            failed += 1
            logger.exception("media_job.convert_failed", extra={"recipe": recipe_key, "src": str(src), "out": str(out_path)})
            continue

    return {"ok": failed == 0, "recipe": recipe_key, "src": str(src), "out_dir": str(out_dir), "made": made, "skipped": skipped, "failed": failed}
