# hr_shop/admin.py

from django.contrib import admin
from .models import Product, ProductVariant


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'slug', 'sku', 'price')
    prepopulated_fields = {'slug': ('name',)}
