from django import forms
from .models import Payment

class PaymentMethodForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect
    )