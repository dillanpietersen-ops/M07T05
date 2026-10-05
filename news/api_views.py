"""
REST API views for news application.
"""

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Article, CustomUser
from .permissions import ArticleRolePermission
from .serializers import ArticleSerializer
from .services import approve_article


class ArticleViewSet(viewsets.ModelViewSet):
    """
    Provide CRUD, subscription, and approval article endpoints.
    """
    serializer_class = ArticleSerializer
    permission_classes = [
        IsAuthenticated,
        ArticleRolePermission,
    ]

    def get_queryset(self):
        """Return articles visible to the authenticated user."""
        queryset = Article.objects.select_related(
            "author",
            "journalist",
            "publisher",
        )
        user = self.request.user
        if user.role == CustomUser.Role.READER:
            return queryset.filter(
                status=Article.Status.APPROVED
            )
        if user.role == CustomUser.Role.JOURNALIST:
            return queryset.filter(
                Q(author=user)
                | Q(status=Article.Status.APPROVED)
            ).distinct()
        if user.role == CustomUser.Role.EDITOR:
            return queryset
        return queryset.none()

    @action(
        detail=False,
        methods=["get"],
    )
    def subscribed(self, request):
        """
        Return approved articles from subscribed sources.
        """
        articles = (
            self.get_queryset()
            .filter(
                Q(
                    publisher__in=request.user.subscribed_publishers.all()
                )
                | Q(
                    journalist__in=request.user.subscribed_journalists.all()
                ),
                status=Article.Status.APPROVED,
            )
            .distinct()
        )
        serializer = self.get_serializer(
            articles,
            many=True,
        )
        return Response(
            serializer.data
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def approve(
        self,
        request,
        pk=None,
    ):
        """
        Allow an editor to approve an article.
        """
        if request.user.role != CustomUser.Role.EDITOR:
            return Response(
                {
                    "detail": (
                        "Only editors may approve articles."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        article = self.get_object()
        approve_article(article)
        return Response(
            self.get_serializer(article).data
        )
