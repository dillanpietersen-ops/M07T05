"""Browser views for the news application."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .forms import ArticleForm, NewsletterForm, RegistrationForm
from .models import (
    Article,
    CustomUser,
    Newsletter,
    Publisher,
)


@login_required
def get_queryset(self):
    """Return articles visible to the authenticated user.

    Deterministic ordering is important for pagination and
    consistent results across requests.
    """
    queryset = Article.objects.select_related(
        "author",
        "journalist",
        "publisher",
    ).order_by("-created_at", "-pk")

    if self.request.user.role == CustomUser.Role.READER:
        return queryset.filter(approved=True)

    return queryset


"""One dashboard route that chooses the template according to
 the authenticated user's role.
"""


@login_required
def dashboard(request):
    """Display the dashboard matching the authenticated user's role."""
    user = request.user
    print("USERNAME:", user.username)
    print("ROLE:", user.role)
    print("GROUPS:", list(user.groups.values_list("name", flat=True)))

    if user.role == CustomUser.Role.READER:
        approved_articles = Article.objects.filter(
            status=Article.Status.APPROVED
        ).select_related(
            "author",
            "journalist",
            "publisher",
        )
        subscribed_articles = approved_articles.filter(
            Q(publisher__in=user.subscribed_publishers.all())
            | Q(journalist__in=user.subscribed_journalists.all())
        ).distinct()
        context = {
            "latest_articles": approved_articles[:10],
            "subscribed_articles": subscribed_articles[:10],
            "publishers": Publisher.objects.all(),
            "journalists": CustomUser.objects.filter(
                role=CustomUser.Role.JOURNALIST
            ),
            "newsletters": Newsletter.objects.prefetch_related(
                "articles"
            )[:10],
        }
        return render(request, "news/reader_dashboard.html", context)
    if user.role == CustomUser.Role.JOURNALIST:
        print("LOADING JOURNALIST DASHBOARD")

        context = {
            "articles": Article.objects.filter(
                author=user
            ).select_related("publisher"),

            "newsletters": Newsletter.objects.filter(
                author=user
            ).prefetch_related("articles"),
        }
        return render(
            request,
            "news/journalist_dashboard.html",
            context,
        )
    if user.role == CustomUser.Role.EDITOR:
        context = {
            "pending_articles": Article.objects.filter(
                status=Article.Status.PENDING
            ).select_related(
                "author",
                "journalist",
                "publisher",
            ),
        }
        return render(request, "news/editor_dashboard.html", context)
    return render(request, "news/access_denied.html", status=403)


@require_POST
@login_required
def article_submit(request, pk):
    article = get_object_or_404(
        Article,
        pk=pk,
        author=request.user,
    )
    article.status = Article.Status.PENDING
    article.save(update_fields=["status"])

    messages.success(
        request,
        "Article submitted for approval."
    )
    return redirect("news:dashboard")


@login_required
def article_create(request):
    """Create an unapproved article for the journalist."""
    if request.user.role != CustomUser.Role.JOURNALIST:
        return HttpResponseForbidden(
            "Only journalists may create articles."
        )
    if request.method == "POST":
        form = ArticleForm(request.POST, user=request.user)
        if form.is_valid():
            article = form.save()
            messages.success(request, "Article saved as a draft.")
            return redirect("news:article-detail", pk=article.pk)
    else:
        form = ArticleForm(user=request.user)
    return render(
        request,
        "news/article_form.html",
        {"form": form},
    )


def home(request):
    """Display the public home page."""
    latest_articles = Article.objects.filter(
        status=Article.Status.APPROVED
    ).select_related(
        "author",
        "journalist",
        "publisher",
    ).order_by("-created_at")[:10]
    return render(
        request,
        "news/home.html",
        {
            "latest_articles": latest_articles,
        },
    )


def article_list(request):
    """Display articles visible to the current Journalist.
    Journalists see their own articles, even if they are DRAFT.
    Readers only see APPROVED articles.
    Editors will currently also only see APPROVED articles"""
    print(
        Article.objects.all().values_list(
            "title",
            "status"
        )
    )
    if (
        request.user.is_authenticated
        and request.user.role == CustomUser.Role.JOURNALIST
    ):
        articles = Article.objects.filter(
            author=request.user
        )
    else:
        articles = Article.objects.filter(
            status=Article.Status.APPROVED
        )
    return render(
        request,
        "news/article_list.html",
        {
            "articles": articles,
        },
    )


