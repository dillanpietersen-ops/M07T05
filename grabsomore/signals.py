from django.contrib.auth.models import Group

"""
Signal handlers and initialization functions for user roles.
"""


def create_default_groups():
    """
    Create the default application user groups.

    Ensures that the Admin, Vendor, and Buyer groups
    exist for role-based access control.
    """
    Group.objects.get_or_create(name='Admin')
    Group.objects.get_or_create(name='Vendor')
    Group.objects.get_or_create(name='Buyer')
