from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
import openai

from .models import Review, ReviewImage, ReviewVote
from .forms import ReviewForm, ReviewImageForm
from products.models import Product

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user has already reviewed this product
    existing_review = Review.objects.filter(product=product, user=request.user).first()
    if existing_review:
        messages.warning(request, 'You have already reviewed this product. You can edit your review instead.')
        return redirect('edit_review', review_id=existing_review.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            
            # Handle review images
            images = request.FILES.getlist('images')
            for image in images:
                ReviewImage.objects.create(review=review, image=image)
            
            messages.success(request, 'Your review has been submitted successfully.')
            return redirect('product_detail', slug=product.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'reviews/review_form.html', context)

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            
            # Handle review images
            images = request.FILES.getlist('images')
            for image in images:
                ReviewImage.objects.create(review=review, image=image)
            
            messages.success(request, 'Your review has been updated successfully.')
            return redirect('product_detail', slug=review.product.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReviewForm(instance=review)
    
    context = {
        'form': form,
        'review': review,
        'product': review.product,
    }
    return render(request, 'reviews/review_form.html', context)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product = review.product
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Your review has been deleted.')
        return redirect('product_detail', slug=product.slug)
    
    context = {
        'review': review,
        'product': product,
    }
    return render(request, 'reviews/review_confirm_delete.html', context)

@login_required
def delete_review_image(request, image_id):
    image = get_object_or_404(ReviewImage, id=image_id)
    review = image.review
    
    # Check if user owns this review
    if review.user != request.user:
        messages.error(request, "You don't have permission to delete this image.")
        return redirect('product_detail', slug=review.product.slug)
    
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image deleted successfully.')
        return redirect('edit_review', review_id=review.id)
    
    context = {
        'image': image,
        'review': review,
    }
    return render(request, 'reviews/review_image_confirm_delete.html', context)

@login_required
def vote_review(request, review_id):
    if request.method == 'POST':
        review = get_object_or_404(Review, id=review_id)
        vote_type = request.POST.get('vote')
        
        if vote_type not in dict(ReviewVote.VOTE_CHOICES):
            return JsonResponse({'success': False, 'error': 'Invalid vote type'})
        
        # Check if user has already voted
        existing_vote = ReviewVote.objects.filter(review=review, user=request.user).first()
        
        if existing_vote:
            if existing_vote.vote == vote_type:
                # Remove vote if clicking the same button
                existing_vote.delete()
                action = 'removed'
            else:
                # Change vote
                existing_vote.vote = vote_type
                existing_vote.save()
                action = 'changed'
        else:
            # Create new vote
            ReviewVote.objects.create(
                review=review,
                user=request.user,
                vote=vote_type
            )
            action = 'added'
        
        # Get updated vote counts
        helpful_count = ReviewVote.objects.filter(review=review, vote='helpful').count()
        not_helpful_count = ReviewVote.objects.filter(review=review, vote='not_helpful').count()
        
        return JsonResponse({
            'success': True,
            'action': action,
            'helpful_count': helpful_count,
            'not_helpful_count': not_helpful_count,
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def analyze_sentiment(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)
    
    if not reviews.exists():
        return JsonResponse({'success': False, 'error': 'No reviews found for this product'})
    
    try:
        # Prepare review texts
        review_texts = [f"{review.title}. {review.comment}" for review in reviews]
        
        # Use OpenAI for sentiment analysis
        openai.api_key = 'your-openai-api-key'  # Use environment variable in production
        
        prompt = f"Analyze the sentiment of these product reviews and provide a summary:\n\n"
        for text in review_texts[:5]:  # Limit to 5 reviews to avoid token limits
            prompt += f"- {text}\n"
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.7,
        )
        
        sentiment_analysis = response.choices[0].text.strip()
        
        return JsonResponse({
            'success': True,
            'sentiment_analysis': sentiment_analysis,
            'review_count': reviews.count(),
            'average_rating': sum(review.rating for review in reviews) / reviews.count(),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})