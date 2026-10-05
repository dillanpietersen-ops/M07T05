"""URL routes for the news application."""

from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views


from . import views
from .api_views import ArticleViewSet


app_name = "news"


router = DefaultRouter()
router.register(
    "articles",
    ArticleViewSet,
    basename="article-api",
)


urlpatterns = [
    # Login screen route & logout
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="login",
    ),
    path(
        "accounts/register/",
        views.register,
        name="register",
    ),
    path(
        "accounts/logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    # Public and dashboard routes.
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),

    # Article browser routes.
    path(
        "articles/",
        views.article_list,
        name="article-list",
    ),
    path(
        "articles/create/",
        views.article_create,
        name="article-create",
    ),
    path(
        "articles/<int:pk>/",
        views.article_detail,
        name="article-detail",
    ),
    path(
        "articles/<int:pk>/edit/",
        views.article_update,
        name="article-update",
    ),
    path(
        "articles/<int:pk>/delete/",
        views.article_delete,
        name="article-delete",
    ),
    path(
        "articles/<int:pk>/approve/",
        views.article_approve,
        name="article-approve",
    ),
    path(
        "articles/<int:pk>/submit/",
        views.submit_for_approval,
        name="article-submit",
    ),

    # Editor routes.
    path(
        "approval-queue/",
        views.approval_queue,
        name="approval-queue",
    ),

    # Newsletter routes.
    path(
        "newsletters/",
        views.newsletter_list,
        name="newsletter-list",
    ),
    path(
        "newsletters/create/",
        views.newsletter_create,
        name="newsletter-create",
    ),
    path(
        "newsletters/<int:pk>/",
        views.newsletter_detail,
        name="newsletter-detail",
    ),
    path(
        "newsletters/<int:pk>/edit/",
        views.newsletter_update,
        name="newsletter-update",
    ),
    path(
        "newsletters/<int:pk>/delete/",
        views.newsletter_delete,
        name="newsletter-delete",
    ),

    # Reader subscription routes.
    path(
        "subscriptions/",
        views.subscription_management,
        name="subscriptions",
    ),
    path(
        "subscriptions/publishers/<int:pk>/toggle/",
        views.toggle_publisher_subscription,
        name="toggle-publisher-subscription",
    ),
    path(
        "subscriptions/journalists/<int:pk>/toggle/",
        views.toggle_journalist_subscription,
        name="toggle-journalist-subscription",
    ),

    # API authentication and router routes.
    path(
        "api/token/",
        obtain_auth_token,
        name="api-token",
    ),
    path(
        "api/",
        include(router.urls),
    ),
]
