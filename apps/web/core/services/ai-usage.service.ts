/**
 * AI Usage service for managing AI usage subscriptions and billing
 */

import { API_BASE_URL } from "@plane/constants";

export interface AIPlan {
  type: string;
  name: string;
  price_id: string;
  cost_per_unit: number;
  description: string;
  unit_name: string;
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

export interface AISubscription {
  active: boolean;
  subscription?: {
    id: string;
    status: string;
    current_period_start: number;
    current_period_end: number;
    cancel_at_period_end: boolean;
    canceled_at?: number;
    created: number;
    subscription_item_id: string;
    quantity: number;
    price_id: string;
  };
}

export interface AIUsageData {
  general_run: AISubscription;
  code_run: AISubscription;
}

export interface CheckoutSessionData {
  id: string;
  url: string;
  status: string;
  payment_status: string;
  plan_type: string;
  plan_name: string;
}

export interface UsageRecord {
  id: string;
  plan_type: string;
  plan_type_display: string;
  usage_count: number;
  cost_per_unit: number;
  total_cost: number;
  created_at: string;
  metadata: Record<string, any>;
}

export interface UsageHistory {
  usage_records: UsageRecord[];
  total_usage_count: number;
  total_cost: number;
}

class AIUsageServiceClass {
  private getHeaders() {
    return {
      "Content-Type": "application/json",
      "X-CSRFToken": this.getCSRFToken(),
    };
  }

  private getCSRFToken(): string {
    const token = document.querySelector("[name=csrfmiddlewaretoken]") as HTMLInputElement;
    return token?.value || "";
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  /**
   * Get available AI usage plans
   */
  async getPlans(workspaceSlug: string): Promise<Record<string, AIPlan>> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-usage/plans/`, {
      method: "GET",
      headers: this.getHeaders(),
      credentials: "include",
    });

    return this.handleResponse<Record<string, AIPlan>>(response);
  }

  /**
   * Get current AI usage subscriptions for workspace
   */
  async getSubscriptions(workspaceSlug: string): Promise<AIUsageData> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-usage/subscriptions/`, {
      method: "GET",
      headers: this.getHeaders(),
      credentials: "include",
    });

    return this.handleResponse<AIUsageData>(response);
  }

  /**
   * Create checkout session for AI usage subscription
   */
  async createCheckoutSession(
    workspaceSlug: string,
    planType: string,
    successUrl?: string,
    cancelUrl?: string
  ): Promise<CheckoutSessionData> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-usage/checkout/`, {
      method: "POST",
      headers: this.getHeaders(),
      credentials: "include",
      body: JSON.stringify({
        plan_type: planType,
        success_url: successUrl,
        cancel_url: cancelUrl,
      }),
    });

    return this.handleResponse<CheckoutSessionData>(response);
  }

  /**
   * Cancel AI usage subscription
   */
  async cancelSubscription(workspaceSlug: string, planType: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-usage/subscriptions/cancel/`, {
      method: "POST",
      headers: this.getHeaders(),
      credentials: "include",
      body: JSON.stringify({
        plan_type: planType,
      }),
    });

    await this.handleResponse<void>(response);
  }

  /**
   * Restart cancelled AI usage subscription
   */
  async restartSubscription(workspaceSlug: string, planType: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-usage/subscriptions/restart/`, {
      method: "POST",
      headers: this.getHeaders(),
      credentials: "include",
      body: JSON.stringify({
        plan_type: planType,
      }),
    });

    await this.handleResponse<void>(response);
  }

  /**
   * Get AI usage history
   */
  async getUsageHistory(workspaceSlug: string, planType?: string, limit: number = 50): Promise<UsageHistory> {
    const params = new URLSearchParams();
    if (planType) params.append("plan_type", planType);
    params.append("limit", limit.toString());

    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-usage/history/?${params}`, {
      method: "GET",
      headers: this.getHeaders(),
      credentials: "include",
    });

    return this.handleResponse<UsageHistory>(response);
  }

  /**
   * Record AI usage (for internal use by AI features)
   */
  async recordUsage(
    workspaceSlug: string,
    planType: string,
    usageCount: number = 1,
    metadata: Record<string, any> = {}
  ): Promise<{
    success: boolean;
    usage_record_id: string;
    stripe_usage_record_id: string;
    usage_count: number;
    total_cost: number;
  }> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceSlug}/ai-usage/record/`, {
      method: "POST",
      headers: this.getHeaders(),
      credentials: "include",
      body: JSON.stringify({
        plan_type: planType,
        usage_count: usageCount,
        metadata,
      }),
    });

    return this.handleResponse(response);
  }
}

export const AIUsageService = new AIUsageServiceClass();
