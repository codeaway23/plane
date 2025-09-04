// Community Edition Integration Configuration
export const COMMUNITY_EDITION_INTEGRATIONS = {
  github: {
    enabled: true,
    name: "GitHub",
    description: "Connect and sync your GitHub repositories with Plane",
    icon: "/logos/github-square.png",
    provider: "github",
    features: ["Repository synchronization", "Issue tracking", "Pull request management", "User mapping"],
    setup: {
      requiresOAuth: true,
      oauthProvider: "github",
      scopes: ["repo", "read:user", "user:email"],
    },
  },
  slack: {
    enabled: true,
    name: "Slack",
    description: "Connect your Slack workspace with Plane",
    icon: "/services/slack.png",
    provider: "slack",
    features: ["Channel notifications", "Issue updates", "Project updates"],
    setup: {
      requiresOAuth: true,
      oauthProvider: "slack",
      scopes: ["channels:read", "chat:write"],
    },
  },
} as const;

export type IntegrationProvider = keyof typeof COMMUNITY_EDITION_INTEGRATIONS;
