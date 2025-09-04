# Python imports
from rest_framework import serializers

# Module imports
from plane.db.models import (
    WorkspaceIntegration,
    Integration,
    GithubRepository,
    GithubRepositorySync,
)


class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = [
            "id",
            "title",
            "provider",
            "network",
            "description",
            "author",
            "webhook_url",
            "webhook_secret",
            "redirect_url",
            "metadata",
            "verified",
            "avatar_url",
        ]


class WorkspaceIntegrationSerializer(serializers.ModelSerializer):
    integration = IntegrationSerializer(read_only=True)
    
    class Meta:
        model = WorkspaceIntegration
        fields = [
            "id",
            "workspace",
            "integration",
            "actor",
            "api_token",
            "metadata",
            "config",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GithubRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GithubRepository
        fields = [
            "id",
            "name",
            "url",
            "config",
            "repository_id",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GithubRepositorySyncSerializer(serializers.ModelSerializer):
    repository = GithubRepositorySerializer(read_only=True)
    
    class Meta:
        model = GithubRepositorySync
        fields = [
            "id",
            "repository",
            "credentials",
            "actor",
            "workspace_integration",
            "label",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
