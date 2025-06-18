from django.urls import path
from . import views

urlpatterns = [
    path('methods/', views.payment_methods, name='payment_methods'),
    path('esewa/<int:order_id>/', views.esewa_payment, name='esewa_payment'),
    path('esewa-success/<int:payment_id>/', views.esewa_success, name='esewa_success'),
    path('esewa-failure/<int:payment_id>/', views.esewa_failure, name='esewa_failure'),
    path('history/', views.payment_history, name='payment_history'),
    path('detail/<int:payment_id>/', views.payment_detail, name='payment_detail'),
]