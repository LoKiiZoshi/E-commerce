from django import forms
from .models import Order, ShippingMethod

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'phone', 'address', 'city', 'country', 'postal_code', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Special instructions for delivery'}),
        }

class ShippingForm(forms.Form):
    shipping_method = forms.ModelChoiceField(
        queryset=ShippingMethod.objects.filter(is_active=True),
        empty_label=None,
        widget=forms.RadioSelect
    )