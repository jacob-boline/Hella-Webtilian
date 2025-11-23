# hr_shop/forms.py

from django import forms
from hr_shop.models import Product, ProductVariant, ProductOptionType, ProductOptionValue


class ProductQuickForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name']


class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'slug', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProductOptionTypeForm(forms.ModelForm):
    class Meta:
        model = ProductOptionType
        fields = ['name', 'code', 'position']


class ProductOptionValueForm(forms.ModelForm):
    class Meta:
        model = ProductOptionValue
        fields = ['name', 'code', 'position']


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['sku', 'name', 'price', 'is_primary']
