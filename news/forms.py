from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Newsletter, CustomUser


class ArticleForm(forms.ModelForm):
    """Create or update an article without exposing approval fields."""
    source_type = forms.ChoiceField(
        choices=[
            ("independent", "Independent journalist"),
            ("publisher", "Publisher"),
        ],
        widget=forms.RadioSelect(
        ),
        label="Publication source",
    )

    class Meta:
        """Configure editable article fields."""
        model = Article
        fields = [
            "title",
            "content",
            "source_type",
            "publisher",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter the article title",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 12,
                    "placeholder": "Write the article content",
                }
            ),
            "publisher": forms.Select(
                attrs={"class": "form-select"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        """Configure source choices for the journalist."""
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields["publisher"].queryset = user.publishers.all()
        if self.instance.pk:
            self.initial["source_type"] = (
                "publisher"
                if self.instance.publisher_id
                else "independent"
            )

    def clean(self):
        """Require exactly one valid publication source."""
        cleaned_data = super().clean()
        source_type = cleaned_data.get("source_type")
        publisher = cleaned_data.get("publisher")
        if source_type == "publisher":
            if publisher is None:
                self.add_error(
                    "publisher",
                    "Select a publisher for a publisher article.",
                )
            elif self.user is not None and not self.user.publishers.filter(
                pk=publisher.pk
            ).exists():
                self.add_error(
                    "publisher",
                    "Select a publisher that belongs to your account.",
                )
        elif source_type == "independent":
            cleaned_data["publisher"] = None
        return cleaned_data

    def save(self, commit=True):
        """Assign the selected source without exposing model fields."""
        article = super().save(commit=False)
        if self.user is not None:
            article.author = self.user
        source_type = self.cleaned_data.get("source_type")
        if source_type == "independent":
            article.journalist = self.user
            article.publisher = None
        else:
            article.journalist = None
            article.publisher = self.cleaned_data.get("publisher")
        if commit:
            article.full_clean()
            article.save()
        return article


class NewsletterForm(forms.ModelForm):
    """Create or update a journalist newsletter."""
    class Meta:
        """Configure newsletter form fields."""
        model = Newsletter
        fields = [
            "title",
            "description",
            "articles",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                }
            ),
            "articles": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, user=None, **kwargs):
        """Limit selection to approved articles."""
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["articles"].queryset = (
            Article.objects.filter(status=Article.Status.APPROVED)
            .select_related(
                "author",
                "journalist",
                "publisher",
            )
            .order_by("-created_at")
        )


class RegistrationForm(UserCreationForm):
    """Register a new user."""
    class Meta:
        model = CustomUser

        fields = [
            "username",
            "email",
            "role",
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        """Persist the custom user role as part of registration."""
        user = super().save(commit=False)
        if self.cleaned_data.get("role"):
            user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user
