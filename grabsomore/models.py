from django.contrib.auth.models import User
from django.db import models


class ResetToken(models.Model):
    """
    Represents a password reset token issued to a user.

    Stores a unique token and expiry date used during
    the password recovery process.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    token = models.CharField(
        max_length=100
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    expiry_date = models.DateTimeField()

    def __str__(self):
        return self.token


class UserProfile(models.Model):
    """
    Extends the Django User model with application-specific
    profile information.

    Stores the role assigned to a user, such as Buyer
    or Vendor, to support role-based access control.
    """
    BUYER = "BUYER"
    VENDOR = "VENDOR"
    ADMIN = "ADMIN"
    ROLE_CHOICES = [
        (BUYER, "Buyer"),
        (VENDOR, "Vendor"),
        # (ADMIN, "Administrator"),
    ]
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="userprofile",
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=BUYER,
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
