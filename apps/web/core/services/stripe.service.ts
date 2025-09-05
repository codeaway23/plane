import { loadStripe, Stripe } from "@stripe/stripe-js";
import { APIService } from "./api.service";
import { AuthService } from "./auth.service";

export class StripeService extends APIService {
  private stripePromise: Promise<Stripe | null>;
  private authService: AuthService;

  constructor() {
    super(process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000");
    this.stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || "");
    this.authService = new AuthService();
  }

  /**
   * Get CSRF token for authenticated requests
   */
  private async getCSRFToken(): Promise<string> {
    try {
      const csrfData = await this.authService.requestCSRFToken();
      return csrfData.csrf_token;
    } catch (error) {
      console.error("Failed to get CSRF token:", error);
      throw new Error("Failed to get CSRF token for authentication");
    }
  }

  /**
   * Create a Stripe checkout session
   */
  async createCheckoutSession(
    workspaceSlug: string,
    priceId: string,
    successUrl?: string,
    cancelUrl?: string
  ): Promise<{ id: string; url: string; status: string }> {
    try {
      // Get CSRF token for authenticated request
      const csrfToken = await this.getCSRFToken();

      const response = await this.post(
        `/api/workspaces/${workspaceSlug}/stripe/checkout/`,
        {
          price_id: priceId,
          success_url: successUrl,
          cancel_url: cancelUrl,
        },
        {
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/json",
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error("Error creating checkout session:", error);
      throw error;
    }
  }

  /**
   * Redirect to Stripe checkout
   */
  async redirectToCheckout(
    workspaceSlug: string,
    priceId: string,
    successUrl?: string,
    cancelUrl?: string
  ): Promise<void> {
    try {
      const { url } = await this.createCheckoutSession(workspaceSlug, priceId, successUrl, cancelUrl);

      if (url) {
        window.location.href = url;
      } else {
        throw new Error("No checkout URL received");
      }
    } catch (error) {
      console.error("Error creating checkout session:");
      console.log(error);
      throw error;
    }
  }

  /**
   * Get subscription details
   */
  async getSubscription(
    workspaceSlug: string,
    subscriptionId: string
  ): Promise<{
    id: string;
    status: string;
    current_period_start: number;
    current_period_end: number;
    cancel_at_period_end: boolean;
    customer: string;
  }> {
    try {
      // Get CSRF token for authenticated request
      const csrfToken = await this.getCSRFToken();

      const response = await this.get(
        `/api/workspaces/${workspaceSlug}/stripe/subscriptions/${subscriptionId}/`,
        {},
        {
          headers: {
            "X-CSRFToken": csrfToken,
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error("Error getting subscription:", error);
      throw error;
    }
  }

  /**
   * Cancel subscription
   */
  async cancelSubscription(
    workspaceSlug: string,
    subscriptionId: string
  ): Promise<{
    id: string;
    status: string;
    cancel_at_period_end: boolean;
  }> {
    try {
      // Get CSRF token for authenticated request
      const csrfToken = await this.getCSRFToken();

      const response = await this.delete(
        `/api/workspaces/${workspaceSlug}/stripe/subscriptions/${subscriptionId}/`,
        {},
        {
          headers: {
            "X-CSRFToken": csrfToken,
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error("Error canceling subscription:", error);
      throw error;
    }
  }

  /**
   * Restart a cancelled subscription
   */
  async restartSubscription(
    workspaceSlug: string,
    subscriptionId: string
  ): Promise<{
    id: string;
    status: string;
    current_period_start: number;
    current_period_end: number;
    cancel_at_period_end: boolean;
    customer: string;
  }> {
    try {
      // Get CSRF token for authenticated request
      const csrfToken = await this.getCSRFToken();

      const response = await this.post(
        `/api/workspaces/${workspaceSlug}/stripe/subscriptions/${subscriptionId}/restart/`,
        {},
        {
          headers: {
            "X-CSRFToken": csrfToken,
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error("Error restarting subscription:", error);
      throw error;
    }
  }

  /**
   * Update subscription to a new price
   */
  async updateSubscription(
    workspaceSlug: string,
    subscriptionId: string,
    newPriceId: string
  ): Promise<{
    id: string;
    status: string;
    current_period_start: number;
    current_period_end: number;
    cancel_at_period_end: boolean;
    customer: string;
  }> {
    try {
      // Get CSRF token for authenticated request
      const csrfToken = await this.getCSRFToken();

      const response = await this.post(
        `/api/workspaces/${workspaceSlug}/stripe/subscriptions/${subscriptionId}/update/`,
        {
          new_price_id: newPriceId,
        },
        {
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/json",
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error("Error updating subscription:", error);
      throw error;
    }
  }

  /**
   * Get customer invoices
   */
  async getInvoices(
    workspaceSlug: string,
    customerId: string,
    limit: number = 10
  ): Promise<{
    invoices: Array<{
      id: string;
      number: string;
      status: string;
      amount_paid: number;
      amount_due: number;
      currency: string;
      created: number;
      due_date: number;
      invoice_pdf?: string;
      hosted_invoice_url?: string;
      description?: string;
    }>;
    has_more: boolean;
  }> {
    try {
      // Get CSRF token for authenticated request
      const csrfToken = await this.getCSRFToken();

      const response = await this.get(
        `/api/workspaces/${workspaceSlug}/stripe/invoices/`,
        {
          customer_id: customerId,
          limit: limit.toString(),
        },
        {
          headers: {
            "X-CSRFToken": csrfToken,
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error("Error getting invoices:", error);
      throw error;
    }
  }

  /**
   * Get current subscription status for workspace
   */
  async getSubscriptionStatus(workspaceSlug: string): Promise<{
    id: string | null;
    status: string;
    current_period_start: number | null;
    current_period_end: number | null;
    cancel_at_period_end: boolean;
    customer: string | null;
    price_id: string | null;
  }> {
    try {
      // Get CSRF token for authenticated request
      const csrfToken = await this.getCSRFToken();

      const response = await this.get(
        `/api/workspaces/${workspaceSlug}/stripe/subscription-status/`,
        {},
        {
          headers: {
            "X-CSRFToken": csrfToken,
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error("Error getting subscription status:", error);
      throw error;
    }
  }

  /**
   * Get Stripe instance
   */
  async getStripe(): Promise<Stripe | null> {
    return this.stripePromise;
  }
}
