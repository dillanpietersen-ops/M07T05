"""Business services for article approval and notifications.

Using an explicit service is safer than sending email from a generic
post_save signal because approval is a business action.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from .models import CustomUser, Article


def notify_article_subscribers(article):
    """Email readers subscribed to the article's source."""
    subscribers = CustomUser.objects.filter(
        role=CustomUser.Role.READER,
        email__isnull=False,
    ).exclude(email="")
    if article.publisher_id:
        subscribers = subscribers.filter(
            subscribed_publishers=article.publisher
        )
    else:
        subscribers = subscribers.filter(
            subscribed_journalists=article.journalist
        )
    recipient_list = list(
        subscribers.values_list("email", flat=True).distinct()
    )
    if not recipient_list:
        return 0
    return send_mail(
        subject=f"New approved article: {article.title}",
        message=(
            f"A new article has been approved.\n\n"
            f"Title: {article.title}\n\n"
            f"{article.content[:500]}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )


@transaction.atomic
def approve_article(article):
    """Approve an article and send one subscriber notification."""
    article.status = Article.Status.APPROVED
    article.save(update_fields=["status"])
    if not article.approval_notification_sent:
        notify_article_subscribers(article)

        article.approval_notification_sent = True
        article.save(
            update_fields=["approval_notification_sent"]
        )
    return article
 