from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
import json
import requests
import datetime

from .models import Order, OrderItem, ShippingMethod
from .forms import OrderForm, ShippingForm 
from cart.models import Cart
from products.models import Product
from recommendations.models import PurchaseHistory

@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    
    if not cart or cart.items.count() == 0:
        messages.warning(request, "Your cart is empty. Please add some products before checkout.")
        return redirect('cart_detail')
    
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    
    initial_data = {
        'full_name': request.user.get_full_name(),
        'email': request.user.email,
        'phone': request.user.phone_number,
        'address': request.user.address,
        'city': request.user.city,
        'country': request.user.country,
        'postal_code': request.user.postal_code,
    }
    
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        shipping_form = ShippingForm(request.POST)
        
        if order_form.is_valid() and shipping_form.is_valid():
            # Create the order
            order = order_form.save(commit=False)
            order.user = request.user
            
            # Set shipping cost
            shipping_method_id = shipping_form.cleaned_data.get('shipping_method')
            shipping_method = ShippingMethod.objects.get(id=shipping_method_id)
            order.shipping_cost = shipping_method.price
            
            # Calculate total price
            subtotal = sum(item.get_total_price() for item in cart.items.all())
            order.total_price = subtotal + shipping_method.price
            
            # Set payment method
            order.payment_method = 'eSewa'  # Default to eSewa for this example
            
            order.save()
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    price=cart_item.product.get_final_price(),
                    quantity=cart_item.quantity
                )
                
                # Update product stock
                product = cart_item.product
                product.stock -= cart_item.quantity
                product.save()
                
                # Record purchase history for recommendations
                PurchaseHistory.objects.create(
                    user=request.user,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.get_final_price()
                )
            
            # Clear the cart
            cart.clear()
            
            # Redirect to payment
            return redirect('payment_process', order_id=order.id)
        
        else:
            messages.error(request, "Please correct the errors below.")
    
    else:
        order_form = OrderForm(initial=initial_data)
        shipping_form = ShippingForm()
    
    context = {
        'cart': cart,
        'order_form': order_form,
        'shipping_form': shipping_form,
        'shipping_methods': shipping_methods,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    
    context = {
        'orders': orders,
    }
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def payment_process(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # For eSewa integration (sandbox mode)
    esewa_url = "https://uat.esewa.com.np/epay/main"
    
    context = {
        'order': order,
        'esewa_url': esewa_url,
        'merchant_id': 'EPAYTEST',  # eSewa test merchant ID
        'success_url': request.build_absolute_uri(f'/orders/payment-success/{order.id}/'),
        'failure_url': request.build_absolute_uri(f'/orders/payment-failure/{order.id}/'),
    }
    return render(request, 'orders/payment_process.html', context)

@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Get eSewa parameters
    oid = request.GET.get('oid')
    amt = request.GET.get('amt')
    refId = request.GET.get('refId')
    
    # Verify payment with eSewa (in a real implementation)
    # For this example, we'll just update the order status
    
    order.status = 'processing'
    order.payment_id = refId
    order.save()
    
    messages.success(request, "Payment successful! Your order is being processed.")
    
    return redirect('order_detail', order_id=order.id)

@login_required
def payment_failure(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    messages.error(request, "Payment failed. Please try again or choose a different payment method.")
    
    return redirect('order_detail', order_id=order.id)

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['pending', 'processing']:
        order.status = 'cancelled'
        order.save()
        
        # Return items to stock
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
        
        messages.success(request, "Your order has been cancelled.")
    else:
        messages.error(request, "This order cannot be cancelled.")
    
    return redirect('order_detail', order_id=order.id)