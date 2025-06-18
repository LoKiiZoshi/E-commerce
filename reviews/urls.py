from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:product_id>/', views.add_review, name='add_review'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('delete-image/<int:image_id>/', views.delete_review_image, name='delete_review_image'),
    path('vote/<int:review_id>/', views.vote_review, name='vote_review'),
    path('analyze-sentiment/<int:product_id>/', views.analyze_sentiment, name='analyze_sentiment'),
]