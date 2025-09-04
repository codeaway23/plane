import { COMMUNITY_EDITION_INTEGRATIONS } from "../constants/integrations";
import { IAppIntegration } from "@plane/types";

export class CommunityEditionIntegrationService {
  /**
   * Get list of available integrations for community edition
   */
  getAppIntegrationsList(): IAppIntegration[] {
    return Object.entries(COMMUNITY_EDITION_INTEGRATIONS)
      .filter(([_, config]) => config.enabled)
      .map(([provider, config]) => ({
        id: provider,
        title: config.name,
        provider: config.provider,
        network: 1,
        description: { en: config.description },
        author: "Plane Community Edition",
        webhook_url: "",
        webhook_secret: "",
        redirect_url: "",
        metadata: {
          features: config.features,
          setup: config.setup,
        },
        verified: true,
        avatar_url: config.icon,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }));
  }

  /**
   * Check if an integration is enabled
   */
  isIntegrationEnabled(provider: string): boolean {
    return COMMUNITY_EDITION_INTEGRATIONS[provider as keyof typeof COMMUNITY_EDITION_INTEGRATIONS]?.enabled ?? false;
  }

  /**
   * Get integration configuration
   */
  getIntegrationConfig(provider: string) {
    return COMMUNITY_EDITION_INTEGRATIONS[provider as keyof typeof COMMUNITY_EDITION_INTEGRATIONS];
  }
}
