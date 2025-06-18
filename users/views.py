from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import uuid
import datetime
import json
import base64
import numpy as np
import requests 

from .models import CustomUser, PasswordResetToken
from .forms import UserRegistrationForm, UserLoginForm, PasswordResetForm, PasswordResetConfirmForm, UserProfileForm

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')

                # ✅ Role-based redirection
                if user.is_superuser or user.is_staff or getattr(user, 'role', '') == 'ADMIN':
                    return redirect('inventory_dashboard')  # 🔄 Use the named URL from urls.py
                else:
                    return redirect('home')  # Regular user landing page
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():  
            email = form.cleaned_data.get('email')
            try:
                user = CustomUser.objects.get(email=email)
                token = str(uuid.uuid4())
                expires_at = timezone.now() + datetime.timedelta(hours=24)
                
                # Create or update password reset token
                PasswordResetToken.objects.update_or_create( 
                    user=user,
                    defaults={'token': token, 'expires_at': expires_at}
                )
                
                # Send email with reset link
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'token': token})
                )
                send_mail(
                    'Password Reset Request',
                    f'Please click the link to reset your password: {reset_url}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Password reset link has been sent to your email.')
                return redirect('login')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No user with that email address exists.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordResetForm()
    
    return render(request, 'users/password_reset_request.html', {'form': form})

def password_reset_confirm(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        if not reset_token.is_valid():
            messages.error(request, 'Password reset link has expired.')
            return redirect('password_reset_request')
        
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                user = reset_token.user
                user.set_password(form.cleaned_data.get('new_password'))
                user.save()
                
                # Delete the token
                reset_token.delete()
                
                messages.success(request, 'Password has been reset successfully. You can now login.')
                return redirect('login')
        else:
            form = PasswordResetConfirmForm()
        
        return render(request, 'users/password_reset_confirm.html', {'form': form})
    
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('password_reset_request')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'users/profile.html', {'form': form})

@csrf_exempt
def face_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            face_data = data.get('face_data')
            
            # Convert base64 to numpy array for face comparison
            face_array = np.frombuffer(base64.b64decode(face_data.split(',')[1]), np.uint8)
            
            # Here you would implement face recognition logic
            # For demonstration, we'll just check if any user has face data
            users = CustomUser.objects.filter(face_scan_data__isnull=False)
            
            # In a real implementation, you would compare the face_array with stored face data
            # For now, we'll just authenticate the first user with face data (for demo purposes)
            if users.exists():
                user = users.first()
                login(request, user)
                return JsonResponse({'success': True, 'message': 'Face login successful'})
            else:
                return JsonResponse({'success': False, 'message': 'No matching face found'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def register_face(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            face_data = data.get('face_data')
            
            # Store the face data in the user's profile
            request.user.face_scan_data = face_data
            request.user.save()
            
            return JsonResponse({'success': True, 'message': 'Face registered successfully'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request or user not authenticated'})

def google_login(request):
    # This would be implemented with a proper OAuth library
    # For demonstration purposes, we'll just render a template with Google login button
    return render(request, 'users/google_login.html')