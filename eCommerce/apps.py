from django.apps import AppConfig


class EcommerceConfig(AppConfig):
    """
    Configuration class for the eCommerce application.

    Registers application settings and startup behaviour
    for the marketplace system.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eCommerce'
