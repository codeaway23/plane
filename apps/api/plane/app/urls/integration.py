from django.urls import path

from plane.app.views import (
    WorkspaceIntegrationViewSet,
    WorkspaceIntegrationGithubRepositoriesEndpoint,
    ProjectGithubRepositorySyncEndpoint,
)

urlpatterns = [
    # Workspace Integrations
    path(
        "workspaces/<str:slug>/workspace-integrations/",
        WorkspaceIntegrationViewSet.as_view({"get": "list", "post": "create"}),
        name="workspace-integrations",
    ),
    path(
        "workspaces/<str:slug>/workspace-integrations/<uuid:pk>/",
        WorkspaceIntegrationViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="workspace-integrations-detail",
    ),
    # GitHub Integration
    path(
        "workspaces/<str:slug>/workspace-integrations/<uuid:integration_id>/github-repositories/",
        WorkspaceIntegrationGithubRepositoriesEndpoint.as_view(),
        name="workspace-integration-github-repositories",
    ),
    # Project GitHub Repository Sync
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/workspace-integrations/<uuid:integration_id>/github-repository-sync/",
        ProjectGithubRepositorySyncEndpoint.as_view(),
        name="project-github-repository-sync",
    ),
]
