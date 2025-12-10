from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from hr_shop.forms import ProductVariantForm, ProductOptionValueForm, ProductOptionTypeForm, ProductEditForm, ProductQuickForm
from hr_shop.models import ProductVariant, Product, ProductOptionValue, ProductOptionType


@staff_member_required
def product_manager(request):
    """
    Main management UI shell. HTMX fills product list, product panel, and option type panel.
    """
    return render(request, 'hr_shop/manage_products.html')


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
def update_product(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    product = get_object_or_404(Product, pk=pk)
    form = ProductEditForm(request.POST, instance=product)
    if form.is_valid():
        form.save()

    return get_manage_product_panel_partial(request, pk)


# ------------------- OPTION TYPE ---------------------- #
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


# ------------------ OPTION VALUE ----------------------- #
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


# ---------------------- VARIANT ------------------------ #
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
