from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_recommendations, name='user_recommendations'),
    path('record-view/<int:product_id>/', views.record_product_view, name='record_product_view'),
    path('generate/', views.generate_recommendations, name='generate_recommendations'),
]