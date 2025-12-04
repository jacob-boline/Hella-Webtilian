# hr_shop/templatetags/shop_tags.py

from django import template

register = template.Library()


@register.simple_tag
def get_display_variant(product):
    """
    Returns the product's display variant.
    """
    return product.variants.filter(is_display_variant=True).first() or product.variants.first()
