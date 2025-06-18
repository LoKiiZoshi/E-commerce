from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('face-login/', views.face_login, name='face_login'),
    path('register-face/', views.register_face, name='register_face'),
    path('google-login/', views.google_login, name='google_login'),
]