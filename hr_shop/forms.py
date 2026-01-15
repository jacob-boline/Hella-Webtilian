# hr_shop/forms.py

import re

from django import forms
from phonenumber_field.formfields import PhoneNumberField

from hr_common.constants.us_states import US_STATES
from hr_common.models import BuildingType
from hr_core.utils.email import normalize_email
from hr_shop.models import Product, ProductVariant, ProductOptionType, ProductOptionValue, OptionTypeTemplate

ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")


class ProductAdminForm(forms.ModelForm):
    option_type_templates = forms.ModelMultipleChoiceField(
        queryset=OptionTypeTemplate.objects.filter(active=True),
        required=False,
        label="Apply option templates",
        help_text="[Select reusable option types to clone onto this product.]"
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
    email = forms.EmailField(
        required=True,
        label='Email')
    phone = PhoneNumberField(
        required=False,
        label='Phone',
        region='US')
    first_name = forms.CharField(
        required=True,
        max_length=100,
        label='First Name')
    middle_initial = forms.CharField(
        required=False,
        max_length=5,
        label='Middle Initial')
    last_name = forms.CharField(
        required=True,
        max_length=100,
        label="Last Name")
    suffix = forms.CharField(
        required=False,
        max_length=20,
        label="Suffix")
    street_address = forms.CharField(
        required=True,
        max_length=255,
        label='Street Address')
    street_address_line2 = forms.CharField(
        required=False,
        max_length=255,
        label='Street Address Line 2')
    building_type = forms.ChoiceField(
        required=True,
        choices=BuildingType.choices,
        label='Building Type')
    unit = forms.CharField(
        required=False,
        max_length=64,
        label='Apt/Office/Unit')
    city = forms.CharField(
        required=True,
        max_length=255,
        label='City')
    subdivision = forms.ChoiceField(
        required=True,
        choices=US_STATES,
        label='State')
    postal_code = forms.CharField(
        required=True,
        max_length=25,
        label='Zip Code')
    note = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={'rows': 6}),
        label='Note')
    save_info_for_next_time = forms.BooleanField(
        required=False,
        initial=False,
        label='Save info for faster checkouts in the future')

    def clean(self):
        cleaned = super().clean()
        bt = cleaned.get('building_type')
        unit = (cleaned.get('unit') or '').strip()

        needs_unit = bt in ('apartment',)

        if needs_unit and not unit:
            self.add_error('unit', 'Unit is required for this building type.')
        return cleaned

    def clean_email(self):
        email = self.cleaned_data['email']
        return normalize_email(email)

    def clean_postal_code(self):
        z = (self.cleaned_data['postal_code'] or "").strip()
        if not ZIP_RE.match(z):
            raise forms.ValidationError('Enter a valid ZIP code.')
        return z
