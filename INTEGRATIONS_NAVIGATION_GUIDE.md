# Integrations Navigation Implementation Guide

This guide explains how the GitHub integration navigation has been implemented in the Plane Community Edition to make it accessible through the settings page.

## Problem Solved

The GitHub integration was not visible in the workspace settings navigation for localhost deployments, even though it was available in the production version. Users couldn't access the integrations page through the settings menu.

## Solution Implemented

### 1. **Updated Constants Configuration**

#### Workspace Settings (`packages/constants/src/workspace.ts`)

Added the integrations setting to the workspace settings:

```typescript
integrations: {
  key: "integrations",
  i18n_label: "workspace_settings.settings.integrations.title",
  href: `/settings/integrations`,
  access: [EUserWorkspaceRoles.ADMIN],
  highlight: (pathname: string, baseUrl: string) => pathname === `${baseUrl}/settings/integrations/`,
},
```

#### Settings Categories (`packages/constants/src/settings.ts`)

Added integrations to the Features category:

```typescript
export const GROUPED_WORKSPACE_SETTINGS = {
  [WORKSPACE_SETTINGS_CATEGORY.ADMINISTRATION]: [
    WORKSPACE_SETTINGS["general"],
    WORKSPACE_SETTINGS["members"],
    WORKSPACE_SETTINGS["billing-and-plans"],
    WORKSPACE_SETTINGS["export"],
  ],
  [WORKSPACE_SETTINGS_CATEGORY.FEATURES]: [WORKSPACE_SETTINGS["integrations"]],
  [WORKSPACE_SETTINGS_CATEGORY.DEVELOPER]: [WORKSPACE_SETTINGS["webhooks"]],
};
```

### 2. **Updated Sidebar Component**

#### Workspace Settings Sidebar (`apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/sidebar.tsx`)

Added the Plug icon for integrations:

```typescript
import {
  ArrowUpToLine,
  Building,
  CreditCard,
  Users,
  Webhook,
  Plug,
} from "lucide-react";

const ICONS = {
  general: Building,
  members: Users,
  export: ArrowUpToLine,
  "billing-and-plans": CreditCard,
  integrations: Plug,
  webhooks: Webhook,
};
```

### 3. **Created Integrations Page**

#### Integrations Page (`apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/integrations/page.tsx`)

Created a comprehensive integrations page that includes:

- **GitHub Integration**: Repository synchronization, issue tracking, pull request management
- **Slack Integration**: Channel notifications, issue updates, project updates
- **GitLab Integration**: Merge request sync, issue tracking, user mapping

**Key Features**:

- Integration status display (Connected/Not Connected)
- Connect/Disconnect functionality
- Feature lists for each integration
- Loading states and error handling
- Responsive grid layout

### 4. **Added Translations**

#### English Translations (`packages/i18n/src/locales/en/translations.json`)

Added the integrations title:

```json
"integrations": {
  "title": "Integrations"
},
```

## Navigation Structure

The integrations page is now accessible through:

```
Workspace Settings → Features → Integrations
```

**Navigation Path**:

1. Go to workspace settings
2. Click on "Features" tab
3. Click on "Integrations"
4. View and manage available integrations

## Integration Cards

Each integration card displays:

- **Logo**: Service-specific logo (GitHub, Slack, GitLab)
- **Title**: Integration name with Beta badge for GitHub
- **Description**: What the integration does
- **Features**: List of available features
- **Status**: Connected/Not Connected
- **Action Button**: Connect/Disconnect

## User Experience

### For Administrators

- Can view all available integrations
- Can connect/disconnect integrations
- Can see integration status at a glance
- Can understand what each integration offers

### For Regular Users

- Cannot access integrations (Admin-only feature)
- Will not see the integrations option in settings

## Technical Implementation

### File Structure

```
packages/constants/src/
├── workspace.ts          # Workspace settings definitions
└── settings.ts           # Settings categories

apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/
├── sidebar.tsx           # Settings sidebar with integrations icon
└── integrations/
    └── page.tsx          # Integrations page component

packages/i18n/src/locales/en/
└── translations.json     # English translations
```

### API Integration

The integrations page uses the existing services:

- `IntegrationService` for managing workspace integrations
- `GithubIntegrationService` for GitHub-specific operations
- `AppInstallationService` for installation management

### State Management

- Uses SWR for data fetching and caching
- Handles loading states and error states
- Provides real-time updates when integrations change

## Testing

### Automated Testing

Run the navigation test script:

```bash
node test_integrations_navigation.js
```

This script verifies:

- Constants are properly configured
- Sidebar component has integrations icon
- Integrations page exists with required content
- Translations are updated

### Manual Testing

1. Start the development server
2. Navigate to workspace settings
3. Look for "Integrations" in the Features section
4. Click on Integrations to see the page
5. Test connect/disconnect functionality

## Future Enhancements

### Planned Features

- [ ] Real-time integration status updates
- [ ] Integration configuration options
- [ ] Bulk integration management
- [ ] Integration health monitoring
- [ ] Custom integration support

### Additional Integrations

- [ ] Jira integration
- [ ] Linear integration
- [ ] Asana integration
- [ ] Trello integration

## Troubleshooting

### Common Issues

1. **Integrations not showing in settings**:
   - Check if user has admin permissions
   - Verify constants are properly configured
   - Check browser console for errors

2. **Integration page not loading**:
   - Verify the page file exists
   - Check for TypeScript errors
   - Ensure all dependencies are installed

3. **Connect/Disconnect not working**:
   - Check API endpoints are accessible
   - Verify authentication is working
   - Check network tab for API errors

### Debug Mode

Enable debug logging:

```javascript
localStorage.setItem("debug", "plane:*");
```

## Security Considerations

- Only workspace admins can access integrations
- OAuth flows are handled securely
- API tokens are managed securely
- Integration data is properly validated

## Performance Considerations

- Lazy loading of integration components
- Efficient data fetching with SWR
- Minimal re-renders with proper state management
- Optimized bundle size

## Conclusion

The integrations navigation has been successfully implemented, providing users with easy access to manage their workspace integrations through the settings page. The implementation follows Plane's design patterns and provides a seamless user experience for both connecting and managing integrations.

The GitHub integration is now fully accessible and functional in the Community Edition, matching the experience available in the production version.
