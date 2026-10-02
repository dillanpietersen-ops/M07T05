from django.contrib.auth.decorators import user_passes_test


def admin_required(view_func):
    """
    Restrict access to users with the Administrator role.

    Args:
        view_func: Django view function to protect.

    Returns:
        Decorated view requiring Administrator access.
    """
    return user_passes_test(
        lambda u: hasattr(u, "userprofile")
        and u.userprofile.role == "ADMIN"
    )(view_func)


def vendor_required(view_func):
    """
    Restrict access to users with the Vendor role.

    Args:
        view_func: Django view function to protect.

    Returns:
        Decorated view requiring Vendor access.
    """
    return user_passes_test(
        lambda u: hasattr(u, "userprofile")
        and u.userprofile.role == "VENDOR"
    )(view_func)


def buyer_required(view_func):
    """
    Restrict access to users with the Buyer role.

    Args:
        view_func: Django view function to protect.

    Returns:
        Decorated view requiring Buyer access.
    """
    return user_passes_test(
        lambda u: hasattr(u, "userprofile")
        and u.userprofile.role == "BUYER"
    )(view_func)
