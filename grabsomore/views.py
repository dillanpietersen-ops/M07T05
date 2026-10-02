# Show HTML pages and redirect users.
from django.shortcuts import render, redirect
from django.contrib.auth.models import (  # Django's built-in auth models
    User,
)
from django.contrib.auth import (  # Functions to handle login and logout
    authenticate,
    login,
    logout,
)
from django.http import (  # For redirecting users or sending responses
    HttpResponseRedirect,
)
from django.urls import reverse, reverse_lazy  # Helps get URLs by their names
from django.contrib.auth.decorators import login_required  # Requires login
from datetime import datetime
from hashlib import sha1  # To hash tokens securely
from django.core.exceptions import ObjectDoesNotExist

from .utils import generate_reset_url, build_email  # Email and token helpers
from .models import ResetToken, UserProfile
from django.contrib.auth.hashers import make_password  # Hash passwords
from eCommerce.models import Product
from django.contrib import messages
from .forms import RegistrationForm


def redirect_to_dashboard(user):
    """
    Redirect an authenticated user according to the assigned role.
    """
    # Django superusers always receive admin access.
    if user.is_superuser:
        return redirect("eCommerce:admin_dashboard")
    try:
        role = user.userprofile.role.upper()
    except UserProfile.DoesNotExist:
        return redirect("grabsomore:welcome")
    if role == "ADMIN":
        return redirect("eCommerce:admin_dashboard")
    if role == "VENDOR":
        return redirect("eCommerce:vendor_dashboard")
    if role == "BUYER":
        return redirect("eCommerce:buyer_dashboard")
    return redirect("grabsomore:welcome")


# This function handles user login


def login_user(request):
    # Display the login form for a GET request.
    if request.method != "POST":
        return render(request, "grabsomore/login.html")
    # Read submitted credentials.
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    # Ensure both fields were submitted.
    if not username or not password:
        return render(
            request,
            "grabsomore/login.html",
            {
                "error": "Username and password are required."
            },
        )
    # Authenticate the user.
    user = authenticate(
        request,
        username=username,
        password=password,
    )
    if user is None:
        return render(
            request,
            "grabsomore/login.html",
            {
                "error": "Invalid username or password."
            },
        )
    # Create the authenticated session.
    login(request, user)
    # Optional session values.
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    # Send the user to the dashboard for the assigned role.
    return redirect_to_dashboard(user)


@login_required
def buyer_dashboard(request):
    products = Product.objects.filter(is_active=True, store__is_active=True)
    context = {
        'products': products
    }
    return render(
        request,
        'eCommerce/buyer_dashboard.html',
        context
    )


# Helper function to change a user's password securely
def change_user_password(username, new_password):
    user = User.objects.get(username=username)  # Find user by username

    # Set the new password (hashed automatically).
    user.set_password(new_password)

    user.save()  # Save changes to the database


# Logs the user out and redirects to login page
def logout_user(request):
    if request.user is not None:
        logout(request)  # Log out the current user
        return HttpResponseRedirect(reverse('grabsomore:login'))


# Only logged-in users can see the welcome page
@login_required(login_url=reverse_lazy('grabsomore:login'))
def welcome(request):
    return render(request, 'grabsomore/welcome.html')  # Show the welcome page


# Handles sending the password reset email after user submits their email
def send_password_reset(request):
    if request.method == 'POST':
        user_email = request.POST.get('email')
        try:
            user = User.objects.get(email=user_email)  # Find user by email
            # Generate reset link with token.
            reset_url = generate_reset_url(user)
            email = build_email(user, reset_url)  # Create the email message
            email.send()  # Send the email

            # Show a confirmation page that email was sent
            return render(request, 'grabsomore/reset_email_sent.html', {
                'email': user_email
            })

        except ObjectDoesNotExist:
            # Show confirmation even when no user is found to avoid info leaks.
            return render(request, 'grabsomore/reset_email_sent.html', {
                'email': user_email
            })

    # Show the form where user can enter their email
    return render(request, 'grabsomore/request_password_reset.html')


