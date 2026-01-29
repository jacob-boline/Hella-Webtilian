# hr_core/templatetags/responsive_images.py


from urllib.parse import urlsplit, urlunsplit

from django import template

register = template.Library()


def _swap_dir_and_suffix(url: str, subdir: str, suffix: str) -> str:
    """
    Given an ImageField URL like /media/hr_about/foo.jpg,
    produce /media/hr_about/<subdir>/foo<suffix>.webp
    """
    if not url:
        return url

    parts = urlsplit(url)
    path = parts.path

    # Split to directory + filename
    if "/" not in path:
        return url
    dirpath, filename = path.rsplit("/", 1)

    # Remove extension from filename
    stem = filename.rsplit(".", 1)[0]

    new_path = f"{dirpath}/{subdir}/{stem}{suffix}.webp"
    return urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))


@register.filter
def about_img_url(url: str, width: int) -> str:
    return _swap_dir_and_suffix(url, "opt_webp", f"-{int(width)}w")


@register.filter
def about_img_srcset(url: str) -> str:
    widths = [640, 960, 1280, 1600, 1920]
    return ", ".join(f"{about_img_url(url, w)} {w}w" for w in widths)


@register.filter
def post_hero_url(url: str, width: int) -> str:
    # your posts hero opt dir is /media/posts/hero/opt/
    return _swap_dir_and_suffix(url, "opt", f"-{int(width)}w")


@register.filter
def post_hero_srcset(url: str) -> str:
    widths = [640, 960, 1280, 1600]
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
