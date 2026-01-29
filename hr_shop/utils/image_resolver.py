# hr_shop/utils/image_resolver.py

from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict

from django.templatetags.static import static

from hr_shop.models import Product, ProductVariant


class PreviewImagePayload(TypedDict):
    url: str
    alt: str


def _parse_int_set(values: Iterable[int | str]) -> set[int]:
    out: set[int] = set()
    for x in values:
        try:
            out.add(int(x))
        except (TypeError, ValueError):
            continue
    return out


def resolve_variant_for_values(product: Product, option_value_ids: Iterable[int | str]) -> ProductVariant | None:
    """
    Given a product and a set/list of OptionValue IDs, find the best-matching active ProductVariant.

    Deterministic rules:
      1) Consider active variants whose option_values are a *superset* of the selected IDs.
      2) Prefer an *exact match* (no extra option values) if available.
      3) Otherwise prefer the *smallest superset* (fewest extra option values).
      4) Tie-breaker: lowest variant.id (stable).
      5) Fallback: product.display_variant or first active variant.
    """
    selected = _parse_int_set(option_value_ids)

    variants = list(product.variants.filter(active=True).prefetch_related("option_values", "image"))
    if not variants:
        return None

    best_variant: ProductVariant | None = None
    best_score: tuple[int, int] | None = None  # (extra_count, id)

    for variant in variants:
        v_ids = variant.option_value_ids_set
        if not selected.issubset(v_ids):
            continue

        extra_count = len(v_ids - selected)
        score = (extra_count, variant.id)

        if best_score is None or score < best_score:
            best_score = score
            best_variant = variant

    return best_variant or product.display_variant or variants[0]


def resolve_variant_preview_image_payload(
    variant: ProductVariant | None,
    *,
    placeholder_url: str | None = None,
    fallback_alt: str = "",
) -> PreviewImagePayload:
    """
    Resolve the preview image payload for a variant.

    Assumption:
      - Variants are expected to have images.
      - If the variant is missing an image, use a placeholder.

    This intentionally does NOT attempt a "product-level" image fallback, since Product
    currently has no direct images relation in the schema.
    """

    placeholder: str = placeholder_url or static("hr_shop/img/placeholder_2.png")

    if not variant:
        return {"url": placeholder, "alt": fallback_alt}

    img = variant.resolve_image()
    if img and getattr(img, "image", None):
        return {
            "url": img.image.url,
            "alt": (img.alt_text or fallback_alt or "").strip(),
        }

    return {
        "url": placeholder,
        "alt": (fallback_alt or "").strip(),
    }
