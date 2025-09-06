import { WorkspaceService } from "@/services/workspace.service";

const workspaceService = new WorkspaceService();

/**
 * Verify if the current user has access to a workspace
 * @param workspaceSlug - The workspace slug to check
 * @returns Promise<boolean> - True if user has access, false otherwise
 */
export const verifyWorkspaceAccess = async (workspaceSlug: string): Promise<boolean> => {
  try {
    // Try to fetch workspace details
    await workspaceService.getWorkspace(workspaceSlug);
    return true;
  } catch (error) {
    console.error(`User does not have access to workspace ${workspaceSlug}:`, error);
    return false;
  }
};

/**
 * Safely redirect to a workspace with access verification
 * @param workspaceSlug - The workspace slug to redirect to
 * @param router - Next.js router instance
 * @param fallbackPath - Fallback path if access is denied (default: "/")
 */
export const safeRedirectToWorkspace = async (
  workspaceSlug: string,
  router: any,
  fallbackPath: string = "/"
): Promise<void> => {
  try {
    const hasAccess = await verifyWorkspaceAccess(workspaceSlug);

    if (hasAccess) {
      router.push(`/${workspaceSlug}`);
    } else {
      console.warn(`Access denied to workspace ${workspaceSlug}, redirecting to ${fallbackPath}`);
      router.push(fallbackPath);
    }
  } catch (error) {
    console.error(`Error verifying workspace access for ${workspaceSlug}:`, error);
    router.push(fallbackPath);
  }
};
