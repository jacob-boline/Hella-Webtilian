# hr_shop/views.py

# import json
import json
import logging
# import urllib.parse
# import stripe

# from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.db.models import Q, Prefetch

from hr_shop.models import Order, Product, ProductVariant, ProductOptionType, ProductOptionValue
from hr_shop.forms import ProductQuickForm, ProductEditForm, ProductVariantForm, ProductOptionTypeForm, ProductOptionValueForm
from hr_shop.cart import add_to_cart

from hr_core.utils.http import is_htmx
from hr_shop.queries import get_active_product_tree


log = logging.getLogger(__name__)


def add_variant_to_cart(request, variant_slug):
    quantity = request.POST.get('quantity', 1)

    cart, variant, line_qty = add_to_cart(request, variant_slug, quantity)

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showMessage': {
            'message': f"Added {variant.product.name} x{line_qty} to cart"
        }
    })

    return response
#
# def add_to_cart(request, variant_slug):
#     quantity = int(request.POST.get('quantity', 1))
#
#     variant = get_object_or_404(ProductVariant, slug=variant_slug)
#
#     cart = get_or_create_cart(request)
#     cart.add(variant, quantity)
#
#     response = HttpResponse(status=204)
#     response['HX-Trigger'] = json.dumps({
#         'showMessage': {'message': f"Added {variant.product.name} to cart"}
#     })
#     return response


@staff_member_required
def product_manager(request):
    """
    Main management UI shell. HTMX fills product list, product panel, and option type panel.
    """
    return render(request, 'hr_shop/manage_products.html')


@staff_member_required
def get_manage_product_list_partial(request):
    products = Product.objects.all().order_by('name')
    form = ProductQuickForm()
    return render(
        request,
        'hr_shop/_pm_product_list.html', {
            'products': products,
            'form': form
        }
    )


