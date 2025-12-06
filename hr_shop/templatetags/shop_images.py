# hr_shop/templatetags/shop_images.py

from django import template

register = template.Library()


@register.simple_tag
def variant_image(variant):
    """
    Return the ProductImage object chosen for this variant, or None.
    """
    if not variant:
        return None
    resolver = getattr(variant, "resolve_image", None)
    if not callable(resolver):
        return None
    return resolver()
