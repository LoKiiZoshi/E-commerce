from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import uuid

from .models import Cart, CartItem
from products.models import Product 

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.get('cart_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['cart_id'] = session_id
        
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    
    return cart

def cart_detail(request):
    cart = get_or_create_cart(request)
    
    context = {
        'cart': cart,
    }
    return render(request, 'cart/cart_detail.html', context)

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if product is already in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    # If product already exists in cart, update quantity
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f"{product.title} added to your cart.")
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{product.title} added to your cart.",
            'cart_total': cart.get_total_items(),
        })
    
    return redirect('cart_detail')

def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if user owns this cart item
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            messages.error(request, "You don't have permission to update this cart.")
            return redirect('cart_detail')
    else:
        session_id = request.session.get('cart_id')
        if cart_item.cart.session_id != session_id:
            messages.error(request, "You don't have permission to update this cart.")
            return redirect('cart_detail')
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, "Cart updated successfully.")
    else:
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'cart_total': cart.get_total_items(),
            'item_total': cart_item.get_total_price() if quantity > 0 else 0,
            'cart_subtotal': cart.get_total_price(),
        })
    
    return redirect('cart_detail')

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if user owns this cart item
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            messages.error(request, "You don't have permission to remove this item.")
            return redirect('cart_detail')
    else:
        session_id = request.session.get('cart_id')
        if cart_item.cart.session_id != session_id:
            messages.error(request, "You don't have permission to remove this item.")
            return redirect('cart_detail')
    
    product_title = cart_item.product.title
    cart_item.delete()
    
    messages.success(request, f"{product_title} removed from your cart.")
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = get_or_create_cart(request)
        return JsonResponse({
            'success': True,
            'message': f"{product_title} removed from your cart.",
            'cart_total': cart.get_total_items(),
            'cart_subtotal': cart.get_total_price(),
        })
    
    return redirect('cart_detail')

def clear_cart(request):
    cart = get_or_create_cart(request)
    cart.clear()
    
    messages.success(request, "Your cart has been cleared.")
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': "Your cart has been cleared.",
            'cart_total': 0,
        })
    
    return redirect('cart_detail')

@login_required
def merge_carts(request):
    # Get the session cart
    session_id = request.session.get('cart_id')
    if not session_id:
        return redirect('cart_detail')
    
    session_cart = Cart.objects.filter(session_id=session_id).first()
    if not session_cart:
        return redirect('cart_detail')
    
    # Get or create the user cart
    user_cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Merge items from session cart to user cart
    for item in session_cart.items.all():
        user_cart_item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            product=item.product,
            defaults={'quantity': item.quantity}
        )
        
        if not created:
            user_cart_item.quantity += item.quantity
            user_cart_item.save()
    
    # Delete the session cart
    session_cart.delete()
    
    # Clear the session cart ID
    if 'cart_id' in request.session:
        del request.session['cart_id']
    
    messages.success(request, "Your carts have been merged.")
    return redirect('cart_detail')