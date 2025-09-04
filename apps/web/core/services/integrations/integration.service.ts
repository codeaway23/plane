import { API_BASE_URL } from "@plane/constants";
import { IAppIntegration, IImporterService, IWorkspaceIntegration, IExportServiceResponse } from "@plane/types";
import { APIService } from "@/services/api.service";
// types
// helper

export class IntegrationService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async getAppIntegrationsList(): Promise<IAppIntegration[]> {
    // Fallback to hardcoded list for community edition
    return Promise.resolve([
      {
        id: "github",
        title: "GitHub",
        provider: "github",
        network: 1,
        description: { en: "Connect and sync your GitHub repositories with Plane" },
        author: "Plane",
        webhook_url: "",
        webhook_secret: "",
        redirect_url: "",
        metadata: {},
        verified: true,
        avatar_url: "/logos/github-square.png",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: "slack",
        title: "Slack",
        provider: "slack",
        network: 1,
        description: { en: "Connect your Slack workspace with Plane" },
        author: "Plane",
        webhook_url: "",
        webhook_secret: "",
        redirect_url: "",
        metadata: {},
        verified: true,
        avatar_url: "/services/slack.png",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);
  }

  async getWorkspaceIntegrationsList(workspaceSlug: string): Promise<IWorkspaceIntegration[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/workspace-integrations/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteWorkspaceIntegration(workspaceSlug: string, integrationId: string): Promise<any> {
    return this.delete(`/api/workspaces/${workspaceSlug}/workspace-integrations/${integrationId}/`)
      .then((res) => res?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async getImporterServicesList(workspaceSlug: string): Promise<IImporterService[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/importers/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
  async getExportsServicesList(
    workspaceSlug: string,
    cursor: string,
    per_page: number
  ): Promise<IExportServiceResponse> {
    return this.get(`/api/workspaces/${workspaceSlug}/export-issues`, {
      params: {
        per_page,
        cursor,
      },
    })
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteImporterService(workspaceSlug: string, service: string, importerId: string): Promise<any> {
    return this.delete(`/api/workspaces/${workspaceSlug}/importers/${service}/${importerId}/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}
