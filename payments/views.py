from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
import requests
import json 

from .models import Payment, EsewaPayment
from orders.models import Order

@login_required
def payment_methods(request):
    context = {
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'payments/payment_methods.html', context)

@login_required
def esewa_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Create payment record
    payment = Payment.objects.create(
        user=request.user,
        order=order,
        amount=order.total_price,
        payment_method='esewa',
        status='pending'
    )
    
    # Create eSewa payment record
    esewa_payment = EsewaPayment.objects.create(
        payment=payment,
        product_id=f"ORDER-{order.id}",
        product_name=f"Order #{order.id}",
        success_url=request.build_absolute_uri(f'/payments/esewa-success/{payment.id}/'),
        failure_url=request.build_absolute_uri(f'/payments/esewa-failure/{payment.id}/')
    )
    
    # eSewa sandbox URL
    esewa_url = "https://uat.esewa.com.np/epay/main"
    
    context = {
        'order': order,
        'payment': payment,
        'esewa_payment': esewa_payment,
        'esewa_url': esewa_url,
        'merchant_id': 'EPAYTEST',  # eSewa test merchant ID
    }
    return render(request, 'payments/esewa_payment.html', context)

@login_required
def esewa_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    esewa_payment = get_object_or_404(EsewaPayment, payment=payment)
    
    # Get eSewa parameters
    oid = request.GET.get('oid')
    amt = request.GET.get('amt')
    refId = request.GET.get('refId')
    
    # Verify payment with eSewa (in a real implementation)
    # For this example, we'll just update the payment status
    
    # Update payment record
    payment.status = 'completed'
    payment.transaction_id = refId
    payment.save()
    
    # Update eSewa payment record
    esewa_payment.reference_id = refId
    esewa_payment.save()
    
    # Update order status
    order = payment.order
    order.status = 'processing'
    order.payment_id = refId
    order.save()
    
    messages.success(request, "Payment successful! Your order is being processed.")
    
    return redirect('order_detail', order_id=order.id)

@login_required
def esewa_failure(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    # Update payment record
    payment.status = 'failed'
    payment.save()
    
    messages.error(request, "Payment failed. Please try again or choose a different payment method.")
    
    return redirect('order_detail', order_id=payment.order.id)

@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user)
    
    context = {
        'payments': payments,
    }
    return render(request, 'payments/payment_history.html', context)

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    context = {
        'payment': payment,
    }
    return render(request, 'payments/payment_detail.html', context)