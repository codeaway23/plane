import { FC, useState, useEffect } from "react";
import { observer } from "mobx-react";
// plane imports
import { EProductSubscriptionEnum } from "@plane/types";
import { Button, Loader } from "@plane/ui";
import { CreditCard, Settings, Brain, Package } from "lucide-react";
// components
import { SettingsHeading } from "@/components/settings/heading";
import { ComprehensiveOverview } from "./comprehensive-overview";
import { PlanManagement } from "./plan-management";
import { AIUsageManagement } from "./ai-usage-management";
import { AIPackManagement } from "./ai-pack-management";
// services
import { StripeService } from "@/services/stripe.service";
import { AuthService } from "@/services/auth.service";
import { useWorkspace } from "@/hooks/store/use-workspace";
import { useUser } from "@/hooks/store/user";

interface SubscriptionData {
  id: string;
  status: string;
  current_period_start: number;
  current_period_end: number;
  cancel_at_period_end: boolean;
  customer: string;
  price_id?: string;
  product_id?: string;
}

type BillingTab = "overview" | "plans" | "ai-usage" | "ai-packs";

export const BillingDashboard: FC = observer(() => {
  const { currentWorkspace } = useWorkspace();
  const { isAuthenticated } = useUser();
  const [activeTab, setActiveTab] = useState<BillingTab>("overview");
  const [subscriptionData, setSubscriptionData] = useState<SubscriptionData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (currentWorkspace && isAuthenticated) {
      fetchSubscriptionData();
    }
  }, [currentWorkspace, isAuthenticated]);

  // Handle success parameter from Stripe checkout and tab selection
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get("success");
    const sessionId = urlParams.get("session_id");
    const tab = urlParams.get("tab");

    // Set active tab if specified in URL
    if (tab && ["overview", "plans", "ai-usage", "ai-packs"].includes(tab)) {
      setActiveTab(tab as BillingTab);
    }

    if (success === "true" && currentWorkspace && isAuthenticated) {
      // Handle checkout completion if session_id is provided
      if (sessionId) {
        handleCheckoutCompletion(sessionId);
      } else {
        // Fallback: just refresh subscription data
        fetchSubscriptionData();
      }

      // Clean up URL parameters
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }, [currentWorkspace, isAuthenticated]);

  // Handle tab change events from comprehensive overview
  useEffect(() => {
    const handleTabChange = (event: CustomEvent) => {
      const tab = event.detail as BillingTab;
      if (["overview", "plans", "ai-usage", "ai-packs"].includes(tab)) {
        setActiveTab(tab);
      }
    };

    window.addEventListener("billing-tab-change", handleTabChange as EventListener);
    return () => {
      window.removeEventListener("billing-tab-change", handleTabChange as EventListener);
    };
  }, []);

  const handleCheckoutCompletion = async (sessionId: string) => {
    if (!currentWorkspace) return;

    setIsLoading(true);
    setError(null);

    try {
      console.log("Handling checkout completion for session:", sessionId);

      // Get CSRF token
      const authService = new AuthService();
      const csrfData = await authService.requestCSRFToken();

      // Call the checkout completion endpoint
      const response = await fetch("/api/stripe/checkout/complete/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfData.csrf_token,
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      if (!response.ok) {
        throw new Error(`Checkout completion failed: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("Checkout completion result:", result);

      // Refresh subscription data after completion
      await fetchSubscriptionData();
    } catch (error) {
      console.error("Error handling checkout completion:", error);
      setError("Failed to process checkout completion. Please refresh the page.");

      // Fallback: just refresh subscription data
      await fetchSubscriptionData();
    }
  };

  const fetchSubscriptionData = async () => {
    if (!currentWorkspace) return;

    setIsLoading(true);
    setError(null);

    try {
      const stripeService = new StripeService();
      const subscriptionData = await stripeService.getSubscriptionStatus(currentWorkspace.slug);

      console.log("Fetched subscription data:", subscriptionData);

      if (subscriptionData.id && subscriptionData.status === "active") {
        setSubscriptionData({
          id: subscriptionData.id,
          status: subscriptionData.status,
          current_period_start: subscriptionData.current_period_start || 0,
          current_period_end: subscriptionData.current_period_end || 0,
          cancel_at_period_end: subscriptionData.cancel_at_period_end,
          customer: subscriptionData.customer || "",
          price_id: subscriptionData.price_id || undefined,
        });
        console.log("Set active subscription data");
      } else {
        // No active subscription
        setSubscriptionData(null);
        console.log("No active subscription found");
      }
    } catch (err: any) {
      const errorMessage =
        err?.response?.data?.error || err?.message || "Failed to load subscription data. Please try again.";
      setError(errorMessage);
      console.error("Error fetching subscription data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const getCurrentSubscriptionType = (): EProductSubscriptionEnum => {
    if (!subscriptionData?.price_id) return EProductSubscriptionEnum.FREE;

    // Use environment variables for Stripe price IDs
    const STARTER_PRICE_ID = process.env.NEXT_PUBLIC_STRIPE_STARTER_PRICE_ID;
    const PRO_PRICE_ID = process.env.NEXT_PUBLIC_STRIPE_PRO_PRICE_ID;

    const priceIdMap: Record<string, EProductSubscriptionEnum> = {
      [STARTER_PRICE_ID ?? ""]: EProductSubscriptionEnum.STARTER,
      [PRO_PRICE_ID ?? ""]: EProductSubscriptionEnum.PRO,
      // Note: AI Pack subscriptions are handled separately and won't appear in main subscription data
    };
    return priceIdMap[subscriptionData.price_id] || EProductSubscriptionEnum.FREE;
  };

  const handleSubscriptionUpdate = () => {
    // Refresh subscription data when subscription changes
    fetchSubscriptionData();
  };

  const tabs = [
    {
      id: "overview" as BillingTab,
      name: "Overview",
      icon: CreditCard,
      description: "Current subscription and billing status",
    },
    {
      id: "plans" as BillingTab,
      name: "Plans",
      icon: Settings,
      description: "Upgrade or downgrade your plan",
    },
    {
      id: "ai-usage" as BillingTab,
      name: "AI Usage",
      icon: Brain,
      description: "Manage AI usage subscriptions and billing",
    },
    {
      id: "ai-packs" as BillingTab,
      name: "AI Packs",
      icon: Package,
      description: "Subscribe to Core AI Pack or Scale AI Pack",
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader.Item height="3rem" width="3rem" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SettingsHeading title="Billing & Plans" description="Manage your subscription, billing, and plan settings." />

      {error && (
        <div className="p-4 bg-red-100 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Success message for new subscriptions */}
      {new URLSearchParams(window.location.search).get("success") === "true" && (
        <div className="p-4 bg-green-100 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="h-5 w-5 bg-green-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs">✓</span>
            </div>
            <p className="text-sm text-green-800 font-medium">
              Subscription activated successfully! Welcome to your new plan.
            </p>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-custom-border-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  isActive
                    ? "border-custom-primary-200 text-custom-primary-200"
                    : "border-transparent text-custom-text-400 hover:text-custom-text-300 hover:border-custom-border-300"
                }`}
              >
                <Icon className="h-5 w-5" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="py-6">
        {activeTab === "overview" && <ComprehensiveOverview onSubscriptionUpdate={handleSubscriptionUpdate} />}

        {activeTab === "plans" && (
          <PlanManagement
            currentSubscriptionType={getCurrentSubscriptionType()}
            subscriptionData={subscriptionData}
            onPlanChange={fetchSubscriptionData}
          />
        )}

        {activeTab === "ai-usage" && <AIUsageManagement />}

        {activeTab === "ai-packs" && <AIPackManagement onSubscriptionUpdate={handleSubscriptionUpdate} />}
      </div>
    </div>
  );
});
