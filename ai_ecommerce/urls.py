from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('products/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('recommendations/', include('recommendations.urls')),
    path('inventory/', include('inventory.urls')),
    path('reviews/', include('reviews.urls')),
    path('analytics/', include('analytics.urls')),
    path('', include('products.urls')),  # Default to products app for homepage
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)