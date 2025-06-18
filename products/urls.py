from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<slug:slug>/', views.edit_product, name='edit_product'),
    path('delete-product/<slug:slug>/', views.delete_product, name='delete_product'),
    path('add-product-image/<int:product_id>/', views.add_product_image, name='add_product_image'),
    path('generate-product-content/', views.generate_product_content, name='generate_product_content'),
]