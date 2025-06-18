from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Sum, F, ExpressionWrapper, FloatField
from django.db.models.functions import Cast
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import uuid

from .models import PurchaseHistory, ProductView, Recommendation
from products.models import Product, Category, ProductTag

def record_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated:
        product_view, created = ProductView.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'view_count': 1}
        )
        
        if not created:
            product_view.view_count += 1
            product_view.save()
    else:
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id
        
        product_view, created = ProductView.objects.get_or_create(
            session_id=session_id,
            product=product,
            defaults={'view_count': 1}
        )
        
        if not created:
            product_view.view_count += 1
            product_view.save()
    
    return JsonResponse({'success': True})

@login_required
def user_recommendations(request):
    # Get collaborative filtering recommendations
    collaborative_recommendations = Recommendation.objects.filter(
        user=request.user,
        recommendation_type='collaborative'
    ).select_related('product')[:8]
    
    # Get content-based recommendations
    content_recommendations = Recommendation.objects.filter(
        user=request.user,
        recommendation_type='content_based'
    ).select_related('product')[:8]
    
    # Get popular items
    popular_recommendations = Recommendation.objects.filter(
        user=request.user,
        recommendation_type='popular'
    ).select_related('product')[:8]
    
    # Get recently viewed items
    recently_viewed = ProductView.objects.filter(
        user=request.user
    ).select_related('product').order_by('-last_viewed_at')[:8]
    
    context = {
        'collaborative_recommendations': collaborative_recommendations,
        'content_recommendations': content_recommendations,
        'popular_recommendations': popular_recommendations,
        'recently_viewed': recently_viewed,
    }
    return render(request, 'recommendations/user_recommendations.html', context)

def generate_recommendations(request):
    # This would typically be run as a scheduled task
    # For demonstration, we'll run it on demand
    
    # Generate collaborative filtering recommendations
    generate_collaborative_recommendations()
    
    # Generate content-based recommendations
    generate_content_based_recommendations()
    
    # Generate popular item recommendations
    generate_popular_recommendations()
    
    return JsonResponse({'success': True, 'message': 'Recommendations generated successfully'})

def generate_collaborative_recommendations():
    # Get all purchase history
    purchases = PurchaseHistory.objects.all().values('user_id', 'product_id', 'quantity')
    
    if not purchases:
        return
    
    # Convert to DataFrame
    df = pd.DataFrame.from_records(purchases)
    
    # Create user-item matrix
    user_item_matrix = df.pivot_table(
        index='user_id',
        columns='product_id',
        values='quantity',
        aggfunc='sum',
        fill_value=0
    )
    
    # Calculate user similarity
    user_similarity = cosine_similarity(user_item_matrix)
    user_similarity_df = pd.DataFrame(
        user_similarity,
        index=user_item_matrix.index,
        columns=user_item_matrix.index
    )
    
    # Generate recommendations for each user
    for user_id in user_item_matrix.index:
        # Get similar users
        similar_users = user_similarity_df[user_id].sort_values(ascending=False)[1:11]  # Top 10 similar users
        
        # Get products purchased by similar users but not by current user
        user_products = set(user_item_matrix.loc[user_id][user_item_matrix.loc[user_id] > 0].index)
        
        recommendations = {}
        
        for similar_user_id, similarity in similar_users.items():
            similar_user_products = set(user_item_matrix.loc[similar_user_id][user_item_matrix.loc[similar_user_id] > 0].index)
            new_products = similar_user_products - user_products
            
            for product_id in new_products:
                if product_id in recommendations:
                    recommendations[product_id] += similarity
                else:
                    recommendations[product_id] = similarity
        
        # Sort recommendations by score
        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Save recommendations to database
        for product_id, score in sorted_recommendations:
            try:
                product = Product.objects.get(id=product_id)
                Recommendation.objects.update_or_create(
                    user_id=user_id,
                    product=product,
                    recommendation_type='collaborative',
                    defaults={'score': score}
                )
            except Product.DoesNotExist:
                continue

def generate_content_based_recommendations():
    # Get all products
    products = Product.objects.all().prefetch_related('category', 'tags')
    
    if not products:
        return
    
    # Create product features
    product_features = []
    product_ids = []
    
    for product in products:
        # Combine title, description, category, and tags
        features = f"{product.title} {product.description} {product.category.name}"
        for tag in product.tags.all():
            features += f" {tag.name}"
        
        product_features.append(features)
        product_ids.append(product.id)
    
    # Create TF-IDF matrix
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(product_features)
    
    # Calculate product similarity
    product_similarity = cosine_similarity(tfidf_matrix)
    
    # Get all users
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.all()
    
    # Generate recommendations for each user
    for user in users:
        # Get products viewed or purchased by user
        viewed_products = ProductView.objects.filter(user=user).values_list('product_id', flat=True)
        purchased_products = PurchaseHistory.objects.filter(user=user).values_list('product_id', flat=True)
        
        user_products = list(set(viewed_products) | set(purchased_products))
        
        if not user_products:
            continue
        
        recommendations = {}
        
        for user_product_id in user_products:
            try:
                product_index = product_ids.index(user_product_id)
                
                # Get similar products
                similar_products = product_similarity[product_index]
                
                # Add to recommendations
                for i, score in enumerate(similar_products):
                    product_id = product_ids[i]
                    
                    if product_id != user_product_id and product_id not in user_products:
                        if product_id in recommendations:
                            recommendations[product_id] = max(recommendations[product_id], score)
                        else:
                            recommendations[product_id] = score
            except ValueError:
                continue
        
        # Sort recommendations by score
        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Save recommendations to database
        for product_id, score in sorted_recommendations:
            try:
                product = Product.objects.get(id=product_id)
                Recommendation.objects.update_or_create(
                    user=user,
                    product=product,
                    recommendation_type='content_based',
                    defaults={'score': score}
                )
            except Product.DoesNotExist:
                continue

def generate_popular_recommendations():
    # Get popular products based on purchase count and view count
    popular_products = Product.objects.annotate(
        purchase_count=Count('purchasehistory'),
        view_count=Count('productview'),
        popularity_score=ExpressionWrapper(
            Cast('purchase_count', FloatField()) * 2.0 + Cast('view_count', FloatField()),
            output_field=FloatField()
        )
    ).order_by('-popularity_score')[:50]
    
    # Get all users
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.all()
    
    # Generate recommendations for each user
    for user in users:
        # Get products already purchased by user
        purchased_products = PurchaseHistory.objects.filter(user=user).values_list('product_id', flat=True)
        
        # Recommend popular products not already purchased
        for i, product in enumerate(popular_products):
            if product.id not in purchased_products:
                # Score is inversely proportional to rank
                score = 1.0 / (i + 1)
                
                Recommendation.objects.update_or_create(
                    user=user,
                    product=product,
                    recommendation_type='popular',
                    defaults={'score': score}
                )