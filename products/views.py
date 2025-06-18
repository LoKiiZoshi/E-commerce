from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
import openai
import json



from .models import Product, Category, ProductImage, ProductTag
from .forms import ProductForm, ProductImageForm, CategoryForm
from reviews.models import Review  

def is_admin(user):
    
    return user.is_superuser or user.is_staff

def home_view(request):
    featured_products = Product.objects.filter(is_featured=True, is_available=True)[:8]
    categories = Category.objects.filter(parent=None)[:6]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'products/home.html', context)

def product_list(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Search by keyword
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Sort products
    sort_by = request.GET.get('sort_by', 'created_at')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name_asc':
        products = products.order_by('title')
    elif sort_by == 'name_desc':
        products = products.order_by('-title')
    else:
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    reviews = Review.objects.filter(product=product)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category, 
        is_available=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_available=True)
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'products/category_detail.html', context)

@login_required
@user_passes_test(is_admin)
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('product_detail', slug=product.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Add Product',
    }
    return render(request, 'products/product_form.html', context)

@login_required
@user_passes_test(is_admin)
def edit_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_detail', slug=product.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': 'Edit Product',
    }
    return render(request, 'products/product_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('product_list')
    
    context = {
        'product': product,
    }
    return render(request, 'products/product_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def add_product_image(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.product = product
            image.save()
            messages.success(request, 'Product image added successfully!')
            return redirect('product_detail', slug=product.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductImageForm()
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'products/product_image_form.html', context)

@login_required
@user_passes_test(is_admin)
def generate_product_content(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_type = data.get('product_type')
            
            # Use OpenAI to generate product content
            openai.api_key = 'your-openai-api-key'  # Use environment variable in production
            
            prompt = f"Generate a product title, description, and suggested price for a {product_type}."
            
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=200,
                n=1,
                stop=None,
                temperature=0.7,
            )
            
            generated_text = response.choices[0].text.strip()
            
            # Parse the generated text (this is a simple example, you might need more robust parsing)
            lines = generated_text.split('\n')
            title = lines[0].replace('Title:', '').strip() if 'Title:' in lines[0] else lines[0].strip()
            
            description_lines = []
            price = "0.00"
            
            for line in lines[1:]:
                if 'Price:' in line or '$' in line:
                    # Extract price
                    import re
                    price_match = re.search(r'\$?(\d+(\.\d{1,2})?)', line)
                    if price_match:
                        price = price_match.group(1)
                else:
                    description_lines.append(line)
            
            description = ' '.join(description_lines).strip()
            
            return JsonResponse({
                'success': True,
                'title': title,
                'description': description,
                'price': price
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'products/generate_content.html')