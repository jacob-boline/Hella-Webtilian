# hr_shop/views/manage.py

import logging
from logging import getLogger

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from hr_common.utils.unified_logging import log_event
from hr_shop.forms import (
    ProductEditForm,
    ProductOptionTypeForm,
    ProductOptionValueForm,
    ProductQuickForm,
    ProductVariantForm
)
from hr_shop.models import Product, ProductOptionType, ProductOptionValue, ProductVariant

logger = getLogger()


def _render_product_list(request, form=None):
    products = Product.objects.all().order_by('name')
    return render(
        request,
        'hr_shop/manage/_pm_product_list.html',
        {
            'products': products,
            'form': form or ProductQuickForm()
        }
    )


def _render_product_panel(
    request,
    product,
    *,
    product_form=None,
    variant_form=None,
    option_type_form=None,
    variant_form_overrides=None,
    reset_option_type_panel=False
):
    option_types = product.option_types.all().order_by('position', 'id')
    variants = (
        product.variants.all()
        .order_by('id')
        .prefetch_related('variant_options__option_value__option_type')
    )

    variant_forms = []
    for variant in variants:
        form_override = None
        if variant_form_overrides:
            form_override = variant_form_overrides.get(variant.pk)
        variant_forms.append(
            (
                variant,
                form_override or ProductVariantForm(instance=variant)
            )
        )

    return render(
        request,
        'hr_shop/manage/_pm_product_panel_partial.html',
        {
            'product': product,
            'option_types': option_types,
            'variants': variants,
            'variant_forms': variant_forms,
            'product_form': product_form or ProductEditForm(instance=product),
            'variant_form': variant_form or ProductVariantForm(),
            'option_type_form': option_type_form or ProductOptionTypeForm(),
            # Reset the option type panel whenever the product changes.
            'reset_option_type_panel': reset_option_type_panel
        }
    )


def _render_option_type_panel(
    request,
    option_type,
    *,
    option_type_form=None,
    value_form=None,
    value_forms=None
):
    values = option_type.values.all().order_by('position', 'id')

    if value_forms is None:
        value_forms = [
            (val, ProductOptionValueForm(instance=val))
            for val in values
        ]

    return render(
        request,
        'hr_shop/manage/_pm_option_type_panel_partial.html',
        {
            'option_type': option_type,
            'values': values,
            'option_type_form': option_type_form or ProductOptionTypeForm(instance=option_type),
            'values_with_forms': value_forms,
            'value_form': value_form or ProductOptionValueForm()
        }
    )


@staff_member_required
def product_manager(request):
    """
    Main management UI shell. HTMX fills product list, product panel, and option type panel.
    """
    return render(request, 'hr_shop/manage/manage_products.html')


@staff_member_required
def get_manage_product_panel_partial(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related('variants', 'option_types__values'),
        pk=pk
    )
    return _render_product_panel(request, product, reset_option_type_panel=True)


@staff_member_required
def get_manage_product_list_partial(request):
    return _render_product_list(request)


@staff_member_required
def get_manage_option_type_panel_partial(request, pk):
    opt_type = get_object_or_404(
        ProductOptionType.objects.prefetch_related('values', 'product'),
        pk=pk
    )
    return _render_option_type_panel(request, opt_type)


