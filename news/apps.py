"""Application configuration for the news application."""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Configure the news application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "news"

    def ready(self):
        """Register application signals."""
        import news.signals  # noqa: F401
