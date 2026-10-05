"""Custom REST API permissions for role-based access."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import CustomUser


class ArticleRolePermission(BasePermission):
    """Authorize article operations according to the user's role."""

    def has_permission(self, request, view):
        """Check role access before entering the view."""
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.method == "POST":
            return request.user.role == CustomUser.Role.JOURNALIST

        return request.user.role in {
            CustomUser.Role.EDITOR,
            CustomUser.Role.JOURNALIST,
        }

    def has_object_permission(self, request, view, obj):
        """Check whether the user may modify the specific article."""
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.user.role == CustomUser.Role.EDITOR:
            return True

        return (
            request.user.role == CustomUser.Role.JOURNALIST
            and obj.author_id == request.user.id
        )
