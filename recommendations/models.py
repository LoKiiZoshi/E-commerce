from django.db import models
from django.conf import settings
from products.models import Product

class PurchaseHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='purchase_histories'
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.user.email} bought {self.product.title} x{self.quantity}"


class ProductView(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='product_views'
    )
    session_id = models.CharField(max_length=100, null=True, blank=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_views'
    )
    view_count = models.PositiveIntegerField(default=1)
    last_viewed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_viewed_at']
        unique_together = (
            ('user', 'product'),
            ('session_id', 'product'),
        )

    def __str__(self):
        who = self.user.email if self.user else f"Session {self.session_id}"
        return f"{who} viewed {self.product.title} ({self.view_count} times)"


class Recommendation(models.Model):
    RECOMMENDATION_TYPE_CHOICES = (
        ('collaborative',    'Collaborative Filtering'),
        ('content_based',    'Content-Based'),
        ('popular',          'Popular Items'),
        ('recently_viewed',  'Recently Viewed'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    score = models.FloatField()
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPE_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score']
        unique_together = ('user', 'product', 'recommendation_type')

    def __str__(self):
        return f"{self.user.email} → {self.product.title} ({self.recommendation_type}, {self.score:.2f})"
