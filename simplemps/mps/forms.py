from django import forms

from .models import AccountSetting, Client, ServiceLevel, Company

from jsignature.forms import JSignatureField
from jsignature.widgets import JSignatureWidget

class UploadForm(forms.Form):
    # title = forms.CharField(max/_length=50)
    file = forms.FileField()


class AccountSettingForm(forms.ModelForm):
    co_branding_logo = forms.ImageField(required=False)
    logo = forms.ImageField(required=False)
    class Meta:
        model = AccountSetting
        exclude = ['company']


class SignatureForm(forms.Form):
    signature = JSignatureField()

class ClientForm (forms.ModelForm):

    contract_types = [
        (True, 'Supplies'),
        (False, 'Supplies and Service')
    ]
    
    pricing_types = [
        (True, 'Pricing Per Page'),
        (False, 'Pricing Per Cartridge')
    ]

    rep_company = forms.ModelChoiceField(queryset=Company.objects.all(), empty_label="-- Select Company --", label="Representative", required=False)
    recurring_client = forms.ModelChoiceField(queryset=Client.objects.all().distinct('organization_name'), empty_label="-- Select Client --", required=False)
    is_supplies_only = forms.ChoiceField(widget=forms.RadioSelect, choices=contract_types, initial=contract_types[0])
    is_pricing_per_page = forms.ChoiceField(widget=forms.RadioSelect, choices=pricing_types, initial=pricing_types[1])
    contract_service_levels = forms.ModelChoiceField(queryset=ServiceLevel.objects.all(), empty_label="-- Select Service Level --", required=False)
    
    class Meta:
        model = Client
        fields = ['organization_name', 'contact', 'email', 'phone_number', 'city', 'state', 'zipcode','country','rep_company']
        