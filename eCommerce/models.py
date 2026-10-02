from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg


class Store(models.Model):
    """
Represents a vendor-managed store.
Contains information about the store owner and products.
"""
    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stores'
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        """Return the store name."""
        return self.name


class Product(models.Model):
    """
Represents a product available for purchase.
Stores product details, pricing, and stock levels.
"""
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='products'
    )
    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    # To make provision for soft delete vendor access approach
    is_active = models.BooleanField(default=True)

    name = models.CharField(
        max_length=100
    )
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    stock = models.IntegerField()

    def __str__(self):
        """Return the product name."""
        return self.name

    @property
    def average_rating(self):
        return (
            self.reviews.aggregate(
                Avg('rating')
            )['rating__avg'] or 0
        )

    class Meta:
        permissions = [
            ("add_products", "Can add products"),
            ("change_products", "Can change products"),
            ("delete_products", "Can delete products"),
            ("view_products", "Can view products"),
        ]


class ProductReview(models.Model):
    """
    Stores customer reviews and ratings for products.
    Supports verified and unverified purchase reviews.
    """
    RATING_CHOICES = [
        (1, '★'),
        (2, '★★'),
        (3, '★★★'),
        (4, '★★★★'),
        (5, '★★★★★'),
    ]
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES
    )
    verified_purchase = models.BooleanField(
        default=False
    )
    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        """
        Configure model-level constraints.

        Ensures that a user can only submit one review
        per product.
        """
        unique_together = ('product', 'user')

    def __str__(self):
        """
        Return a readable representation of the review.

        Returns:
            str: Username and product name.
        """
        return f"{self.user.username} - {self.product}"


class Order(models.Model):
    """
    Represents a customer purchase transaction.
    Stores delivery details, status, and pricing.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    full_name = models.CharField(max_length=150)
    delivery_address = models.TextField()
    phone_number = models.CharField(max_length=30)

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CONFIRMED'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Return a readable order identifier.

        Returns:
            str: Order ID.
        """
        return f'Order {self.id} - {self.buyer.username}'


class OrderItem(models.Model):
    """
Represents an individual product within an order.
Stores quantity and price information at purchase time.
"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.PROTECT
    )
    product_name = models.CharField(max_length=150)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    quantity = models.PositiveIntegerField(default=1)

    def get_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'