def article_detail(request, pk):
    """Display a single article."""
    article = get_object_or_404(
        Article,
        pk=pk,
    )
    return render(
        request,
        "news/article_detail.html",
        {
            "article": article,
            "can_manage": (
                request.user.is_authenticated and (
                    request.user == article.author
                    or request.user.role == CustomUser.Role.EDITOR
                )
            ),
        },
    )


@login_required
def article_update(request, pk):
    """Update an existing article."""
    article = get_object_or_404(
        Article,
        pk=pk,
    )
    if request.user != article.author and (
        request.user.role != CustomUser.Role.EDITOR
    ):
        return HttpResponseForbidden(
            "You do not have permission to edit this article."
        )
    return render(
        request,
        "news/article_form.html",
        {
            "form": ArticleForm(instance=article),
            "article": article,
        },
    )


@login_required
def article_delete(request, pk):
    """Delete an article."""
    article = get_object_or_404(
        Article,
        pk=pk,
    )
    if (
        request.user != article.author
        and request.user.role != CustomUser.Role.EDITOR
    ):
        return HttpResponseForbidden(
            "You do not have permission to delete this article."
        )
    if request.method == "POST":
        article.delete()

        messages.success(
            request,
            "Article deleted successfully.",
        )
        return redirect("news:dashboard")
    return render(
        request,
        "news/article_confirm_delete.html",
        {
            "article": article,
        },
    )


@require_POST
@login_required
def article_approve(request, pk):
    """Approve an article."""
    print("APPROVE BUTTON CLICKED")
    article = get_object_or_404(
        Article,
        pk=pk,
    )
    if request.user.role != CustomUser.Role.EDITOR:
        return HttpResponseForbidden(
            "Only editors may approve articles."
        )
    if article.status == Article.Status.APPROVED:
        messages.info(
            request,
            "This article is already approved.",
        )
        return redirect("news:approval-queue")

    article.status = Article.Status.APPROVED
    article.save(update_fields=["status"])
    messages.success(
        request,
        f'"{article.title}" approved successfully.',
    )
    return redirect("news:approval-queue")


@login_required
def approval_queue(request):
    """Display articles awaiting approval."""
    if request.user.role != CustomUser.Role.EDITOR:
        return HttpResponseForbidden(
            "Only editors may access the approval queue."
        )
    pending_articles = (
        Article.objects.filter(
            status=Article.Status.PENDING
        )
        .select_related(
            "author",
            "journalist",
            "publisher",
        )
        .order_by("created_at")
    )
    return render(
        request,
        "news/approval_queue.html",
        {
            "pending_articles": pending_articles,
        },
    )


def newsletter_list(request):
    """Display all newsletters."""
    newsletters = (
        Newsletter.objects
        .select_related("author")
        .prefetch_related("articles")
        .order_by("-created_at")
    )
    return render(
        request,
        "news/newsletter_list.html",
        {
            "newsletters": newsletters,
        },
    )


@login_required
def newsletter_create(request):
    """Create a newsletter."""

    if request.user.role != CustomUser.Role.JOURNALIST:
        return HttpResponseForbidden(
            "Only journalists may create newsletters."
        )
    if request.method == "POST":
        form = NewsletterForm(
            request.POST,
            user=request.user,
        )
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()
            messages.success(
                request,
                "Newsletter created successfully."
            )
            return redirect(
                "news:newsletter-detail",
                pk=newsletter.pk,
            )
    else:
        form = NewsletterForm(
            user=request.user,
        )
    return render(
        request,
        "news/newsletter_form.html",
        {
            "form": form,
            "page_title": "Create Newsletter",
            "submit_label": "Create Newsletter",
        },
    )


def newsletter_detail(request, pk):
    """Display a newsletter and its articles."""
    newsletter = get_object_or_404(
        Newsletter.objects.prefetch_related("articles"),
        pk=pk,
    )
    articles = newsletter.articles.filter(
        status=Article.Status.APPROVED
    )
    can_manage = False
    if request.user.is_authenticated:
        can_manage = (
            request.user == newsletter.author
            or request.user.role == CustomUser.Role.EDITOR
        )
    return render(
        request,
        "news/newsletter_detail.html",
        {
            "newsletter": newsletter,
            "articles": articles,
            "can_manage": can_manage,
        },
    )


