import { FC, useState, useEffect } from "react";
import { observer } from "mobx-react";
// plane imports
import { Button, Loader } from "@plane/ui";
import { Brain, Zap, Code, CheckCircle, XCircle, AlertCircle, ArrowUpRight } from "lucide-react";
// hooks
import { useWorkspace } from "@/hooks/store/use-workspace";
// services
import { AIPackService, AIPackPlan, AIPackSubscription } from "@/services/ai-pack.service";

interface AIPackManagementProps {
  onSubscriptionUpdate?: () => void;
}

export const AIPackManagement: FC<AIPackManagementProps> = observer(({ onSubscriptionUpdate }) => {
  const { currentWorkspace } = useWorkspace();
  const [plans, setPlans] = useState<Record<string, AIPackPlan>>({});
  const [subscription, setSubscription] = useState<AIPackSubscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (currentWorkspace) {
      fetchData();
    }
  }, [currentWorkspace]);

  const fetchData = async () => {
    if (!currentWorkspace) return;

    setIsLoading(true);
    setError(null);

    try {
      const [plansData, subscriptionData] = await Promise.all([
        AIPackService.getPlans(currentWorkspace.slug),
        AIPackService.getSubscription(currentWorkspace.slug),
      ]);

      console.log("AI Pack plans data:", plansData);
      setPlans(plansData);
      console.log("AI Pack subscription data:", subscriptionData);
      setSubscription(subscriptionData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load AI Pack data");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubscribe = async (packType: string) => {
    if (!currentWorkspace) return;

    setActionLoading((prev) => ({ ...prev, [`subscribe_${packType}`]: true }));

    try {
      const checkoutData = await AIPackService.createCheckoutSession(currentWorkspace.slug, packType);

      // Redirect to Stripe checkout
      window.location.href = checkoutData.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create checkout session");
    } finally {
      setActionLoading((prev) => ({ ...prev, [`subscribe_${packType}`]: false }));
    }
  };

  const handleCancel = async () => {
    if (!currentWorkspace) return;

    setActionLoading((prev) => ({ ...prev, cancel: true }));

    try {
      await AIPackService.cancelSubscription(currentWorkspace.slug);
      await fetchData();
      onSubscriptionUpdate?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel subscription");
    } finally {
      setActionLoading((prev) => ({ ...prev, cancel: false }));
    }
  };

  const handleRestart = async () => {
    if (!currentWorkspace) return;

    setActionLoading((prev) => ({ ...prev, restart: true }));

    try {
      await AIPackService.restartSubscription(currentWorkspace.slug);
      await fetchData();
      onSubscriptionUpdate?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to restart subscription");
    } finally {
      setActionLoading((prev) => ({ ...prev, restart: false }));
    }
  };

  const handleUpgrade = async (packType: string) => {
    if (!currentWorkspace) return;

    setActionLoading((prev) => ({ ...prev, [`upgrade_${packType}`]: true }));

    try {
      const checkoutData = await AIPackService.upgradeSubscription(currentWorkspace.slug, packType);

      // Redirect to Stripe checkout
      window.location.href = checkoutData.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create upgrade session");
    } finally {
      setActionLoading((prev) => ({ ...prev, [`upgrade_${packType}`]: false }));
    }
  };

  const getStatusIcon = (subscription: AIPackSubscription) => {
    if (!subscription.active) {
      return <XCircle className="h-6 w-6 text-red-500" />;
    }

    if (subscription.subscription?.cancel_at_period_end) {
      return <AlertCircle className="h-6 w-6 text-yellow-500" />;
    }

    return <CheckCircle className="h-6 w-6 text-green-500" />;
  };

  const getStatusText = (subscription: AIPackSubscription) => {
    if (!subscription.active) {
      return "No active subscription";
    }

    if (subscription.subscription?.cancel_at_period_end) {
      return "Cancelling at period end";
    }

    return "Active";
  };

  const getStatusColor = (subscription: AIPackSubscription) => {
    if (!subscription.active) {
      return "text-red-600";
    }

    if (subscription.subscription?.cancel_at_period_end) {
      return "text-yellow-600";
    }

    return "text-green-600";
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(price);
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  // Helper: is the current plan the scale pack?
  const isScaleActive = subscription?.active && subscription?.pack_type === "scale_ai_pack";

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader.Item height="3rem" width="3rem" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-4 bg-red-100 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Available Plans */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(plans).map(([packType, plan]) => {
          const isCurrentPlan = subscription?.pack_type === packType;
          const isUpgrade = subscription?.active && !isCurrentPlan;
          const canSubscribe = !subscription?.active;

          // Determine if this is a downgrade (from scale to core)
          const isDowngrade = isScaleActive && packType === "core_ai_pack" && !isCurrentPlan;

          // Button label logic
          let actionButton = null;
          if (isCurrentPlan) {
            actionButton = (
              <div className="space-y-3">
                {subscription?.subscription?.cancel_at_period_end ? (
                  <Button
                    variant="outline-primary"
                    className="w-full"
                    onClick={handleRestart}
                    loading={actionLoading.restart}
                  >
                    Restart Subscription
                  </Button>
                ) : (
                  <Button
                    variant="outline-danger"
                    className="w-full"
                    onClick={handleCancel}
                    loading={actionLoading.cancel}
                  >
                    Cancel Subscription
                  </Button>
                )}
              </div>
            );
          } else if (isDowngrade) {
            actionButton = (
              <Button
                variant="primary"
                className="w-full"
                onClick={() => handleUpgrade(packType)}
                loading={actionLoading[`upgrade_${packType}`]}
              >
                <ArrowUpRight className="h-4 w-4 mr-2" />
                Downgrade to {plan.name}
              </Button>
            );
          } else if (isUpgrade) {
            actionButton = (
              <Button
                variant="primary"
                className="w-full"
                onClick={() => handleUpgrade(packType)}
                loading={actionLoading[`upgrade_${packType}`]}
              >
                <ArrowUpRight className="h-4 w-4 mr-2" />
                Upgrade to {plan.name}
              </Button>
            );
          } else if (canSubscribe) {
            actionButton = (
              <Button
                variant="primary"
                className="w-full"
                onClick={() => handleSubscribe(packType)}
                loading={actionLoading[`subscribe_${packType}`]}
              >
                Subscribe to {plan.name}
              </Button>
            );
          } else {
            actionButton = (
              <div className="text-center py-2">
                <span className="text-sm text-custom-text-400">
                  {subscription?.pack_config?.name} subscription active
                </span>
              </div>
            );
          }

          return (
            <div key={packType} className="border border-custom-border-200 rounded-lg p-6 space-y-4">
              {/* Plan Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {packType === "core_ai_pack" ? (
                    <Zap className="h-6 w-6 text-blue-500" />
                  ) : (
                    <Code className="h-6 w-6 text-purple-500" />
                  )}
                  <div>
                    <h3 className="text-lg font-semibold text-custom-text-100">{plan.name}</h3>
                    <p className="text-sm text-custom-text-400">{plan.description}</p>
                  </div>
                </div>
                {isCurrentPlan && getStatusIcon(subscription!)}
              </div>

              {/* Pricing */}
              <div className="space-y-2">
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-custom-text-100">{formatPrice(plan.monthly_price)}</span>
                  <span className="text-sm text-custom-text-400">/month</span>
                </div>
                <p className="text-sm text-custom-text-400">
                  Includes {plan.general_runs} general runs or {plan.code_runs} code runs
                </p>
              </div>

              {/* Features */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-custom-text-300">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>{plan.general_runs} General AI Runs</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-custom-text-300">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>{plan.code_runs} Code AI Runs</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-custom-text-300">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Monthly billing cycle</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-custom-text-300">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Cancel anytime</span>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-4">{actionButton}</div>
            </div>
          );
        })}
      </div>

      {/* Enterprise Volume Option */}
      <div className="border border-custom-border-200 rounded-lg p-6 bg-gradient-to-r from-purple-50 to-blue-50">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Brain className="h-6 w-6 text-purple-500" />
            <div>
              <h3 className="text-lg font-semibold text-custom-text-100">Enterprise Volume</h3>
              <p className="text-sm text-custom-text-400">
                Custom pricing for high-volume usage. Flexible bundles, discounted rates at very high usage, unlimited
                options at $500k+ ACV.
              </p>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <Button
            variant="outline-primary"
            className="w-full"
            onClick={() => {
              alert("Please contact sales for Enterprise pricing");
            }}
          >
            <ArrowUpRight className="h-4 w-4 mr-2" />
            Contact Sales
          </Button>
        </div>
      </div>
    </div>
  );
});
