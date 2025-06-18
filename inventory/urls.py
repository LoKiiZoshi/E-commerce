from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_dashboard, name='inventory_dashboard'), 
    path('product/<int:product_id>/', views.product_inventory, name='product_inventory'),
    path('add-stock-movement/', views.add_stock_movement, name='add_stock_movement'),
    path('add-stock-movement/<int:product_id>/', views.add_stock_movement, name='add_stock_movement_for_product'),
    path('generate-forecast/<int:product_id>/', views.generate_inventory_forecast, name='generate_inventory_forecast'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('add-supplier/', views.add_supplier, name='add_supplier'),
    path('edit-supplier/<int:supplier_id>/', views.edit_supplier, name='edit_supplier'),
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-order/<int:po_id>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('add-purchase-order/', views.add_purchase_order, name='add_purchase_order'),
    path('add-purchase-order-item/<int:po_id>/', views.add_purchase_order_item, name='add_purchase_order_item'),
    path('update-purchase-order-status/<int:po_id>/', views.update_purchase_order_status, name='update_purchase_order_status'),
    path('receive-purchase-order/<int:po_id>/', views.receive_purchase_order, name='receive_purchase_order'),
]