@login_required
def newsletter_update(request, pk):
    """Update an existing newsletter."""
    newsletter = get_object_or_404(
        Newsletter,
        pk=pk,
    )
    if (
        request.user != newsletter.author
        and request.user.role != CustomUser.Role.EDITOR
    ):
        return HttpResponseForbidden(
            "You do not have permission to edit this newsletter."
        )
    if request.method == "POST":
        form = NewsletterForm(
            request.POST,
            instance=newsletter,
            user=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Newsletter updated successfully."
            )
            return redirect(
                "news:newsletter-detail",
                pk=newsletter.pk,
            )
    else:
        form = NewsletterForm(
            instance=newsletter,
            user=request.user,
        )
    return render(
        request,
        "news/newsletter_form.html",
        {
            "form": form,
            "newsletter": newsletter,
            "page_title": "Edit Newsletter",
            "submit_label": "Save Changes",
        },
    )


@login_required
def newsletter_delete(request, pk):
    """Delete a newsletter."""
    newsletter = get_object_or_404(
        Newsletter,
        pk=pk,
    )
    if (
        request.user != newsletter.author
        and request.user.role != CustomUser.Role.EDITOR
    ):
        return HttpResponseForbidden(
            "You do not have permission to delete this newsletter."
        )
    if request.method == "POST":
        newsletter_title = newsletter.title
        newsletter.delete()
        messages.success(
            request,
            f'Newsletter "{newsletter_title}" deleted successfully.'
        )
        return redirect("news:dashboard")
    return render(
        request,
        "news/newsletter_confirm_delete.html",
        {
            "newsletter": newsletter,
        },
    )


@login_required
def submit_for_approval(request, pk):
    article = get_object_or_404(
        Article,
        pk=pk,
        author=request.user,
    )

    article.status = Article.Status.PENDING
    article.save()

    return redirect("news:dashboard")


@login_required
def subscription_management(request):
    """Display subscription management page."""

    if request.user.role != CustomUser.Role.READER:
        return HttpResponseForbidden(
            "Only readers may manage subscriptions."
        )

    publishers = Publisher.objects.order_by("name")

    journalists = CustomUser.objects.filter(
        role=CustomUser.Role.JOURNALIST
    ).order_by("username")

    context = {
        "publishers": publishers,
        "journalists": journalists,
        "subscribed_publisher_ids": set(
            request.user.subscribed_publishers.values_list(
                "id",
                flat=True,
            )
        ),
        "subscribed_journalist_ids": set(
            request.user.subscribed_journalists.values_list(
                "id",
                flat=True,
            )
        ),
    }

    return render(
        request,
        "news/subscription_management.html",
        context,
    )


@require_POST
@login_required
def toggle_publisher_subscription(request, pk):
    """Subscribe or unsubscribe a reader from a publisher."""

    if request.user.role != CustomUser.Role.READER:
        return HttpResponseForbidden(
            "Only readers may manage subscriptions."
        )

    publisher = get_object_or_404(
        Publisher,
        pk=pk,
    )

    if request.user.subscribed_publishers.filter(
        pk=publisher.pk
    ).exists():

        request.user.subscribed_publishers.remove(
            publisher
        )

        messages.success(
            request,
            f"Unsubscribed from {publisher.name}."
        )

    else:
        request.user.subscribed_publishers.add(
            publisher
        )

        messages.success(
            request,
            f"Subscribed to {publisher.name}."
        )

    return redirect(
        "news:subscriptions"
    )


@require_POST
@login_required
def toggle_journalist_subscription(request, pk):
    """Subscribe or unsubscribe from a journalist."""

    if request.user.role != CustomUser.Role.READER:
        return HttpResponseForbidden(
            "Only readers may manage subscriptions."
        )

    journalist = get_object_or_404(
        CustomUser,
        pk=pk,
        role=CustomUser.Role.JOURNALIST,
    )

    if request.user.subscribed_journalists.filter(
        pk=journalist.pk
    ).exists():

        request.user.subscribed_journalists.remove(
            journalist
        )

        messages.success(
            request,
            f"Unsubscribed from {journalist.username}."
        )

    else:
        request.user.subscribed_journalists.add(
            journalist
        )

        messages.success(
            request,
            f"Subscribed to {journalist.username}."
        )

    return redirect(
        "news:subscriptions"
    )


def register(request):
    """Register a new user."""

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Account created successfully."
            )

            return redirect("news:login")

    else:
        form = RegistrationForm()

    return render(
        request,
        "registration/register.html",
        {"form": form},
    )
