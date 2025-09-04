# Python imports
import requests
from typing import Dict, Any, List

# Django imports
from django.db import IntegrityError
from django.utils import timezone

# Third party imports
from rest_framework import status
from rest_framework.response import Response

# Module imports
from plane.app.views.base import BaseAPIView
from plane.app.permissions import WorkSpaceAdminPermission, allow_permission, ROLE
from plane.db.models import (
    Workspace,
    WorkspaceIntegration,
    Project,
    GithubRepository,
    GithubRepositorySync,
)
from plane.utils.exception_logger import log_exception


class WorkspaceIntegrationGithubRepositoriesEndpoint(BaseAPIView):
    permission_classes = [WorkSpaceAdminPermission]

    def get(self, request, slug, integration_id):
        try:
            workspace = Workspace.objects.get(slug=slug)
            workspace_integration = WorkspaceIntegration.objects.get(
                id=integration_id,
                workspace=workspace,
                integration__provider="github"
            )

            # Get GitHub repositories using the integration's API token
            api_token = workspace_integration.api_token.token
            headers = {
                "Authorization": f"token {api_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Get repositories for the authenticated user
            response = requests.get(
                "https://api.github.com/user/repos",
                headers=headers,
                params={
                    "per_page": 100,
                    "page": request.GET.get("page", 1),
                    "sort": "updated",
                }
            )

            if response.status_code == 200:
                repositories = response.json()
                return Response(repositories, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Failed to fetch GitHub repositories"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except WorkspaceIntegration.DoesNotExist:
            return Response(
                {"error": "GitHub integration not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            log_exception(e)
            return Response(
                {"error": "Failed to fetch repositories"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProjectGithubRepositorySyncEndpoint(BaseAPIView):
    permission_classes = [WorkSpaceAdminPermission]

    def post(self, request, slug, project_id, integration_id):
        try:
            workspace = Workspace.objects.get(slug=slug)
            project = Project.objects.get(id=project_id, workspace=workspace)
            workspace_integration = WorkspaceIntegration.objects.get(
                id=integration_id,
                workspace=workspace,
                integration__provider="github"
            )

            # Get repository data from request
            repository_data = request.data.get("repository", {})
            if not repository_data:
                return Response(
                    {"error": "Repository data is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create or get GitHub repository
            github_repo, created = GithubRepository.objects.get_or_create(
                project=project,
                repository_id=repository_data.get("id"),
                defaults={
                    "name": repository_data.get("name"),
                    "url": repository_data.get("html_url"),
                    "owner": repository_data.get("owner", {}).get("login"),
                    "config": {},
                }
            )

            # Create repository sync
            github_sync, created = GithubRepositorySync.objects.get_or_create(
                project=project,
                repository=github_repo,
                defaults={
                    "actor": request.user,
                    "workspace_integration": workspace_integration,
                    "credentials": {},
                }
            )

            return Response(
                {
                    "id": github_sync.id,
                    "repository": {
                        "id": github_repo.id,
                        "name": github_repo.name,
                        "url": github_repo.url,
                        "owner": github_repo.owner,
                    },
                    "sync": {
                        "id": github_sync.id,
                        "created": created,
                    }
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )

        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except WorkspaceIntegration.DoesNotExist:
            return Response(
                {"error": "GitHub integration not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            log_exception(e)
            return Response(
                {"error": "Failed to sync repository"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, slug, project_id, integration_id):
        try:
            workspace = Workspace.objects.get(slug=slug)
            project = Project.objects.get(id=project_id, workspace=workspace)
            workspace_integration = WorkspaceIntegration.objects.get(
                id=integration_id,
                workspace=workspace,
                integration__provider="github"
            )

            # Find and delete the repository sync
            github_sync = GithubRepositorySync.objects.get(
                project=project,
                workspace_integration=workspace_integration
            )
            github_sync.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except WorkspaceIntegration.DoesNotExist:
            return Response(
                {"error": "GitHub integration not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except GithubRepositorySync.DoesNotExist:
            return Response(
                {"error": "Repository sync not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            log_exception(e)
            return Response(
                {"error": "Failed to delete repository sync"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
