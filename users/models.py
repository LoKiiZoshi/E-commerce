from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')  
        CUSTOMER = 'CUSTOMER', _('Customer')

    email = models.EmailField(_('email address'), unique=True)
    google_id = models.CharField(max_length=255, blank=True, null=True)
    face_scan_data = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)   
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # ✅ Role field to distinguish between Admin and Customer
    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email or self.username

    def is_admin(self):
        return self.role == self.Roles.ADMIN

    def is_customer(self):
        return self.role == self.Roles.CUSTOMER


class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self): 
        return f"{self.user.email} - {self.token}"

    def is_valid(self):
        return self.expires_at > timezone.now()
