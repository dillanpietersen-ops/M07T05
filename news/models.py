"""Database models for the news application."""

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class CustomUser(AbstractUser):
    """Represent an authenticated news application user."""
    class Role(models.TextChoices):
        """Available application roles."""
        # Reader: can only view articles and newsletters.
        READER = "READER", "Reader"
        # Editor: can view, update, and delete articles and newsletters.
        EDITOR = "EDITOR", "Editor"
        # Journalist: can create, view, update, and delete articles and
        # newsletters.
        JOURNALIST = "JOURNALIST", "Journalist"
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER,
    )
    # Reader-specific fields.
    interests = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    # Journalist-specific fields.
    biography = models.TextField(
        blank=True,
        null=True,
    )
    journalist_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    subscribed_publishers = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribers",
    )
    subscribed_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="journalist_subscribers",
    )

    def clean(self):
        """Clear fields that do not belong to the selected role."""
        super().clean()
        if self.role == self.Role.READER:
            self.biography = None
            self.journalist_reference = None
        elif self.role == self.Role.JOURNALIST:
            self.interests = None
        else:
            self.interests = None
            self.biography = None
            self.journalist_reference = None

    def save(self, *args, **kwargs):
        """Validate role-specific fields before saving."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Return the username and role."""
        return f"{self.username} ({self.get_role_display()})"


class Publisher(models.Model):
    """Represent a publisher containing editors and journalists."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name="edited_publishers",
        limit_choices_to={"role": CustomUser.Role.EDITOR},
    )
    journalists = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name="publishers",
        limit_choices_to={"role": CustomUser.Role.JOURNALIST},
    )

    def __str__(self):
        """Return the publisher name."""
        return self.name


class Article(models.Model):
    """Represent an independent or publisher news article."""
    class Meta:
        """Configure article ordering."""
        ordering = ["-created_at", "-pk"]

    class Status(models.TextChoices):
        """Provide editorial workflow statuses."""

        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Awaiting approval"
        APPROVED = "APPROVED", "Approved"

    title = models.CharField(max_length=255)
    content = models.TextField()

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="authored_articles",
    )

    journalist = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journalist_articles",
        limit_choices_to={"role": CustomUser.Role.JOURNALIST},
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    approval_notification_sent = models.BooleanField(default=False)

    @property
    def approved(self):
        """Return whether the article is approved."""

        return self.status == self.Status.APPROVED


class Newsletter(models.Model):
    """Represent a curated collection of approved articles.

    Created by journalists.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="newsletters",
        limit_choices_to={"role": CustomUser.Role.JOURNALIST},
    )
    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name="newsletters",
        limit_choices_to={"status": Article.Status.APPROVED},
    )

    class Meta:
        """Configure newsletter ordering."""
        ordering = ["-created_at"]

    def clean(self):
        """Ensure a journalist created the newsletter."""
        super().clean()

        if self.author_id and self.author.role != CustomUser.Role.JOURNALIST:
            raise ValidationError(
                "A newsletter author must be a journalist."
            )

    def __str__(self):
        """Return the newsletter title."""
        return self.title
