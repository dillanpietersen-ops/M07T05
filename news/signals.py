"""Signals for synchronizing user roles and Django groups."""
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser

ROLE_GROUP_MAP = {
    CustomUser.Role.READER: "Reader",
    CustomUser.Role.EDITOR: "Editor",
    CustomUser.Role.JOURNALIST: "Journalist",
}


@receiver(post_save, sender=CustomUser)
def assign_role_group(sender, instance, **kwargs):
    """Assign a user exclusively to the group matching the user's role."""
    group_name = ROLE_GROUP_MAP.get(instance.role)
    if not group_name:
        return
    role_groups = Group.objects.filter(
        name__in=tuple(ROLE_GROUP_MAP.values())
    )
    instance.groups.remove(*role_groups)
    group, _ = Group.objects.get_or_create(name=group_name)
    instance.groups.add(group)
