# hr_shop/admin.py

from django.contrib import admin
from .models import Product, ProductVariant, ProductOptionType, ProductOptionValue


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'active')
    list_editable = ('active',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'slug', 'sku', 'price', 'active')
    list_editable = ('name', 'sku', 'price', 'active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductOptionType)
class ProductOptionT9ypeAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'code', 'position', 'active')
    list_editable = ('name', 'code', 'position', 'active')
    list_display_links = ('product',)


@admin.register(ProductOptionValue)
class ProductOptionValue(admin.ModelAdmin):
    list_display = ('option_type', 'name', 'code', 'position')
    list_editable = ('name', 'code', 'position')
    list_display_links = ('option_type',)
