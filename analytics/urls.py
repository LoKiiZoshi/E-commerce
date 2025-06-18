from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('record-page-view/', views.record_page_view, name='record_page_view'),
    path('record-product-view/<int:product_id>/', views.record_product_view, name='record_product_view'),
    path('record-search-query/', views.record_search_query, name='record_search_query'),
]