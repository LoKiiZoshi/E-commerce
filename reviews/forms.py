from django import forms
from .models import Review, ReviewImage

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(),
            'comment': forms.Textarea(attrs={'rows': 5}),
        }

class ReviewImageForm(forms.ModelForm):
    class Meta:
        model = ReviewImage
        fields = ['image']