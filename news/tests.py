from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Article,
    CustomUser,
    Publisher,
)


class ArticleAPITests(APITestCase):

    def setUp(self):
        """Create test users, publishers, and articles."""

        self.password = "SafePass123!"

        # Create required groups
        for name in ["Reader", "Editor", "Journalist"]:
            Group.objects.get_or_create(name=name)

        # Create users
        self.reader = CustomUser.objects.create_user(
            username="reader",
            email="reader@example.com",
            password=self.password,
            role=CustomUser.Role.READER,
        )

        self.editor = CustomUser.objects.create_user(
            username="editor",
            email="editor@example.com",
            password=self.password,
            role=CustomUser.Role.EDITOR,
        )

        self.journalist = CustomUser.objects.create_user(
            username="journalist",
            email="journalist@example.com",
            password=self.password,
            role=CustomUser.Role.JOURNALIST,
        )

        self.other_journalist = CustomUser.objects.create_user(
            username="otherjournalist",
            email="otherjournalist@example.com",
            password=self.password,
            role=CustomUser.Role.JOURNALIST,
        )

        # Create publishers
        self.publisher = Publisher.objects.create(
            name="Test Publisher",
        )

        self.other_publisher = Publisher.objects.create(
            name="Other Publisher",
        )

        # Create approved article
        self.approved_article = Article.objects.create(
            title="Approved Article",
            content="Approved article content.",
            author=self.journalist,
            journalist=self.journalist,
            status=Article.Status.APPROVED,
        )

        # Create pending article
        self.draft_article = Article.objects.create(
            title="Draft Article",
            content="Draft article content.",
            author=self.journalist,
            journalist=self.journalist,
            status=Article.Status.PENDING,
        )

        # Create approved article from another publisher
        self.other_article = Article.objects.create(
            title="Other Approved Article",
            content="Article from another publisher.",
            author=self.other_journalist,
            journalist=self.other_journalist,
            publisher=self.other_publisher,
            status=Article.Status.APPROVED,
        )

    def authenticate(self, user):
        """Authenticate API requests as the specified user."""
        self.client.force_authenticate(user=user)

    def response_results(self, response):
        """Return paginated or non-paginated response data."""
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    # Test 1: Authenticated Access Per Role
    def test_authenticated_access_per_role(self):
        """Authenticated users should access the article list."""

        for user in [
            self.reader,
            self.journalist,
            self.editor,
        ]:
            self.authenticate(user)

            response = self.client.get(
                reverse("news:article-api-list")
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
            )

    # Test 2: Reader Retrieves Approved Articles
    def test_reader_only_sees_approved_articles(self):
        """Readers should retrieve approved articles only."""

        self.authenticate(self.reader)

        response = self.client.get(
            reverse("news:article-api-list")
        )

        results = self.response_results(
            response
        )

        returned_ids = {
            article["id"]
            for article in results
        }

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            self.approved_article.id,
            returned_ids,
        )

        self.assertIn(
            self.other_article.id,
            returned_ids,
        )

        self.assertNotIn(
            self.draft_article.id,
            returned_ids,
        )

    # Test 3: Reader Cannot See Drafts
    def test_reader_cannot_retrieve_draft_article(self):
        """Readers should not retrieve draft articles."""

        self.authenticate(self.reader)

        response = self.client.get(
            reverse(
                "news:article-api-detail",
                kwargs={
                    "pk": self.draft_article.id
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # Test 4: Journalist Can Create
    def test_journalist_can_create_article(self):
        """Journalists should create articles."""

        self.authenticate(self.journalist)

        response = self.client.post(
        reverse("news:article-api-list"),
        {
            "title": "New Article",
            "content": "Created via API",
            "journalist": self.journalist.id,
        },
        format="json",
    )   
        print(response.data)
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        article = Article.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            article.author,
            self.journalist,
        )

        self.assertEqual(
            article.status,
            Article.Status.PENDING,
        )

    # Test 5: Reader Cannot Create
    def test_reader_cannot_create_article(self):
        """Readers should not create articles."""

        self.authenticate(self.reader)

        response = self.client.post(
            reverse("news:article-api-list"),
            {
                "title": "Unauthorized",
                "content": "Not allowed",
                "journalist": self.journalist.id,
                "publisher": self.publisher.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # Test 6: Journalist Can Update
    def test_journalist_can_update_article(self):
        """Journalists should update their articles."""

        self.authenticate(
            self.journalist
        )

        response = self.client.patch(
            reverse(
                "news:article-api-detail",
                kwargs={
                    "pk": self.draft_article.id
                },
            ),
            {
                "title": "Updated Draft"
            },
            format="json",
        )
        print(response.data)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.draft_article.refresh_from_db()

        self.assertEqual(
            self.draft_article.title,
            "Updated Draft",
        )

    # Test 7: Editor Can Delete
    def test_editor_can_delete_article(self):
        """Editors should delete articles."""

        self.authenticate(self.editor)

        response = self.client.delete(
            reverse(
                "news:article-api-detail",
                kwargs={
                    "pk": self.draft_article.id
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Article.objects.filter(
                id=self.draft_article.id
            ).exists()
        )

    # Test 8: Reader Cannot Delete
    def test_reader_cannot_delete_article(self):
        """Readers should not delete articles."""

        self.authenticate(self.reader)

        response = self.client.delete(
            reverse(
                "news:article-api-detail",
                kwargs={
                    "pk": self.approved_article.id
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # Test 9: Editor Can Approve
    def test_editor_can_approve_article(self):
        """Editors should approve articles."""

        self.authenticate(self.editor)

        response = self.client.post(
            reverse(
                "news:article-api-approve",
                kwargs={
                    "pk": self.draft_article.id
                },
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.draft_article.refresh_from_db()

        self.assertEqual(
            self.draft_article.status,
            Article.Status.APPROVED,
        )

    # Test 10: Journalist Cannot Approve
    def test_journalist_cannot_approve_article(self):
        """Journalists should not approve articles."""

        self.authenticate(
            self.journalist
        )

        response = self.client.post(
            reverse(
                "news:article-api-approve",
                kwargs={
                    "pk": self.draft_article.id
                },
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.draft_article.refresh_from_db()

        self.assertEqual(
            self.draft_article.status,
            Article.Status.PENDING,
        )
