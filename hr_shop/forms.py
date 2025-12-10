# hr_shop/forms.py

from django import forms
from hr_shop.models import Product, ProductVariant, ProductOptionType, ProductOptionValue, OptionTypeTemplate


class ProductAdminForm(forms.ModelForm):
    option_type_templates = forms.ModelMultipleChoiceField(
        queryset=OptionTypeTemplate.objects.filter(active=True),
        required=False,
        label="Apply option templates",
        help_text="[Select reusable option types to clone onto this product."
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def label_from_instance(obj: ProductOptionType):
            values = obj.values.order_by('position', 'id').values_list('name', flat=True)
            values_list = ", ".join(values)
            if values_list:
                return f'{obj.name} ({values_list})'
            return obj.name

        self.fields['option_type_templates'].label_from_instance = label_from_instance

    def save(self, commit=True):
        is_new = self.instance.pk is None
        product = super().save(commit=commit)

        templates = self.cleaned_data.get('option_type_templates')
        if commit and templates and is_new:
            for tmpl in templates:
                tmpl.clone_to_product(product, include_values=True)

        return product


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
        fields = ['sku', 'name', 'price', 'is_display_variant']


class CheckoutForm(forms.Form):
    pass