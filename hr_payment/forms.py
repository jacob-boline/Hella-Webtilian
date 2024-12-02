import pycountry
from django import forms


class TitleChoices:
    MR = 'Mr.'
    MRS = 'Mrs.'
    MS = 'Ms.'
    PROF = 'Prof.'
    REV = 'Rev.'
    SR = 'Sr.'
    ST = 'St.'
    JR = 'Jr.'
    DR = 'Dr.'
    ESQ = 'Esq'
    HON = 'Hon.'
    RTHON = 'Rt. Hon.'
    MSGR = 'Msgr.'
    SIR = 'Sir'
    MDM = 'Madam'


class SuffixChoices:
    JR = 'Jr.'
    SR = 'Sr.'
    SCND = '2nd'
    THRD = '3rd'
    FRTH = '4th'
    FFTH = '5th'
    II = 'II'
    III = 'III'
    IV = 'IV'
    V = 'V'
    VI = 'VI'
    VII = 'VII'


class PrePaymentEntryForm(forms.Form):
    title = forms.ChoiceField(label='Title', required=False, choices=TitleChoices)
    suffix = forms.ChoiceField(label='Suffix', required=False, choices=SuffixChoices)
    first_name = forms.CharField(label='First Name', max_length=50, required=True)
    last_name = forms.CharField(label='Last Name', max_length=100, required=True)
    email_1 = forms.EmailField(label='Email', min_length=6, max_length=100, required=True)
    email_2 = forms.EmailField(label='Confirm Email', min_length=6, max_length=100, required=True)
    street_address = forms.CharField(min_length=3, max_length=100, required=True)
    unit = forms.CharField(min_length=1, max_length=30, required=False)
    city = forms.CharField(min_length=2, max_length=100, required=True)
    subdivision = forms.CharField(min_length=2, max_length=100, required=True)
    index = forms.CharField(min_length=1, max_length=30, required=True)
    country_code = forms.ChoiceField(choices=[(country.alpha_2, country.name) for country in pycountry.countries],
                                     required=True)

    def confirmed_email(self):
        pass

    def extract_address(self):
        pass

    def compile_name(self):
        return f"{self.cleaned_data['title'] or None} {self.cleaned_data['first_name']} {self.cleaned_data['last_name']} {self.cleaned_data['suffix'] or None}"


class PaymentEntryForm(forms.Form):
    pass