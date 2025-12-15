# hr_shop/forms.py

from django import forms
from hr_shop.models import Product, ProductVariant, ProductOptionType, ProductOptionValue, OptionTypeTemplate
from hr_common.models import BuildingType


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


class CheckoutDetailsForm(forms.Form):

    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(required=False, max_length=50, label='Phone')

    first_name = forms.CharField(required=True, max_length=100, label='First Name')
    middle_initial = forms.CharField(required=False, max_length=5, label='Middle Initial')
    last_name = forms.CharField(required=True, max_length=100, label="Last Name")
    suffix = forms.CharField(required=False, max_length=20, label="Suffix")

    street_address = forms.CharField(required=True, max_length=255, label='Street Address')
    street_address_line2 = forms.CharField(required=False, max_length=255, label='Street Address Line 2')

    building_type = forms.ChoiceField(required=True, choices=BuildingType.choices, label='Building Type')
    unit = forms.CharField(required=False, max_length=64, label='Apt/Office/Unit')

    city = forms.CharField(required=True, max_length=255, label='City')
    subdivision = forms.CharField(required=True, max_length=100, label='State')
    postal_code = forms.CharField(required=True, max_length=25, label='Zip Code')

    note = forms.CharField(required=False, max_length=1000, widget=forms.Textarea(attrs={'rows': 5}), label='Note')
