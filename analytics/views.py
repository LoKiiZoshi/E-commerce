from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, F, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.utils import timezone
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

from .models import PageView, ProductView, SearchQuery, SalesReport, ProductPerformance, CategoryPerformance
from orders.models import Order, OrderItem
from products.models import Product, Category

def is_staff(user):
    return user.is_staff or user.is_superuser

def record_page_view(request):
    # Don't record admin page views
    if request.path.startswith('/admin/'):
        return JsonResponse({'success': True})
    
    # Get user or session ID
    user = request.user if request.user.is_authenticated else None
    session_id = request.session.session_key
    
    # Create page view record
    PageView.objects.create(
        user=user,
        session_id=session_id,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        path=request.path,
        referrer=request.META.get('HTTP_REFERER')
    )
    
    return JsonResponse({'success': True})

def record_product_view(request, product_id):
    # Get user or session ID
    user = request.user if request.user.is_authenticated else None
    session_id = request.session.session_key
    
    # Create product view record
    ProductView.objects.create(
        user=user,
        session_id=session_id,
        product_id=product_id
    )
    
    # Update product performance
    performance, created = ProductPerformance.objects.get_or_create(product_id=product_id)
    performance.views += 1
    
    # Calculate conversion rate
    if performance.views > 0:
        performance.conversion_rate = (performance.purchase_count / performance.views) * 100
    
    performance.save()
    
    return JsonResponse({'success': True})

def record_search_query(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        results_count = int(request.POST.get('results_count', 0))
        
        # Get user or session ID
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key
        
        # Create search query record
        SearchQuery.objects.create(
            user=user,
            session_id=session_id,
            query=query,
            results_count=results_count
        )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@user_passes_test(is_staff)
def analytics_dashboard(request):
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    date_range = request.GET.get('date_range', '30')
    if date_range == '7':
        start_date = end_date - timedelta(days=7)
    elif date_range == '90':
        start_date = end_date - timedelta(days=90)
    elif date_range == '365':
        start_date = end_date - timedelta(days=365)
    
    # Get sales data
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    total_sales = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders = orders.count()
    average_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    # Get