@staff_member_required
def create_product(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    form = ProductQuickForm(request.POST)
    if form.is_valid():
        form.save()

    products = Product.objects.all().order_by('name')
    form = ProductQuickForm()
    return render(request,'hr_shop/_pm_product_list.html', {
            'products': products,
            'form': form
        }
    )


@staff_member_required
def get_manage_product_panel_partial(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related('variants', 'option_types__values'), pk=pk)
    option_types = product.option_types.all().order_by('position', 'id')
    variants = product.variants.all().order_by('id')

    product_form = ProductEditForm(instance=product)
    variant_form = ProductVariantForm()
    option_type_form = ProductOptionTypeForm()

    return render(request, 'hr_shop/_pm_product_panel_partial.html', {
        'product': product,
        'option_types': option_types,
        'variants': variants,
        'product_form': product_form,
        'variant_form': variant_form,
        'option_type_form': option_type_form
    })


@staff_member_required
def update_product(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    product = get_object_or_404(Product, pk=pk)
    form = ProductEditForm(request.POST, instance=product)
    if form.is_valid():
        form.save()

    return get_manage_product_panel_partial(request, pk)


@staff_member_required
def get_manage_option_type_panel_partial(request, pk):
    opt_type = get_object_or_404(ProductOptionType.objects.prefetch_related('values', 'product'), pk=pk)
    values = opt_type.values.all().order_by('position', 'id')
    form = ProductOptionValueForm()

    return render(
        request,
        'hr_shop/_pm_option_type_panel_partial.html',
        {
            'option_type': opt_type,
            'values': values,
            'value_form': form
        }
    )


@staff_member_required
def create_option_type(request, product_pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    product = get_object_or_404(Product, pk=product_pk)
    form = ProductOptionTypeForm(request.POST)
    if form.is_valid():
        opt_type = form.save(commit=False)
        opt_type.product = product
        opt_type.save()

    return get_manage_product_panel_partial(request, product_pk)


@staff_member_required
def update_option_type(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    opt_type = get_object_or_404(ProductOptionType, pk=pk)
    form = ProductOptionTypeForm(request.POST, instance=opt_type)
    if form.is_valid():
        form.save()

    return get_manage_option_type_panel_partial(request, pk)


@staff_member_required
def delete_option_type(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    opt_type = get_object_or_404(ProductOptionType, pk=pk)
    product_pk = opt_type.product_id
    opt_type.delete()

    return get_manage_product_panel_partial(request, product_pk)


@staff_member_required
def create_option_value(request, option_type_pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    opt_type = get_object_or_404(ProductOptionType, pk=option_type_pk)
    form = ProductOptionValueForm(request.POST)
    if form.is_valid():
        value = form.save(commit=False)
        value.option_type = opt_type
        value.save()

    return get_manage_option_type_panel_partial(request, option_type_pk)


@staff_member_required
def update_option_value(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    val = get_object_or_404(ProductOptionValue, pk=pk)
    opt_type_pk = val.option_type_id
    form = ProductOptionValueForm(request.POST, instance=val)
    if form.is_valid():
        form.save()

    return get_manage_option_type_panel_partial(request, opt_type_pk)


@staff_member_required
def delete_option_value(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    val = get_object_or_404(ProductOptionValue, pk=pk)
    opt_type_pk = val.option_type_id
    val.delete()

    return get_manage_option_type_panel_partial(request, opt_type_pk)


@staff_member_required
def create_variant(request, product_pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    product = get_object_or_404(Product, pk=product_pk)
    form = ProductVariantForm(request.POST)
    if form.is_valid():
        variant = form.save(commit=False)
        variant.product = product
        variant.save()

    return get_manage_product_panel_partial(request, product_pk)


@staff_member_required
def delete_variant(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    variant = get_object_or_404(ProductVariant, pk=pk)
    product_pk = variant.product_id
    variant.delete()

    return get_manage_product_panel_partial(request, product_pk)


def get_merch_grid_partial(request):

    products = get_active_product_tree()

    return render(request, 'hr_shop/_merch_grid_partial.html', { 'products': products, })

    # active_option_values_qs = (
    # ProductOptionValue.objects
    # .filter(active=True, option_type__active=True, variants__active=True).select_related('option_type').distinct())
    #
    #
    # active_variants_qs = ( ProductVariant.objects.filter(active=True).prefetch_related(Prefetch('option_values', queryset=active_option_values_qs)
    #
    # active_option_types_qs = (
    #                        ProductOptionType.objects.filter(active=True, values__active=True, values__variants__active=True).prefetch_related(Prefetch('values', queryset=active_option_values_qs, to_attr='active values'))
    #                        )
    #
    # return (
    #     Product.objects
    #         .filter(active=True)
    #         .prefetch_related(Prefetch('variants', queryset=active_variants_qs, to_attr='active_variants'), Prefetch('option_types', queryset=active_option_types_qs, to_attr='active_option_types'),)) ))


def get_product_modal_partial(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    option_types = product.option_types.prefetch_related('values')
    display_variant = product.display_variant

    if display_variant:
        display_values = display_variant.option_values.select_related('option_type')

        # map each option type on the product to the option value related to the product's display variant
        mapping = {
            ov.option_type_id: ov.option_type_id for ov in display_values
        }

        for opt in option_types:
            setattr(opt, 'default_value_id', mapping.get(opt.id))

    context = {
        'product': product,
        'option_types': option_types,
        'display_variant': display_variant
    }

    return render(request, 'hr_shop/_product_detail_modal.html', context)


#
#
# def get_product_modal_partial(request, product_slug):
#     product = get_object_or_404(
#         Product.objects.filter(active=True).prefetch_related(
#             'variants__option_values__option_type',
#             'option_types__values'
#         ),
#         slug=product_slug
#     )
#
#     option_types = product.option_types.filter(active=True).order_by('position', 'id').prefetch_related('values')
#
#     variants = product.variants.filter(active=True).order_by('id')
#
#     return render(request, 'hr_shop/_product_detail_modal.html', {
#         'product': product,
#         'option_types': option_types,
#         'variants': variants
#     })


@login_required
def orders(request):
    qs = (Order.objects
          .filter(Q(email=request.user.email) | Q(user=request.user))
          .order_by('-created_at')
          .distinct())

    ctx = {
        "orders": qs[:20],
        "has_more": qs.count() > 20
    }

    template = "orders.html"
    if is_htmx(request):
        template = "_orders_modal.html"

    return render(request, f"account/{template}", ctx)


@login_required
def orders_page(request, n: int):
    per = 20
    start = (n-1)*per
    end = n*per

    qs = (Order.objects
          .filter(Q(email=request.user.email) | Q(user=request.user))
          .order_by('-created_at')
          .distinct())

    return render(request, "account/_orders_list_items.html", {
        "orders": qs[start:end],
        "has_more": qs.count() > end
    })


@login_required
def order_detail_modal(request, order_id: int):
    order = get_object_or_404(
        Order.objects.filter(Q(email=request.user.email) | Q(user=request.user)),
        pk=order_id
    )
    return render(request, "account/_order_detail_modal.html", {"order": order})



#========================================================================================================================================================#


# def clear_cart(request):
#     pass
#
#
# def product_gallery(request):
#     # import stripe
#     # stripe.api_key = stripe_test_private_key
#     #
#     # def get_all_stripe_objects(stripe_listable):
#     #     objects = []
#     #     get_more = True
#     #     starting_after = None
#     #     while get_more:
#     #         # stripe.Customer implements ListableAPIResource(APIResource):
#     #         resp = stripe_listable.list(limit=100, starting_after=starting_after)
#     #         objects.extend(resp['data'])
#     #         get_more = resp['has_more']
#     #         if len(resp['data']) > 0:
#     #             starting_after = resp['data'][-1]['id']
#     #     return objects
#     #
#     # all_stripe_products = get_all_stripe_objects(stripe.Product)
#     # all_stripe_prices = get_all_stripe_objects(stripe.Price)
#
#     cart = Cart(request)
#     # prices = stripe.Price.search(query="active:'true'", expand=['data.product'])  # product data is attainable by expansion on prices data, though not prices via product expansion
#     prices = stripe.Price.list(expand=['data.product'])
#     # log.info(msg=f'prices object in product_gallery = {prices}')
#     return render(request, 'hr_shop/product_gallery.html', {'prices': prices, 'cart': cart})
#
#
# def product_detail(request, encoded_name):
#     cart = Cart(request)
#     decoded_name = urllib.parse.unquote_plus(encoded_name)
#     product = stripe.Product.search(query=f"name:'{decoded_name}'", expand=['data.default_price'])
#     unit_price = float(product.default_price.unit_amount_decimal)/100
#     return render(request, 'hr_shop/product_detail.html', {'product': product, 'cart': cart, 'unit_price': unit_price})
#
#
# def cart_detail(request):
#     cart = Cart(request)
#     cart_items = cart.session.cart_items.all()
#     for item in cart_items:
#         item['quantity'] = cart_items[item.id]
#         item['subtotal'] = cart.get_item_subtotal(item.id)
#     cart.session.save()
#     return render (request, 'hr_shop/view_cart.html', {'cart_items': cart_items, 'cart': cart})
#
#
# def add_product(request, encoded_name, quantity=1):
#     cart = Cart(request)
#     decoded_name = urllib.parse.unquote_plus(encoded_name)
#     product = stripe.Product.search(query=f"name:'{decoded_name}'", expand=['data.default_price'])
#     result = cart.new_item(product_id=product.id, quantity=quantity)
#     messages.info(request, message=result)
#     response = redirect(request, 'product_gallery', {'cart': cart})
#     headers_dict = {'cartChanged': None}
#     response.headers['HX-Trigger'] = json.dumps(headers_dict)
#     return response
#
#
# def update_product(request, product_id, quantity=None, increment=False, decrement=False):
#     cart = Cart(request)
#     result = cart.update_item(product_id=product_id, quantity=quantity, increment=increment, decrement=decrement)
#     messages.info(request, message=result)
#     return redirect(request, 'cart_detail', {'cart': cart})
#
#
# def remove_product(request, product_id):
#     cart = Cart(request)
#     result = cart.delete_item(product_id=product_id)
#     messages.info(request, message=result)
#     return redirect(request, 'cart_detail', {'cart': cart})
#
#
# def checkout(request):
#     cart = Cart(request)
#     return redirect(request, 'payment_entry', {'cart': cart})
#
#
# def cart_counter(request):
#     cart = Cart(request)
#     item_count = cart.num_items()
#     return render(request, 'hr_shop/cart_counter.html', {'item_count': item_count})
