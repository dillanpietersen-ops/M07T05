"""
Admin configuration for the eCommerce application.

Registers marketplace models for management
through the Django administration interface.
"""

from django.contrib import admin
from .models import Order, OrderItem, Product
admin.site.register(Product)


class OrderItemInline(admin.TabularInline):
    """
    Displays order items within the
    Order admin interface.
    """
    model = OrderItem
    extra = 0
    readonly_fields = (
        'product',
        'product_name',
        'price',
        'quantity',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Configures the administration
    interface for customer orders.
    """
    list_display = (
        'id',
        'buyer',
        'total_price',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'buyer__username',
        'full_name',
    )

    inlines = [OrderItemInline]
