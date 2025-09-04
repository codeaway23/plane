# Frontend GitHub Integration Guide

This guide explains how the GitHub integration works in the Plane Community Edition frontend.

## Overview

The frontend GitHub integration consists of several components and services that work together to provide a seamless experience for connecting and managing GitHub repositories with Plane projects.

## Architecture

### Services Layer

#### 1. IntegrationService (`/core/services/integrations/integration.service.ts`)

- **Purpose**: Manages workspace integrations
- **Key Methods**:
  - `getAppIntegrationsList()`: Returns available integrations (GitHub, Slack)
  - `getWorkspaceIntegrationsList()`: Gets integrations for a workspace
  - `deleteWorkspaceIntegration()`: Removes an integration

#### 2. GithubIntegrationService (`/core/services/integrations/github.service.ts`)

- **Purpose**: Handles GitHub-specific operations
- **Key Methods**:
  - `listAllRepositories()`: Fetches GitHub repositories
  - `getGithubRepoInfo()`: Gets repository details
  - `createGithubServiceImport()`: Imports GitHub data

#### 3. ProjectService (`/core/services/project/project.service.ts`)

- **Purpose**: Manages project-related GitHub operations
- **Key Methods**:
  - `syncGithubRepository()`: Syncs a repository with a project
  - `getProjectGithubRepository()`: Gets synced repository info
  - `getGithubRepositories()`: Fetches repositories via URL

#### 4. AppInstallationService (`/core/services/app_installation.service.ts`)

- **Purpose**: Handles app installation and configuration
- **Key Methods**:
  - `addInstallationApp()`: Creates new workspace integration
  - `addSlackChannel()`: Configures Slack integration
  - `removeSlackChannel()`: Removes Slack integration

### Components Layer

#### 1. IntegrationCard (`/core/components/project/integration-card.tsx`)

- **Purpose**: Displays integration status and controls
- **Features**:
  - Shows integration logo and description
  - Provides repository selection for GitHub
  - Handles sync operations

#### 2. SelectRepository (`/core/components/integration/github/select-repository.tsx`)

- **Purpose**: Repository selection dropdown
- **Features**:
  - Infinite scroll pagination
  - Search functionality
  - Repository filtering

#### 3. GithubImporterRoot (`/core/components/integration/github/root.tsx`)

- **Purpose**: Main GitHub import workflow
- **Features**:
  - Multi-step import process
  - User mapping
  - Configuration options

#### 4. GithubAuth (`/core/components/integration/github/auth.tsx`)

- **Purpose**: GitHub authentication component
- **Features**:
  - OAuth flow initiation
  - Connection status display

### Community Edition Configuration

#### 1. Integration Constants (`/ce/constants/integrations.ts`)

- **Purpose**: Defines available integrations for CE
- **Configuration**:
  - Integration metadata
  - Feature lists
  - Setup requirements

#### 2. Community Edition Service (`/ce/services/integration.service.ts`)

- **Purpose**: CE-specific integration management
- **Features**:
  - Integration availability checking
  - Configuration retrieval
  - Feature validation

## API Integration

### Endpoints Used

1. **Workspace Integrations**:
   - `GET /api/workspaces/{slug}/workspace-integrations/`
   - `POST /api/workspaces/{slug}/workspace-integrations/`
   - `DELETE /api/workspaces/{slug}/workspace-integrations/{id}/`

2. **GitHub Repositories**:
   - `GET /api/workspaces/{slug}/workspace-integrations/{id}/github-repositories/`

3. **Repository Sync**:
   - `POST /api/workspaces/{slug}/projects/{id}/workspace-integrations/{id}/github-repository-sync/`
   - `DELETE /api/workspaces/{slug}/projects/{id}/workspace-integrations/{id}/github-repository-sync/`

### Data Flow

1. **Integration Setup**:

   ```
   User clicks "Connect GitHub" → OAuth flow → Integration created → Repository list fetched
   ```

2. **Repository Sync**:

   ```
   User selects repository → Sync request sent → Repository linked to project → Status updated
   ```

3. **Data Import**:
   ```
   User initiates import → Repository data fetched → Issues/PRs imported → Users mapped
   ```

## Usage Examples

### 1. Setting up GitHub Integration

```typescript
// In a React component
import { IntegrationService } from "@/services/integrations";

const integrationService = new IntegrationService();

// Get available integrations
const integrations = await integrationService.getAppIntegrationsList();

// Get workspace integrations
const workspaceIntegrations =
  await integrationService.getWorkspaceIntegrationsList(workspaceSlug);
```

### 2. Syncing a Repository

```typescript
// In a React component
import { ProjectService } from "@/services/project";

const projectService = new ProjectService();

// Sync repository with project
await projectService.syncGithubRepository(
  workspaceSlug,
  projectId,
  integrationId,
  {
    name: "my-repo",
    owner: "username",
    repository_id: "12345",
    url: "https://github.com/username/my-repo",
  }
);
```

### 3. Fetching GitHub Repositories

```typescript
// In a React component
import { GithubIntegrationService } from "@/services/integrations";

const githubService = new GithubIntegrationService();

// Get repositories
const repositories = await githubService.listAllRepositories(
  workspaceSlug,
  integrationId
);
```

## Error Handling

The services include comprehensive error handling:

```typescript
try {
  const result =
    await integrationService.getWorkspaceIntegrationsList(workspaceSlug);
} catch (error) {
  // Error is automatically handled by the service
  console.error("Integration error:", error);
}
```

## Testing

### Frontend Integration Test

Run the test script to verify all components are properly configured:

```bash
node test_frontend_integration.js
```

### Manual Testing

1. **Start the development server**:

   ```bash
   npm run dev
   ```

2. **Navigate to workspace settings**:
   - Go to your workspace
   - Click on Settings
   - Navigate to Integrations

3. **Test GitHub integration**:
   - Click on GitHub integration
   - Follow the OAuth flow
   - Select a repository
   - Verify sync works

## Troubleshooting

### Common Issues

1. **Integration not showing**:
   - Check if GitHub OAuth is configured
   - Verify environment variables
   - Check browser console for errors

2. **Repository sync fails**:
   - Verify GitHub token has repository access
   - Check API endpoint responses
   - Ensure project exists

3. **Authentication issues**:
   - Clear browser cache
   - Check OAuth configuration
   - Verify redirect URLs

### Debug Mode

Enable debug logging by setting:

```javascript
localStorage.setItem("debug", "plane:*");
```

## Future Enhancements

- [ ] Real-time sync status updates
- [ ] Bulk repository operations
- [ ] Advanced filtering options
- [ ] Webhook configuration
- [ ] Custom field mapping

## Contributing

When contributing to the frontend integration:

1. Follow the existing code patterns
2. Add proper TypeScript types
3. Include error handling
4. Update tests
5. Document new features

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the browser console
3. Check the network tab for API errors
4. Create an issue in the repository