# This view is called when user clicks the reset link in their email
def reset_user_password(request, token):
    hashed_token = sha1(token.encode()).hexdigest()  # Hash the token from URL
    try:
        user_token = ResetToken.objects.get(
            token=hashed_token,
        )  # Look for token in DB
        # Check if the token expired
        if user_token.expiry_date.replace(tzinfo=None) < datetime.now():
            user_token.delete()  # Delete expired token
            return render(
                request,
                'grabsomore/password_reset_expired.html',
            )  # Show expired token message
        # Save user ID and token in session to verify next step
        request.session['user_id'] = user_token.user.id
        request.session['reset_token'] = token

        # Show the password reset form
        return render(
            request,
            'grabsomore/password_reset.html',
            {'token': token},
        )
    except ResetToken.DoesNotExist:
        # Token not found or already used
        return render(request, 'grabsomore/password_reset_invalid.html')


# Handles the password reset form submission (when user enters new password)
def reset_password(request):
    if request.method == 'POST':
        username = request.session.get('user')
        token = request.session.get('token')
        password = request.POST.get('password')
        password_conf = request.POST.get('password_conf')

        # Check if all required data is present
        if not all([username, token, password, password_conf]):
            return render(request, 'password_reset.html', {
                'error': 'Missing fields or session expired.',
                'token': token
            })
        # Check if passwords match
        if password != password_conf:
            return render(request, 'password_reset.html', {
                'error': 'Passwords do not match.',
                'token': token
            })
        try:
            user = User.objects.get(username=username)  # Find user by username
            hashed_token = sha1(token.encode()).hexdigest()
            reset_token = ResetToken.objects.get(token=hashed_token)

            # Check token expiry again (just to be sure)
            if reset_token.expiry_date.replace(tzinfo=None) < datetime.now():
                reset_token.delete()
                return render(request, 'password_reset_expired.html')
            # Update the user's password (hashed securely)
            user.password = make_password(password)
            user.save()
            # Delete the token and clear session info
            reset_token.delete()
            request.session.flush()
            # Redirect user to login page after successful password reset
            return HttpResponseRedirect(reverse('grabsomore:login'))
        except (User.DoesNotExist, ResetToken.DoesNotExist):
            return render(request, 'password_reset_invalid.html')
    # If accessed with GET or another method, redirect to the login page
    return HttpResponseRedirect(reverse('grabsomore:login'))


def admin_required(user):
    """
Restricts access to users with Administrator privileges.
"""
    return (
        hasattr(user, "userprofile")
        and user.userprofile.role == "ADMIN"
    )


def vendor_required(user):
    """
Restricts access to users with Vendor privileges.
"""
    return (
        hasattr(user, "userprofile")
        and user.userprofile.role == "VENDOR"
    )


def buyer_required(user):
    """
Restricts access to users with Buyer privileges.
"""
    return (
        hasattr(user, "userprofile")
        and user.userprofile.role == "BUYER"
    )


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend",
            )
            messages.success(
                request,
                "Your account was created successfully."
            )
            return redirect_to_dashboard(user)
    else:
        form = RegistrationForm()
    return render(
        request,
        "grabsomore/register.html",
        {"form": form},
    )


@login_required
def dashboard_redirect(request):
    return redirect_to_dashboard(request.user)


@login_required
def admin_dashboard(request):
    if not (
        request.user.is_superuser
        or (
            hasattr(request.user, "userprofile")
            and request.user.userprofile.role == UserProfile.ADMIN
        )
    ):
        return redirect("grabsomore:dashboard_redirect")

    return render(request, "grabsomore/admin_dashboard.html")


@login_required
def vendor_dashboard(request):
    if not (
        hasattr(request.user, "userprofile")
        and request.user.userprofile.role == UserProfile.VENDOR
    ):
        return redirect("grabsomore:dashboard_redirect")

    return render(request, "grabsomore/vendor_dashboard.html")
