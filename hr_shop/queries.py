from django.db.models import Prefetch, Q
from hr_shop.models import Product, ProductVariant, ProductOptionType, ProductOptionValue


active_option_values_qs = (
    ProductOptionValue.objects
    .filter(
        active=True,
        option_type__active=True,
        variants__active=True,            # only values used by at least one active variant
    )
    .select_related("option_type")        # FK "upstream" → use select_related
    .distinct()
)

active_variants_qs = (
    ProductVariant.objects
    .filter(active=True)
    .prefetch_related(
        Prefetch(
            "option_values",
            queryset=active_option_values_qs,
            to_attr="active_option_values",   # optional: stash on a custom attribute
        )
    )
)


active_option_types_qs = (
    ProductOptionType.objects
    .filter(
        active=True,
        values__active=True,
        values__variants__active=True,
    )
    .prefetch_related(
        Prefetch(
            "values",
            queryset=active_option_values_qs,
            to_attr="active_values",
        )
    )
    .distinct()
)


def get_active_product_tree():
    return (
        Product.objects
        .filter(active=True)
        .prefetch_related(
            Prefetch(
                "variants",
                queryset=active_variants_qs,
                to_attr="active_variants",
            ),
            Prefetch(
                "option_types",
                queryset=active_option_types_qs,
                to_attr="active_option_types",
            ),
        )
    )
