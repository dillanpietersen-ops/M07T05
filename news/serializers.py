"""REST API serializers for the news application.
Making approved read-only prevents a journalist from approving an
article through crafted JSON.
"""

from rest_framework import serializers
from .models import Article, CustomUser


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize and validate article data."""
    author = serializers.StringRelatedField(read_only=True)
    approved = serializers.BooleanField(read_only=True)

    class Meta:
        """Configure serialized article fields."""
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "journalist",
            "publisher",
            "created_at",
            "approved",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "approved",
        ]

    def validate(self, attrs):
        """Validate journalist and publisher source selection."""
        journalist = attrs.get(
            "journalist",
            getattr(self.instance, "journalist", None),
        )
        publisher = attrs.get(
            "publisher",
            getattr(self.instance, "publisher", None),
        )
        if bool(journalist) == bool(publisher):
            raise serializers.ValidationError(
                "Select either a journalist or publisher, "
                "but not both."
            )
        return attrs

    def create(self, validated_data):
        """Create an unapproved article for the authenticated journalist."""
        request = self.context["request"]
        if request.user.role != CustomUser.Role.JOURNALIST:
            raise serializers.ValidationError(
                "Only journalists may create articles."
            )
        validated_data["author"] = request.user
        validated_data["status"] = Article.Status.PENDING
        return super().create(validated_data)
