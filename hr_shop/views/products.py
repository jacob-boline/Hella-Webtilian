import json

from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.templatetags.static import static
from django.views.decorators.http import require_POST, require_GET

from hr_shop.models import Product
from hr_shop.queries import get_active_product_tree
from hr_shop.utils import resolve_variant_for_values


def get_merch_grid_partial(request):

    products = get_active_product_tree()

    return render(request, 'hr_shop/_OLD_merch_grid_partial.html', {'products': products, })


def get_product_modal_partial(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    option_types = product.option_types.prefetch_related('values')
    display_variant = product.display_variant

    if display_variant:
        display_values = display_variant.option_values.select_related('option_type')

        # map each option type on the product to the option value related to the product's display variant
        mapping = {ov.option_type_id: ov.id for ov in display_values}

        for opt in option_types:
            setattr(opt, 'default_value_id', mapping.get(opt.id))

    variants_data = []
    for v in product.variants.filter(active=True).prefetch_related('option_values', 'image'):
        img = v.resolve_image()
        img_url = img.image.url if img and img.image else static('hr_shop/img/placeholder_2.png')

        variants_data.append({
            'id': v.id,
            'slug': v.slug,
            'price': str(v.price),
            'image_url': img_url,
            'option_value_ids': list(v.option_values.values_list('id', flat=True))
        })

    context = {
        'product': product,
        'option_types': option_types,
        'display_variant': display_variant,
        'variants_json': json.dumps(variants_data)
    }

    return render(request, 'hr_shop/_product_detail_modal.html', context)


@require_POST
def update_details_modal(request, product_slug):
    """
    Given a product and posted option_... values, return:
        - image_url
        - price
        - variant_slug
    via an HX-Trigger event.
    """
    product = get_object_or_404(Product, slug=product_slug)

    selected_value_ids = []
    for key, value in request.POST.items():
        if key.startswith('opt_') and value:
            try:
                selected_value_ids.append(int(value))
            except ValueError:
                pass

    if not selected_value_ids:
        return HttpResponseBadRequest('No options selected')

    # 🔥 Resolve the variant first
    variant = resolve_variant_for_values(product, selected_value_ids)

    # Resolve image from that variant
    img = variant.resolve_image() if variant else None
    if img and getattr(img, "image", None):
        image_url = img.image.url
    else:
        image_url = static('hr_shop/img/placeholder_2.png')

    # At this point, resolve_variant_for_values should NEVER return None,
    # so it's safe to drop the `if variant else None` guards:
    context = {
        "image_url": image_url,
        "price": str(variant.price),
        "variant_slug": variant.slug,
    }

    response = HttpResponse(status=204)
    response["HX-Trigger"] = json.dumps({"variantPreviewUpdated": context})
    return response


@require_GET
def product_image_for_selection(request, product_slug):
    """
    Given ?ov=<option_value_id>&ov=<option_value_id>...,
    find the best-matching variant for this product and
    return its image URL + alt.
    """
    product = get_object_or_404(Product, slug=product_slug)

    # Gather selected option value IDs
    raw_ids = request.GET.getlist("ov")
    try:
        selected_ids = {int(x) for x in raw_ids if x}
    except ValueError:
        selected_ids = set()

    # Prefetch everything we need
    variants = (
        product.variants
        .select_related("image")
        .prefetch_related("option_values")
    )

    chosen_variant = None

    if selected_ids:
        # Look for the most specific variant whose option_values
        # set is a superset of the selected IDs.
        # (If you want strict equality, change the condition.)
        for v in variants:
            v_ids = set(v.option_values.values_list("id", flat=True))
            if selected_ids.issubset(v_ids):
                chosen_variant = v
                break

    # Fallbacks
    if not chosen_variant:
        chosen_variant = product.display_variant or variants.first()

    img = chosen_variant.resolve_image() if chosen_variant else None
    if img:
        return JsonResponse(
            {
                "url": img.image.url,
                "alt": img.alt_text or product.name,
            }
        )

    # Final fallback: no image
    return JsonResponse(
        {
            "url": "",
            "alt": product.name,
        }
    )
