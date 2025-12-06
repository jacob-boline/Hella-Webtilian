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
