# Python imports
import requests
from typing import Dict, Any

# Django imports
from django.db import IntegrityError
from django.utils import timezone

# Third party imports
from rest_framework import status
from rest_framework.response import Response

# Module imports
from plane.app.views.base import BaseViewSet, BaseAPIView
from plane.app.serializers import WorkspaceIntegrationSerializer
from plane.app.permissions import WorkSpaceAdminPermission, allow_permission, ROLE
from plane.db.models import (
    Workspace,
    WorkspaceIntegration,
    Integration,
    APIToken,
    User,
)
from plane.utils.exception_logger import log_exception


class WorkspaceIntegrationViewSet(BaseViewSet):
    model = WorkspaceIntegration
    serializer_class = WorkspaceIntegrationSerializer
    permission_classes = [WorkSpaceAdminPermission]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("slug"))
            .select_related("integration", "actor", "api_token")
        )

    def create(self, request, slug):
        try:
            workspace = Workspace.objects.get(slug=slug)
            
            # Get integration provider
            provider = request.data.get("provider")
            if not provider:
                return Response(
                    {"error": "Provider is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get or create integration
            integration, _ = Integration.objects.get_or_create(
                provider=provider,
                defaults={
                    "title": provider.title(),
                    "description": {"en": f"Integration with {provider.title()}"},
                    "verified": True,
                }
            )

            # Create API token for the integration
            api_token = APIToken.objects.create(
                user=request.user,
                name=f"{provider.title()} Integration",
                description=f"API token for {provider.title()} integration",
            )

            # Create workspace integration
            workspace_integration = WorkspaceIntegration.objects.create(
                workspace=workspace,
                integration=integration,
                actor=request.user,
                api_token=api_token,
                metadata=request.data.get("metadata", {}),
                config=request.data.get("config", {}),
            )

            serializer = WorkspaceIntegrationSerializer(workspace_integration)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except IntegrityError:
            return Response(
                {"error": "Integration already exists for this workspace"},
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            log_exception(e)
            return Response(
                {"error": "Failed to create integration"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def destroy(self, request, slug, pk):
        try:
            workspace_integration = self.get_object()
            workspace_integration.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            log_exception(e)
            return Response(
                {"error": "Failed to delete integration"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
