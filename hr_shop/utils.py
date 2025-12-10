# hr_shop/utils.py


def resolve_product_image_for_values(product, option_value_ids):
    """
    Given a product and a set/list of OptionValue IDs (selected in the modal),
    choose the most specific ProductImage that matches.
    """
    selected = set(option_value_ids)
    qs = product.images.prefetch_related('option_values')

    best = None
    best_specificity = -1

    for img in qs:
        img_ids = set(img.option_values.values_list('id', flat=True))
        if img_ids.issubset(selected):
            spec = len(img_ids)
            if spec > best_specificity:
                best_specificity = spec
                best = img

    if best:
        return best

    return (
        product.images.filter(is_display=True).first()
        or product.images.first()
    )


def resolve_variant_for_values(product, option_value_ids):
    """
    Given a product and a set/list of OptionValue IDs, find the best-matching ProductVariant.

    - Prefer variants whose option_values are a *superset* of the selected IDs.
    - Among those, pick the one with the most option_values (most specific).
    - Fallback to product.display_variant or first active variant.
    """
    selected = set(map(int, option_value_ids))

    variants = (
        product.variants
        .filter(active=True)
        .prefetch_related("option_values", "image")
    )

    best_variant = None
    best_specificity = -1

    for variant in variants:
        v_ids = variant.option_value_ids_set
        if selected.issubset(v_ids):
            spec = len(v_ids)
            if spec > best_specificity:
                best_specificity = spec
                best_variant = variant

    if best_variant is None:
        # Last-resort fallback: display_variant or first active variant
        best_variant = product.display_variant or variants.first()

    return best_variant
