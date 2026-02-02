# hr_core/templatetags/responsive_images.py

from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import urlsplit, urlunsplit

from django import template
from django.templatetags.static import static

register = template.Library()


# ------------------------------
# Media URL helpers (ImageField)
# ------------------------------

def _swap_dir_and_suffix(url: str, subdir: str, suffix: str) -> str:
    """
    Given an ImageField URL like /media/hr_about/foo.jpg,
    produce /media/hr_about/<subdir>/foo<suffix>.webp
    """
    if not url:
        return url

    parts = urlsplit(url)
    path = parts.path

    if "/" not in path:
        return url

    dirpath, filename = path.rsplit("/", 1)
    stem = filename.rsplit(".", 1)[0]
    new_path = f"{dirpath}/{subdir}/{stem}{suffix}.webp"
    return urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))


@register.filter
def about_img_url(url: str, width: int) -> str:
    return _swap_dir_and_suffix(url, "opt_webp", f"-{int(width)}w")


@register.filter
def about_img_srcset(url: str) -> str:
    widths = (640, 960, 1280, 1600, 1920)
    return ", ".join(f"{about_img_url(url, w)} {w}w" for w in widths)


@register.filter
def post_hero_url(url: str, width: int) -> str:
    return _swap_dir_and_suffix(url, "opt", f"-{int(width)}w")


@register.filter
def post_hero_srcset(url: str) -> str:
    widths = (640, 960, 1280, 1600)
    return ", ".join(f"{post_hero_url(url, w)} {w}w" for w in widths)


ALLOWED_VARIANT_SIZES = {"256", "512", "768"}


@register.filter
def variant_img_url(url: str, size: int | str) -> str:
    if size is None:
        raise ValueError("variant_img_url: size is None")

    s = str(size).strip().replace(" ", "")
    if s not in ALLOWED_VARIANT_SIZES:
        raise ValueError(f"variant_img_url: invalid size {size!r}")

    return _swap_dir_and_suffix(url, "opt_webp", f"-{s}w")


@register.filter
def variant_img_srcset(url: str) -> str:
    return ", ".join(
        [
            f"{variant_img_url(url, 256)} 256w",
            f"{variant_img_url(url, 512)} 512w",
            f"{variant_img_url(url, 768)} 768w",
        ]
    )


# ------------------------------
# Static background/wipe helpers
# ------------------------------

def _static_variant_from_source(source_static_path: str, out_bucket: str, out_subdir: str, width: int) -> str:
    """
    Convert a source static asset path like:
      hr_core/images/backgrounds/hero-01.jpg

    into a generated variant static path like:
      hr_core/images/backgrounds/bg_opt/hero-01-1920w.webp

    Assumes variants are written alongside the sources inside static:
      hr_core/static/hr_core/images/<bucket>/<out_subdir>/<stem>-<w>w.webp

    and Django serves it under /static/.
    """
    if not source_static_path:
        return source_static_path

    p = PurePosixPath(source_static_path)
    stem = p.stem
    out_rel = PurePosixPath("hr_core") / "images" / out_bucket / out_subdir / f"{stem}-{int(width)}w.webp"
    return static(str(out_rel))


@register.simple_tag
def background_url(source_static_path: str, width: int) -> str:
    # recipe: bg_section -> out_subdir "bg_opt"
    return _static_variant_from_source(source_static_path, out_bucket="backgrounds", out_subdir="bg_opt", width=width)


@register.simple_tag
def background_srcset(source_static_path: str) -> str:
    widths = (960, 1920)
    return ", ".join(f"{background_url(source_static_path, w)} {w}w" for w in widths)


@register.simple_tag
def wipe_url(source_static_path: str, width: int) -> str:
    # recipe: wipe_section -> out_subdir "opt_webp"
    return _static_variant_from_source(source_static_path, out_bucket="wipes", out_subdir="opt_webp", width=width)


@register.simple_tag
def wipe_srcset(source_static_path: str) -> str:
    widths = (960, 1440, 1920, 2560)
    return ", ".join(f"{wipe_url(source_static_path, w)} {w}w" for w in widths)