@staff_member_required
def create_product(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    form = ProductQuickForm(request.POST)
    if form.is_valid():
        product = form.save()
        log_event(
            logger,
            logging.INFO,
            "manage.product.created",
            user_id=request.user.id if request.user.is_authenticated else None,
            product_id=product.id,
        )
        form = ProductQuickForm()

    return _render_product_list(request, form=form)


@staff_member_required
def update_product(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    product = get_object_or_404(Product, pk=pk)
    form = ProductEditForm(request.POST, instance=product)
    if form.is_valid():
        form.save()
        log_event(
            logger,
            logging.INFO,
            "manage.product.updated",
            user_id=request.user.id if request.user.is_authenticated else None,
            product_id=product.id,
        )
        return _render_product_panel(request, product)

    return _render_product_panel(request, product, product_form=form)


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
        log_event(
            logger,
            logging.INFO,
            "manage.option_type.created",
            user_id=request.user.id if request.user.is_authenticated else None,
            product_id=product.id,
            option_type_id=opt_type.id,
        )

    return _render_product_panel(request, product, option_type_form=form)


@staff_member_required
def update_option_type(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    opt_type = get_object_or_404(ProductOptionType, pk=pk)
    form = ProductOptionTypeForm(request.POST, instance=opt_type)
    if form.is_valid():
        form.save()
        log_event(
            logger,
            logging.INFO,
            "manage.option_type.updated",
            user_id=request.user.id if request.user.is_authenticated else None,
            option_type_id=opt_type.id,
            product_id=opt_type.product_id,
        )
        return _render_option_type_panel(request, opt_type)

    return _render_option_type_panel(request, opt_type, option_type_form=form)


@staff_member_required
def delete_option_type(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    opt_type = get_object_or_404(ProductOptionType, pk=pk)
    product_pk = opt_type.product_id
    option_type_id = opt_type.id
    opt_type.delete()
    log_event(
        logger,
        logging.INFO,
        "manage.option_type.deleted",
        user_id=request.user.id if request.user.is_authenticated else None,
        option_type_id=option_type_id,
        product_id=product_pk,
    )

    product = get_object_or_404(Product, pk=product_pk)
    return _render_product_panel(request, product, reset_option_type_panel=True)


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
        log_event(
            logger,
            logging.INFO,
            "manage.option_value.created",
            user_id=request.user.id if request.user.is_authenticated else None,
            option_type_id=opt_type.id,
            option_value_id=value.id,
        )

    return _render_option_type_panel(request, opt_type, value_form=form)


@staff_member_required
def update_option_value(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    val = get_object_or_404(ProductOptionValue, pk=pk)
    form = ProductOptionValueForm(request.POST, instance=val)
    if form.is_valid():
        form.save()
        log_event(
            logger,
            logging.INFO,
            "manage.option_value.updated",
            user_id=request.user.id if request.user.is_authenticated else None,
            option_value_id=val.id,
            option_type_id=val.option_type_id,
        )
        return _render_option_type_panel(request, val.option_type)

    option_type = get_object_or_404(ProductOptionType, pk=val.option_type_id)
    value_forms = [(val, form)] + [
        (v, ProductOptionValueForm(instance=v))
        for v in option_type.values.exclude(pk=val.pk).order_by('position', 'id')
    ]
    return _render_option_type_panel(
        request,
        option_type,
        value_forms=value_forms
    )


@staff_member_required
def delete_option_value(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    val = get_object_or_404(ProductOptionValue, pk=pk)
    opt_type_pk = val.option_type_id
    option_value_id = val.id
    val.delete()
    log_event(
        logger,
        logging.INFO,
        "manage.option_value.deleted",
        user_id=request.user.id if request.user.is_authenticated else None,
        option_value_id=option_value_id,
        option_type_id=opt_type_pk,
    )

    opt_type = get_object_or_404(ProductOptionType, pk=opt_type_pk)
    return _render_option_type_panel(request, opt_type)


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
        log_event(
            logger,
            logging.INFO,
            "manage.variant.created",
            user_id=request.user.id if request.user.is_authenticated else None,
            product_id=product.id,
            variant_id=variant.id,
        )

    return _render_product_panel(request, product, variant_form=form)


@staff_member_required
def update_variant(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    variant = get_object_or_404(ProductVariant.objects.select_related('product'), pk=pk)
    product = variant.product
    form = ProductVariantForm(request.POST, instance=variant)
    if form.is_valid():
        form.save()
        log_event(
            logger,
            logging.INFO,
            "manage.variant.updated",
            user_id=request.user.id if request.user.is_authenticated else None,
            product_id=product.id,
            variant_id=variant.id,
        )
        return _render_product_panel(request, product)

    return _render_product_panel(
        request,
        product,
        variant_form_overrides={variant.pk: form}
    )


@staff_member_required
def delete_variant(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    variant = get_object_or_404(ProductVariant, pk=pk)
    product_pk = variant.product_id
    variant_id = variant.id
    variant.delete()
    log_event(
        logger,
        logging.INFO,
        "manage.variant.deleted",
        user_id=request.user.id if request.user.is_authenticated else None,
        product_id=product_pk,
        variant_id=variant_id,
    )

    product = get_object_or_404(Product, pk=product_pk)
    return _render_product_panel(request, product)
