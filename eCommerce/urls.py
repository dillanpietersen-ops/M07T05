"""
URL configuration for the eCommerce application.

Defines URL routing and URL configuration classes
used to register application endpoints.
"""

from abc import ABC, abstractmethod
from django.urls import path
from . import views

app_name = 'eCommerce'


class BaseURLConfig(ABC):
    """
    Abstract base class for application URL configuration.

    Provides a common structure for subclasses that
    define URL patterns for the application.
    """
    app_name = 'eCommerce'

    @classmethod
    @abstractmethod
    def get_urlpatterns(cls):
        """Return the URL patterns for this app."""
        raise NotImplementedError(
            'Subclasses must implement get_urlpatterns().'
        )


class EcommerceURLConfig(BaseURLConfig):
    """
    Concrete URL configuration for the eCommerce application.

    Defines URL routes for products, reviews, shopping cart,
    checkout, and customer dashboards.
    """
    @classmethod
    def get_urlpatterns(cls):
        """
        Generate and return all eCommerce URL patterns.

        Returns:
            list: Application URL pattern definitions.
        """
        return [
            path(
                'product/<int:product_id>/',
                views.view_product_page,
                name='product_page',
            ),
            path(
                'review/<int:product_id>/',
                views.add_review,
                name='add_review',
            ),
            path(
                'products/',
                views.list_products,
                name='products_list',
            ),
            path(
                'cart/',
                views.show_user_cart,
                name='main_cart_page',
            ),
            path(
                'change-price/',
                views.change_product_price,
                name='change_price',
            ),
            path(
                'add-to-cart/',
                views.add_item_to_cart,
                name='add_to_cart',
            ),
            path(
                'clear-cart/',
                views.clear_cart,
                name='clear_cart',
            ),
            path(
                'checkout/',
                views.checkout,
                name='checkout',
            ),
            path(
                'order-confirmation/<int:order_id>/',
                views.order_confirmation,
                name='order_confirmation',
            ),
            path(
                'buyer-dashboard/',
                views.buyer_dashboard,
                name='buyer_dashboard',
            ),
            path(
                'admin-dashboard/',
                views.admin_dashboard,
                name='admin_dashboard',
            ),
            path(
                'vendor-dashboard/',
                views.vendor_dashboard,
                name='vendor_dashboard',
            ),
            path(
                'users/',
                views.user_list,
                name='user_list',
            ),
            path(
                'vendors/',
                views.vendor_list,
                name='vendor_list',
            ),
            path(
                'orders/',
                views.order_list,
                name='order_list',
            ),
            path(
                'vendor/store/create/',
                views.create_store,
                name='create_store',
            ),
            path(
                'vendor/store/<int:store_id>/update/',
                views.update_store,
                name='update_store',
            ),
            path(
                'vendor/store/<int:store_id>/delete/',
                views.delete_store,
                name='delete_store',
            ),
            path(
                'vendor/product/create/',
                views.create_product,
                name='create_product',
            ),
            path(
                'vendor/product/<int:product_id>/stock/',
                views.update_stock,
                name='update_stock',
            ),
            path(
                'vendor/stores/',
                views.store_list,
                name='store_list',
            ),
            path(
                'vendor-products/',
                views.vendor_products,
                name='vendor_products',
            ),
            path(
                'product/<int:product_id>/update/',
                views.update_product,
                name='update_product',
            ),
            path(
                'product/<int:product_id>/delete/',
                views.delete_product,
                name='delete_product',
            ),
        ]


app_name = EcommerceURLConfig.app_name
urlpatterns = EcommerceURLConfig.get_urlpatterns()
