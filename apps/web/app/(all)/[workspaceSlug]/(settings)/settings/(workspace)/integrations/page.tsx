"use client";

import { useState } from "react";
import { observer } from "mobx-react";
import Image from "next/image";
import { useParams } from "next/navigation";
import useSWR from "swr";
import { Button } from "@plane/ui";
// components
import { EmptyState } from "@/components/common/empty-state";
// constants
import { WORKSPACE_INTEGRATIONS } from "@/constants/fetch-keys";
// services
import { IntegrationService } from "@/services/integrations";
// images
import GithubLogo from "@/public/logos/github-square.png";
import SlackLogo from "@/public/services/slack.png";
import GitlabLogo from "@/public/logos/gitlab-logo.svg";

const integrationDetails: { [key: string]: any } = {
  github: {
    logo: GithubLogo,
    title: "GitHub",
    description: "Connect and sync your GitHub repositories with Plane",
    features: ["Repository synchronization", "Issue tracking", "Pull request management"],
  },
  slack: {
    logo: SlackLogo,
    title: "Slack",
    description: "Connect your Slack workspace with Plane",
    features: ["Channel notifications", "Issue updates", "Project updates"],
  },
  gitlab: {
    logo: GitlabLogo,
    title: "GitLab",
    description: "Connect and sync your GitLab merge requests with Plane",
    features: ["Merge request sync", "Issue tracking", "User mapping"],
  },
};

const integrationService = new IntegrationService();

const IntegrationsPage = observer(() => {
  const { workspaceSlug } = useParams();
  const [isConnecting, setIsConnecting] = useState<string | null>(null);

  const { data: workspaceIntegrations, mutate } = useSWR(
    workspaceSlug ? WORKSPACE_INTEGRATIONS(workspaceSlug as string) : null,
    workspaceSlug ? () => integrationService.getWorkspaceIntegrationsList(workspaceSlug as string) : null
  );

  const { data: appIntegrations } = useSWR("APP_INTEGRATIONS", () => integrationService.getAppIntegrationsList());

  const handleConnect = async (provider: string) => {
    if (!workspaceSlug) return;

    setIsConnecting(provider);
    try {
      // For now, we'll just show a success message
      // In a real implementation, this would trigger the OAuth flow
      console.log(`Connecting to ${provider}...`);

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Refresh the integrations list
      mutate();

      console.log(`Successfully connected to ${provider}`);
    } catch (error) {
      console.error(`Failed to connect to ${provider}:`, error);
    } finally {
      setIsConnecting(null);
    }
  };

  const handleDisconnect = async (integrationId: string) => {
    if (!workspaceSlug) return;

    try {
      await integrationService.deleteWorkspaceIntegration(workspaceSlug as string, integrationId);
      mutate();
    } catch (error) {
      console.error("Failed to disconnect integration:", error);
    }
  };

  const getIntegrationStatus = (provider: string) => {
    if (!workspaceIntegrations) return "not_connected";

    const integration = workspaceIntegrations.find(
      (integration: any) => integration.integration?.provider === provider
    );

    return integration ? "connected" : "not_connected";
  };

  if (!appIntegrations) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-custom-border-200 border-t-custom-primary-100 mx-auto" />
          <p className="mt-2 text-sm text-custom-text-200">Loading integrations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-semibold text-custom-text-100">Integrations</h3>
          <p className="text-sm text-custom-text-200">
            Connect with popular tools and services to sync your work across your entire workflow ecosystem.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {appIntegrations.map((integration: any) => {
            const status = getIntegrationStatus(integration.provider);
            const details = integrationDetails[integration.provider];
            const isConnected = status === "connected";
            const isConnectingToThis = isConnecting === integration.provider;

            return (
              <div
                key={integration.id}
                className="rounded-lg border border-custom-border-200 bg-custom-background-100 p-6"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="h-10 w-10 flex-shrink-0">
                      <Image
                        src={details?.logo || integration.avatar_url}
                        alt={`${integration.title} Logo`}
                        width={40}
                        height={40}
                        className="rounded"
                      />
                    </div>
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-custom-text-100">
                        {integration.title}
                        {integration.provider === "github" && (
                          <span className="ml-2 rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-800">Beta</span>
                        )}
                      </h4>
                      <p className="mt-1 text-xs text-custom-text-200">
                        {details?.description || integration.description?.en}
                      </p>
                    </div>
                  </div>
                </div>

                {details?.features && (
                  <div className="mt-4">
                    <ul className="space-y-1">
                      {details.features.map((feature: string, index: number) => (
                        <li key={index} className="flex items-center text-xs text-custom-text-300">
                          <div className="mr-2 h-1 w-1 rounded-full bg-custom-text-300" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="mt-6">
                  {isConnected ? (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-green-600">Connected</span>
                      <Button
                        variant="outline-primary"
                        size="sm"
                        onClick={() => {
                          if (!workspaceIntegrations) return;
                          const integration = workspaceIntegrations.find(
                            (integration: any) => integration.integration?.provider === integration.provider
                          );
                          if (integration) {
                            handleDisconnect(integration.id);
                          }
                        }}
                      >
                        Disconnect
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleConnect(integration.provider)}
                      loading={isConnectingToThis}
                      className="w-full"
                    >
                      {isConnectingToThis ? "Connecting..." : "Connect"}
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {appIntegrations.length === 0 && (
          <EmptyState
            title="No integrations available"
            description="Integrations will appear here when they are configured for your workspace."
            image="/empty-state/integrations.svg"
          />
        )}
      </div>
    </div>
  );
});

export default IntegrationsPage;
