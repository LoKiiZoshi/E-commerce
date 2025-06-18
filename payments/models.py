from django.db import models
from django.conf import settings
from orders.models import Order

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('esewa', 'eSewa'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.order.id} - {self.user.email}"

class EsewaPayment(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='esewa_payment')
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    success_url = models.URLField()
    failure_url = models.URLField()
    
    def __str__(self):
        return f"eSewa Payment for {self.payment.order.id}"