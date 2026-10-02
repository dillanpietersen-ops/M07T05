from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class RegistrationForm(UserCreationForm):
    """
    User registration form for the eCommerce application.

    Extends Django's UserCreationForm by adding:
    - Email address field
    - User role selection (Admin, Vendor, Buyer)
    - Bootstrap styling for improved UI

    Validates that the email address is unique and that
    the password confirmation matches before creating a user.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email address",
            }
        ),
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=True,
        label="Account type",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm password",
            }
        ),
        help_text="Enter the same password again for verification.",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "role",
            "password1",
            "password2",
        ]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Username",
                }
            ),
        }

    def clean_email(self):
        """
        Validate that the email address is unique.
        """
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )
        return email

    def save(self, commit=True):
        """
        Create a new user and store the selected role.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": self.cleaned_data["role"],
                },
            )
        return user
