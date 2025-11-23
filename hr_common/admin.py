# hr_common/admin.py

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from hr_common.models import Address


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_editable = ("street_address", "city", "subdivision", "postal_code", "country")
    list_filter = ("city", "subdivision", "postal_code", "country")
    list_display = ("id", "street_address", "city", "subdivision", "postal_code", "country")
    list_display_links = ("id",)
