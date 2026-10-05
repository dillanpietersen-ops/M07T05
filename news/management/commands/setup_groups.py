"""Create application groups and assign model permissions."""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Create Reader, Editor, and Journalist groups."""
    help = "Create news application groups and permissions."
    GROUP_PERMISSIONS = {
        "Reader": [
            "view_article",
            "view_newsletter",
        ],
        "Editor": [
            "view_article",
            "change_article",
            "delete_article",
            "approve_article",
            "view_newsletter",
            "change_newsletter",
            "delete_newsletter",
        ],
        "Journalist": [
            "add_article",
            "view_article",
            "change_article",
            "delete_article",
            "add_newsletter",
            "view_newsletter",
            "change_newsletter",
            "delete_newsletter",
        ],
    }

    def handle(self, *args, **options):
        """Create each group and replace its permission collection."""
        for group_name, codenames in self.GROUP_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            permissions = Permission.objects.filter(
                content_type__app_label="news",
                codename__in=codenames,
            ).order_by("content_type__model", "codename")
            existing_codenames = set(
                permissions.values_list("codename", flat=True)
            )
            missing_codenames = sorted(set(codenames) - existing_codenames)

            if missing_codenames:
                self.stdout.write(
                    self.style.WARNING(
                        f"{group_name} is missing permissions: "
                        f"{', '.join(missing_codenames)}"
                    )
                )

            group.permissions.set(permissions)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Configured {group_name} with "
                    f"{permissions.count()} permissions."
                )
            )
