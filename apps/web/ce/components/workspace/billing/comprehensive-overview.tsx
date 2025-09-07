import { FC, useState, useEffect } from "react";
import { observer } from "mobx-react";
// plane imports
import { EProductSubscriptionEnum } from "@plane/types";
import { Button, Loader } from "@plane/ui";
import { getSubscriptionName } from "@plane/utils";
import {
  Calendar,
  CreditCard,
  AlertCircle,
  CheckCircle,
  XCircle,
  Brain,
  Zap,
  Code,
  Package,
  Settings,
} from "lucide-react";
// components
import { SettingsHeading } from "@/components/settings/heading";
// services
import { StripeService } from "@/services/stripe.service";
import { AIUsageService, AIUsageData } from "@/services/ai-usage.service";
import { AIPackService, AIPackSubscription } from "@/services/ai-pack.service";
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

interface ComprehensiveOverviewProps {
  onSubscriptionUpdate?: () => void;
}

export const ComprehensiveOverview: FC<ComprehensiveOverviewProps> = observer(({ onSubscriptionUpdate }) => {
  const { currentWorkspace } = useWorkspace();
  const { isAuthenticated } = useUser();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Main subscription data
  const [subscriptionData, setSubscriptionData] = useState<SubscriptionData | null>(null);

  // AI Usage data
  const [aiUsageData, setAiUsageData] = useState<AIUsageData | null>(null);

  // AI Pack data
  const [aiPackData, setAiPackData] = useState<AIPackSubscription | null>(null);

  useEffect(() => {
    if (currentWorkspace && isAuthenticated) {
      fetchAllData();
    }
  }, [currentWorkspace, isAuthenticated]);

  const fetchAllData = async () => {
    if (!currentWorkspace) return;

    setIsLoading(true);
    setError(null);

    try {
      // Fetch all subscription data in parallel
      const [mainSubscription, aiUsage, aiPack] = await Promise.allSettled([
        fetchMainSubscription(),
        fetchAIUsageData(),
        fetchAIPackData(),
      ]);

      // Handle main subscription
      if (mainSubscription.status === "fulfilled") {
        setSubscriptionData(mainSubscription.value);
      }

      // Handle AI usage data
      if (aiUsage.status === "fulfilled") {
        setAiUsageData(aiUsage.value);
      }

      // Handle AI pack data
      if (aiPack.status === "fulfilled") {
        setAiPackData(aiPack.value);
      }

      // Log any errors but don't fail the entire operation
      if (mainSubscription.status === "rejected") {
        console.error("Failed to fetch main subscription:", mainSubscription.reason);
      }
      if (aiUsage.status === "rejected") {
        console.error("Failed to fetch AI usage data:", aiUsage.reason);
      }
      if (aiPack.status === "rejected") {
        console.error("Failed to fetch AI pack data:", aiPack.reason);
      }
    } catch (err) {
      setError("Failed to load subscription data. Please try again.");
      console.error("Error fetching subscription data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMainSubscription = async (): Promise<SubscriptionData | null> => {
    const stripeService = new StripeService();
    const data = await stripeService.getSubscriptionStatus(currentWorkspace!.slug);

    if (data.id && data.status === "active") {
      return {
        id: data.id,
        status: data.status,
        current_period_start: data.current_period_start || 0,
        current_period_end: data.current_period_end || 0,
        cancel_at_period_end: data.cancel_at_period_end,
        customer: data.customer || "",
        price_id: data.price_id || undefined,
      };
    }
    return null;
  };

  const fetchAIUsageData = async (): Promise<AIUsageData | null> => {
    return await AIUsageService.getSubscriptions(currentWorkspace!.slug);
  };

  const fetchAIPackData = async (): Promise<AIPackSubscription | null> => {
    return await AIPackService.getSubscription(currentWorkspace!.slug);
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "canceled":
        return <XCircle className="h-5 w-5 text-red-500" />;
      case "past_due":
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "active":
        return "Active";
      case "canceled":
        return "Canceled";
      case "past_due":
        return "Past Due";
      case "incomplete":
        return "Incomplete";
      case "incomplete_expired":
        return "Expired";
      case "trialing":
        return "Trial";
      case "unpaid":
        return "Unpaid";
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const getAIUsageStatusIcon = (subscription: any) => {
    if (!subscription?.active) {
      return <XCircle className="h-4 w-4 text-red-500" />;
    }
    if (subscription?.subscription?.cancel_at_period_end) {
      return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
    return <CheckCircle className="h-4 w-4 text-green-500" />;
  };

  const getAIUsageStatusText = (subscription: any) => {
    if (!subscription?.active) {
      return "Inactive";
    }
    if (subscription?.subscription?.cancel_at_period_end) {
      return "Cancelling";
    }
    return "Active";
  };

  const getAIPackStatusIcon = (subscription: AIPackSubscription) => {
    if (!subscription?.active) {
      return <XCircle className="h-4 w-4 text-red-500" />;
    }
    if (subscription?.subscription?.cancel_at_period_end) {
      return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
    return <CheckCircle className="h-4 w-4 text-green-500" />;
  };

  const getAIPackStatusText = (subscription: AIPackSubscription) => {
    if (!subscription?.active) {
      return "No active subscription";
    }
    if (subscription?.subscription?.cancel_at_period_end) {
      return "Cancelling at period end";
    }
    return "Active";
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader.Item height="3rem" width="3rem" />
      </div>
    );
  }

  const subscriptionType = getCurrentSubscriptionType();
  const subscriptionName = getSubscriptionName(subscriptionType);

  return (
    <div className="space-y-6">
      <SettingsHeading
        title="Subscription Overview"
        description="Complete overview of all your active subscriptions and plans."
      />

      {error && (
        <div className="p-4 bg-red-100 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Main Subscription Plan */}
      <div className="bg-custom-background-100 border border-custom-border-200 rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 bg-custom-primary-100/20 rounded-lg flex items-center justify-center">
              <Settings className="h-6 w-6 text-custom-primary-200" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-custom-text-100">{subscriptionName}</h3>
                {subscriptionData && getStatusIcon(subscriptionData.status)}
              </div>
              <p className="text-sm text-custom-text-300">
                Main Plan • {subscriptionData ? getStatusText(subscriptionData.status) : "Free Plan"}
              </p>
              {subscriptionData?.cancel_at_period_end && (
                <p className="text-sm text-yellow-600 font-medium">
                  Subscription will cancel at the end of the current period
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* AI Pack Subscription */}
      {aiPackData?.active && (
        <div className="bg-custom-background-100 border border-custom-border-200 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 bg-custom-primary-100/20 rounded-lg flex items-center justify-center">
                <Package className="h-6 w-6 text-custom-primary-200" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-custom-text-100">
                    {aiPackData.pack_config?.name || "AI Pack Subscription"}
                  </h3>
                  {getAIPackStatusIcon(aiPackData)}
                </div>
                <p className="text-sm text-custom-text-300">AI Pack • {getAIPackStatusText(aiPackData)}</p>
                {aiPackData.subscription?.cancel_at_period_end && (
                  <p className="text-sm text-yellow-600 font-medium">
                    Subscription will cancel at the end of the current period
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Usage Subscriptions */}
      {aiUsageData && (aiUsageData.general_run?.active || aiUsageData.code_run?.active) && (
        <div className="space-y-4">
          {/* General Run Subscription */}
          {aiUsageData.general_run?.active && (
            <div className="bg-custom-background-100 border border-custom-border-200 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 bg-custom-primary-100/20 rounded-lg flex items-center justify-center">
                    <Zap className="h-6 w-6 text-custom-primary-200" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold text-custom-text-100">General AI Runs</h3>
                      {getAIUsageStatusIcon(aiUsageData.general_run)}
                    </div>
                    <p className="text-sm text-custom-text-300">
                      AI Usage • {getAIUsageStatusText(aiUsageData.general_run)}
                    </p>
                    {aiUsageData.general_run.subscription?.cancel_at_period_end && (
                      <p className="text-sm text-yellow-600 font-medium">
                        Subscription will cancel at the end of the current period
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Code Run Subscription */}
          {aiUsageData.code_run?.active && (
            <div className="bg-custom-background-100 border border-custom-border-200 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 bg-custom-primary-100/20 rounded-lg flex items-center justify-center">
                    <Code className="h-6 w-6 text-custom-primary-200" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold text-custom-text-100">Code AI Runs</h3>
                      {getAIUsageStatusIcon(aiUsageData.code_run)}
                    </div>
                    <p className="text-sm text-custom-text-300">
                      AI Usage • {getAIUsageStatusText(aiUsageData.code_run)}
                    </p>
                    {aiUsageData.code_run.subscription?.cancel_at_period_end && (
                      <p className="text-sm text-yellow-600 font-medium">
                        Subscription will cancel at the end of the current period
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* No Active Subscriptions Message */}
      {!subscriptionData &&
        !aiPackData?.active &&
        !aiUsageData?.general_run?.active &&
        !aiUsageData?.code_run?.active && (
          <div className="bg-custom-background-100 border border-custom-border-200 rounded-lg p-6">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 bg-custom-primary-100/20 rounded-lg flex items-center justify-center">
                <CreditCard className="h-6 w-6 text-custom-primary-200" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-custom-text-100">Free Plan</h3>
                <p className="text-sm text-custom-text-300">
                  No active subscriptions. Explore our plans to unlock more features.
                </p>
              </div>
            </div>
          </div>
        )}
    </div>
  );
});
