import { API_BASE_URL } from "@plane/constants";

export interface AIPackPlan {
  type: string;
  name: string;
  price_id: string;
  monthly_price: number;
  general_runs: number;
  code_runs: number;
  description: string;
  stripe_price?: {
    id: string;
    unit_amount: number;
    currency: string;
    active: boolean;
  };
  stripe_product?: {
    id: string;
    name: string;
    description: string;
    active: boolean;
  };
  error?: string;
}

export interface AIPackSubscription {
  active: boolean;
  subscription?: {
    id: string;
    status: string;
    current_period_start: number;
    current_period_end: number;
    cancel_at_period_end: boolean;
    customer: string;
    price_id: string;
  };
  pack_type?: string;
  pack_config?: {
    name: string;
    monthly_price: number;
    general_runs: number;
    code_runs: number;
    description: string;
  };
}

export interface CheckoutSessionData {
  id: string;
  url: string;
  pack_type: string;
  pack_config: {
    name: string;
    monthly_price: number;
    general_runs: number;
    code_runs: number;
    description: string;
  };
}

export interface AIPackUsageLimits {
  has_subscription: boolean;
  general_runs_limit: number;
  code_runs_limit: number;
  pack_type?: string;
  pack_name?: string;
}

class AIPackServiceClass {
  private getHeaders() {
    return {
      "Content-Type": "application/json",
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  /**
   * Get available AI Pack plans
   */
  async getPlans(workspaceSlug: string): Promise<Record<string, AIPackPlan>> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-packs/plans/`, {
      method: "GET",
      headers: this.getHeaders(),
      credentials: "include",
    });

    return this.handleResponse<Record<string, AIPackPlan>>(response);
  }

  /**
   * Get current AI Pack subscription for workspace
   */
  async getSubscription(workspaceSlug: string): Promise<AIPackSubscription> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-packs/subscription/`, {
      method: "GET",
      headers: this.getHeaders(),
      credentials: "include",
    });

    return this.handleResponse<AIPackSubscription>(response);
  }

  /**
   * Create checkout session for AI Pack subscription
   */
  async createCheckoutSession(
    workspaceSlug: string,
    packType: string,
    successUrl?: string,
    cancelUrl?: string
  ): Promise<CheckoutSessionData> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-packs/checkout/`, {
      method: "POST",
      headers: this.getHeaders(),
      credentials: "include",
      body: JSON.stringify({
        pack_type: packType,
      }),
    });

    return this.handleResponse<CheckoutSessionData>(response);
  }

  /**
   * Cancel AI Pack subscription
   */
  async cancelSubscription(
    workspaceSlug: string
  ): Promise<{ success: boolean; subscription_id: string; cancel_at_period_end: boolean; current_period_end: number }> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-packs/subscription/cancel/`, {
      method: "POST",
      headers: this.getHeaders(),
      credentials: "include",
    });

    return this.handleResponse<{
      success: boolean;
      subscription_id: string;
      cancel_at_period_end: boolean;
      current_period_end: number;
    }>(response);
  }

  /**
   * Restart AI Pack subscription
   */
  async restartSubscription(
    workspaceSlug: string
  ): Promise<{ success: boolean; subscription_id: string; cancel_at_period_end: boolean; current_period_end: number }> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-packs/subscription/restart/`, {
      method: "POST",
      headers: this.getHeaders(),
      credentials: "include",
    });

    return this.handleResponse<{
      success: boolean;
      subscription_id: string;
      cancel_at_period_end: boolean;
      current_period_end: number;
    }>(response);
  }

  /**
   * Upgrade AI Pack subscription
   */
  async upgradeSubscription(
    workspaceSlug: string,
    packType: string,
    successUrl?: string,
    cancelUrl?: string
  ): Promise<CheckoutSessionData> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-packs/upgrade/`, {
      method: "POST",
      headers: this.getHeaders(),
      credentials: "include",
      body: JSON.stringify({
        pack_type: packType,
      }),
    });

    return this.handleResponse<CheckoutSessionData>(response);
  }

  /**
   * Get AI Pack usage limits
   */
  async getUsageLimits(workspaceSlug: string): Promise<AIPackUsageLimits> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-packs/usage-limits/`, {
      method: "GET",
      headers: this.getHeaders(),
      credentials: "include",
    });

    return this.handleResponse<AIPackUsageLimits>(response);
  }
}

export const AIPackService = new AIPackServiceClass();
