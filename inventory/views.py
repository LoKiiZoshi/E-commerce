from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from django.db.models.functions import Cast
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta

from .models import InventoryRecord, StockMovement, InventoryForecast, Supplier, PurchaseOrder, PurchaseOrderItem
from .forms import StockMovementForm, SupplierForm, PurchaseOrderForm, PurchaseOrderItemForm
from products.models import Product
from orders.models import OrderItem  
def is_admin_user(user):
    return user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'ADMIN'

@login_required 
@user_passes_test(is_admin_user)
def inventory_dashboard(request):
    # Get low stock products
    low_stock_products = Product.objects.filter(stock__lt=F('id') % 10 + 5)  # Just for demo
    
    # Get recent stock movements
    recent_movements = StockMovement.objects.all().select_related('product', 'created_by')[:10]
    
    # Get upcoming purchase orders
    upcoming_orders = PurchaseOrder.objects.filter(
        status__in=['approved', 'ordered'],
        expected_delivery_date__gte=datetime.now().date()
    ).select_related('supplier')[:5]
                                                                 
    context = {
        'low_stock_products': low_stock_products,  
        'recent_movements': recent_movements,
        'upcoming_orders': upcoming_orders,
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
@user_passes_test(is_admin_user)
def product_inventory(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Get inventory records
    inventory_records = InventoryRecord.objects.filter(product=product)
    
    # Get stock movements
    stock_movements = StockMovement.objects.filter(product=product)
    
    # Get inventory forecasts
    inventory_forecasts = InventoryForecast.objects.filter(product=product)
    
    context = {
        'product': product,
        'inventory_records': inventory_records,
        'stock_movements': stock_movements,
        'inventory_forecasts': inventory_forecasts,
    }
    return render(request, 'inventory/product_inventory.html', context)

@login_required
@user_passes_test(is_admin_user)
def add_stock_movement(request, product_id=None):
    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.created_by = request.user
            movement.save()
            
            # Update product stock
            product = movement.product
            if movement.movement_type == 'in':
                product.stock += movement.quantity
            elif movement.movement_type == 'out':
                product.stock -= movement.quantity
            else:  # adjustment
                product.stock = movement.quantity
            
            product.save()
            
            # Create inventory record
            InventoryRecord.objects.create(
                product=product,
                quantity=product.stock
            )
            
            messages.success(request, 'Stock movement added successfully.')
            return redirect('product_inventory', product_id=product.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial_data = {}
        if product:
            initial_data['product'] = product
        
        form = StockMovementForm(initial=initial_data)
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'inventory/stock_movement_form.html', context)

@login_required
@user_passes_test(is_admin_user)
def generate_inventory_forecast(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Get historical data
    inventory_records = InventoryRecord.objects.filter(product=product).order_by('created_at')
    order_items = OrderItem.objects.filter(product=product).order_by('order__created_at')
    
    if not inventory_records or not order_items:
        messages.warning(request, 'Not enough historical data to generate forecast.')
        return redirect('product_inventory', product_id=product.id)
    
    try:
        # Prepare data for time series analysis
        dates = []
        quantities = []
        
        for item in order_items:
            dates.append(item.order.created_at.date())
            quantities.append(item.quantity)
        
        # Create DataFrame
        df = pd.DataFrame({
            'date': dates,
            'quantity': quantities
        })
        
        # Aggregate by date
        df = df.groupby('date').sum().reset_index()
        
        # Sort by date
        df = df.sort_values('date')
        
        # Fill missing dates with 0
        date_range = pd.date_range(start=df['date'].min(), end=df['date'].max())
        df = df.set_index('date').reindex(date_range, fill_value=0).reset_index()
        df = df.rename(columns={'index': 'date'})
        
        # Fit ARIMA model
        model = ARIMA(df['quantity'], order=(5,1,0))
        model_fit = model.fit()
        
        # Forecast next 30 days
        forecast = model_fit.forecast(steps=30)
        
        # Save forecasts
        for i, pred in enumerate(forecast):
            forecast_date = datetime.now().date() + timedelta(days=i+1)
            
            # Ensure prediction is not negative
            predicted_demand = max(0, pred)
            
            InventoryForecast.objects.update_or_create(
                product=product,
                forecast_date=forecast_date,
                defaults={
                    'predicted_demand': predicted_demand,
                    'confidence_level': 0.8  # Placeholder
                }
            )
        
        messages.success(request, 'Inventory forecast generated successfully.')
    except Exception as e:
        messages.error(request, f'Error generating forecast: {str(e)}')
    
    return redirect('product_inventory', product_id=product.id)

@login_required
@user_passes_test(is_admin_user)
def supplier_list(request):
    suppliers = Supplier.objects.all()
    
    context = {
        'suppliers': suppliers,
    }
    return render(request, 'inventory/supplier_list.html', context)

@login_required
@user_passes_test(is_admin_user)
def add_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier added successfully.')
            return redirect('supplier_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierForm()
    
    context = {
        'form': form,
    }
    return render(request, 'inventory/supplier_form.html', context)

@login_required
@user_passes_test(is_admin_user)
def edit_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated successfully.')
            return redirect('supplier_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierForm(instance=supplier)
    
    context = {
        'form': form,
        'supplier': supplier,
    }
    return render(request, 'inventory/supplier_form.html', context)

@login_required
@user_passes_test(is_admin_user)
def purchase_order_list(request):
    purchase_orders = PurchaseOrder.objects.all().select_related('supplier')
    
    context = {
        'purchase_orders': purchase_orders,
    }
    return render(request, 'inventory/purchase_order_list.html', context)

@login_required
@user_passes_test(is_admin_user)
def purchase_order_detail(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    
    context = {
        'purchase_order': purchase_order,
    }
    return render(request, 'inventory/purchase_order_detail.html', context)

@login_required
@user_passes_test(is_admin_user)
def add_purchase_order(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            purchase_order = form.save(commit=False)
            purchase_order.created_by = request.user
            purchase_order.save()
            
            messages.success(request, 'Purchase order created successfully.')
            return redirect('purchase_order_detail', po_id=purchase_order.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseOrderForm(initial={'order_date': datetime.now().date()})
    
    context = {
        'form': form,
    }
    return render(request, 'inventory/purchase_order_form.html', context)

@login_required
@user_passes_test(is_admin_user)
def add_purchase_order_item(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    
    if request.method == 'POST':
        form = PurchaseOrderItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.purchase_order = purchase_order
            item.save()
            
            # Update purchase order total
            purchase_order.total_amount += item.get_total_price()
            purchase_order.save()
            
            messages.success(request, 'Item added to purchase order.')
            return redirect('purchase_order_detail', po_id=purchase_order.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseOrderItemForm()
    
    context = {
        'form': form,
        'purchase_order': purchase_order,
    }
    return render(request, 'inventory/purchase_order_item_form.html', context)

@login_required
@user_passes_test(is_admin_user)
def update_purchase_order_status(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(PurchaseOrder.STATUS_CHOICES):
            purchase_order.status = status
            purchase_order.save()
            
            messages.success(request, 'Purchase order status updated.')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('purchase_order_detail', po_id=purchase_order.id)

@login_required
@user_passes_test(is_admin_user)
def receive_purchase_order(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    
    if request.method == 'POST':
        for item in purchase_order.items.all():
            received_quantity = int(request.POST.get(f'received_quantity_{item.id}', 0))
            
            if received_quantity > 0:
                # Update received quantity
                item.received_quantity += received_quantity
                item.save()
                
                # Update product stock
                product = item.product
                product.stock += received_quantity
                product.save()
                
                # Create stock movement
                StockMovement.objects.create(
                    product=product,
                    quantity=received_quantity,
                    movement_type='in',
                    reference=f'PO-{purchase_order.id}',
                    created_by=request.user
                )
                
                # Create inventory record
                InventoryRecord.objects.create(
                    product=product,
                    quantity=product.stock
                )
        
        # Update purchase order status
        all_received = all(item.received_quantity >= item.quantity for item in purchase_order.items.all())
        if all_received:
            purchase_order.status = 'received'
        else:
            purchase_order.status = 'ordered'
        
        purchase_order.save()
        
        messages.success(request, 'Purchase order items received.')
    
    return redirect('purchase_order_detail', po_id=purchase_order.id)