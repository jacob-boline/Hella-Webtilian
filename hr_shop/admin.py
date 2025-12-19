# hr_shop/admin.py

from django.contrib import admin
from hr_shop.models import (
    Product,
    ProductVariant,
    ProductOptionType,
    ProductOptionValue,
    OptionTypeTemplate,
    ConfirmedEmail,
    Customer,
    Order,
    OrderItem
)
from hr_shop.forms import ProductAdminForm


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'active')
    list_editable = ('active',)
    prepopulated_fields = {'slug': ('name',)}
    form = ProductAdminForm


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
class ProductOptionValueAdmin(admin.ModelAdmin):
    list_display = ('option_type', 'name', 'code', 'position')
    list_editable = ('name', 'code', 'position')
    list_display_links = ('option_type',)


@admin.register(ConfirmedEmail)
class ConfirmedEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'confirmed_at')
    search_fields = ('email',)
    readonly_fields = ('confirmed_at',)
    ordering = ('-confirmed_at',)
    date_hierarchy = 'confirmed_at'

    actions = ['confirm_selected']

    @admin.action(description="Manually confirm selected emails")
    def confirm_selected(self, request, queryset):
        pass

    def has_add_permission(self, request):
        """Allow manual addition of confirmed emails."""
        return True

    def has_change_permission(self, request, obj=None):
        """Don't allow editing - just view or delete."""
        return False


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'middle_initial', 'last_name', 'phone', 'user', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('variant', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'email', 'status', 'total', 'created_at')
    list_display_links = ('customer',)
    list_filter = ('status', 'created_at')
    search_fields = ('email', 'customer__email', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('created_at', 'updated_at', 'stripe_checkout_session_id')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    inlines = (OrderItemInline,)
