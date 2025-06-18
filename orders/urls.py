from django.urls import path 
from orders.views import*     

urlpatterns = [
    path('checkout/', checkout, name='checkout'),
    path('my-orders/', order_list, name='order_list'),
    path('order/<int:order_id>/',order_detail, name='order_detail'),
    path('payment-process/<int:order_id>/', payment_process, name='payment_process'),
    path('payment-success/<int:order_id>/', payment_success, name='payment_success'),
    path('payment-failure/<int:order_id>/', payment_failure, name='payment_failure'),
    path('cancel-order/<int:order_id>/', cancel_order, name='cancel_order'),
]   