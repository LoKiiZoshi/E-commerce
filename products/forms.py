from django import forms
from .models import Product, ProductImage, Category, ProductSpecification, ProductTag

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'parent']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'discount_price', 'category', 
                  'stock', 'is_available', 'is_featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'discount_price': forms.NumberInput(attrs={'step': '0.01'}),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary']

class ProductSpecificationForm(forms.ModelForm):
    class Meta:
        model = ProductSpecification
        fields = ['name', 'value']

class ProductTagForm(forms.ModelForm):
    class Meta:
        model = ProductTag
        fields = ['name']