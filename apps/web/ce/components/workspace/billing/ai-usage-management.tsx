import { FC, useState, useEffect } from "react";
import { observer } from "mobx-react";
// plane imports
import { Button, Loader } from "@plane/ui";
import { Brain, Zap, Code, CheckCircle, XCircle, AlertCircle, AlertTriangle } from "lucide-react";
// hooks
import { useWorkspace } from "@/hooks/store/use-workspace";
// services
import { AIUsageService } from "@/services/ai-usage.service";

interface AIPlan {
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

interface AISubscription {
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

interface AIUsageData {
  general_run: AISubscription;
  code_run: AISubscription;
}

export const AIUsageManagement: FC = observer(() => {
  const { currentWorkspace } = useWorkspace();
  const [plans, setPlans] = useState<Record<string, AIPlan>>({});
  const [subscriptions, setSubscriptions] = useState<AIUsageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [showCancelDialog, setShowCancelDialog] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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
      const [plansData, subscriptionsData] = await Promise.all([
        AIUsageService.getPlans(currentWorkspace.slug),
        AIUsageService.getSubscriptions(currentWorkspace.slug),
      ]);

      console.log("plansData", plansData);
      setPlans(plansData);
      console.log("subscriptionsData", subscriptionsData);
      setSubscriptions(subscriptionsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load AI usage data");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubscribe = async (planType: string) => {
    if (!currentWorkspace) return;

    setActionLoading((prev) => ({ ...prev, [`subscribe_${planType}`]: true }));

    try {
      const checkoutData = await AIUsageService.createCheckoutSession(currentWorkspace.slug, planType);

      // Redirect to Stripe checkout
      window.location.href = checkoutData.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create checkout session");
    } finally {
      setActionLoading((prev) => ({ ...prev, [`subscribe_${planType}`]: false }));
    }
  };

  const handleCancel = (planType: string) => {
    setShowCancelDialog(planType);
  };

  const confirmCancel = async (planType: string) => {
    if (!currentWorkspace) return;

    setActionLoading((prev) => ({ ...prev, [`cancel_${planType}`]: true }));

    try {
      await AIUsageService.cancelSubscription(currentWorkspace.slug, planType);
      await fetchData(); // Refresh data

      setSuccess(`${plans[planType]?.name || planType} subscription cancelled immediately. You can restart anytime.`);
      setTimeout(() => setSuccess(null), 5000);
      setShowCancelDialog(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel subscription");
    } finally {
      setActionLoading((prev) => ({ ...prev, [`cancel_${planType}`]: false }));
    }
  };

  const handleRestart = async (planType: string) => {
    if (!currentWorkspace) return;

    setActionLoading((prev) => ({ ...prev, [`restart_${planType}`]: true }));

    try {
      await AIUsageService.restartSubscription(currentWorkspace.slug, planType);
      await fetchData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to restart subscription");
    } finally {
      setActionLoading((prev) => ({ ...prev, [`restart_${planType}`]: false }));
    }
  };

  const getStatusIcon = (subscription: AISubscription) => {
    if (!subscription.active) {
      return <XCircle className="h-5 w-5 text-red-500" />;
    }

    if (subscription.subscription?.cancel_at_period_end) {
      return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }

    return <CheckCircle className="h-5 w-5 text-green-500" />;
  };

  const getStatusText = (subscription: AISubscription) => {
    if (!subscription.active) {
      return "Inactive";
    }

    if (subscription.subscription?.cancel_at_period_end) {
      return "Cancelling at period end";
    }

    return "Active";
  };

  const getStatusColor = (subscription: AISubscription) => {
    if (!subscription.active) {
      return "text-red-600";
    }

    if (subscription.subscription?.cancel_at_period_end) {
      return "text-yellow-600";
    }

    return "text-green-600";
  };

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

      {success && (
        <div className="p-4 bg-green-100 border border-green-200 rounded-lg">
          <p className="text-sm text-green-600">{success}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(plans).map(([planType, plan]) => {
          const subscription = subscriptions?.[planType as keyof AIUsageData];
          const isActive = subscription?.active || false;
          const isCancelling = subscription?.subscription?.cancel_at_period_end || false;

          return (
            <div key={planType} className="border border-custom-border-200 rounded-lg p-6 space-y-4">
              {/* Plan Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {planType === "general_run" ? (
                    <Zap className="h-6 w-6 text-blue-500" />
                  ) : (
                    <Code className="h-6 w-6 text-purple-500" />
                  )}
                  <div>
                    <h3 className="text-lg font-semibold text-custom-text-100">{plan.name}</h3>
                    <p className="text-sm text-custom-text-400">{plan.description}</p>
                  </div>
                </div>
                {getStatusIcon(subscription || { active: false })}
              </div>

              {/* Pricing */}
              <div className="space-y-2">
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-custom-text-100">${plan.cost_per_unit}</span>
                  <span className="text-sm text-custom-text-400">per {plan.unit_name}</span>
                </div>
                {plan.stripe_price && (
                  <p className="text-xs text-custom-text-400">Metered billing • Pay only for what you use</p>
                )}
              </div>

              {/* Status */}
              <div className="flex items-center gap-2">
                <span className={`text-sm font-medium ${getStatusColor(subscription || { active: false })}`}>
                  {getStatusText(subscription || { active: false })}
                </span>
                {subscription?.subscription?.current_period_end && (
                  <span className="text-xs text-custom-text-400">
                    • Renews {new Date(subscription.subscription.current_period_end * 1000).toLocaleDateString()}
                  </span>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                {!isActive ? (
                  <Button
                    onClick={() => handleSubscribe(planType)}
                    loading={actionLoading[`subscribe_${planType}`]}
                    className="flex-1"
                  >
                    Subscribe
                  </Button>
                ) : (
                  <>
                    {isCancelling ? (
                      <Button
                        onClick={() => handleRestart(planType)}
                        loading={actionLoading[`restart_${planType}`]}
                        variant="neutral-primary"
                        className="flex-1"
                      >
                        Restart Subscription
                      </Button>
                    ) : (
                      <Button
                        onClick={() => handleCancel(planType)}
                        loading={actionLoading[`cancel_${planType}`]}
                        variant="neutral-primary"
                        className="flex-1"
                      >
                        Cancel Subscription
                      </Button>
                    )}
                  </>
                )}
              </div>

              {/* Error Message */}
              {plan.error && (
                <div className="p-3 bg-yellow-100 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">{plan.error}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Usage Information */}
      <div className="bg-custom-background-80 border border-custom-border-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <Brain className="h-5 w-5 text-custom-text-400 mt-0.5" />
          <div className="space-y-2">
            <h4 className="font-medium text-custom-text-100">How AI Usage Billing Works</h4>
            <div className="text-sm text-custom-text-400 space-y-1">
              <p>
                • <strong>Metered Billing:</strong> You only pay for the AI runs you actually use
              </p>
              <p>
                • <strong>Multiple Plans:</strong> You can subscribe to both General Run and Code Run plans
                simultaneously
              </p>
              <p>
                • <strong>Usage Tracking:</strong> Each AI interaction is automatically tracked and billed
              </p>
              <p>
                • <strong>Flexible Management:</strong> Cancel or restart subscriptions at any time
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Cancel Subscription Confirmation Dialog */}
      {showCancelDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-custom-background-100 border border-custom-border-200 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-6 w-6 text-orange-500" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-custom-text-100">
                  Cancel {plans[showCancelDialog]?.name || showCancelDialog} Subscription
                </h3>
                <p className="text-sm text-custom-text-300">
                  Are you sure you want to cancel your {plans[showCancelDialog]?.name || showCancelDialog} subscription?
                </p>
              </div>
            </div>

            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-orange-800">
                <strong>Important:</strong> Your {plans[showCancelDialog]?.name || showCancelDialog} subscription will
                be cancelled immediately. You'll lose access to this AI feature right away, but you can restart your
                subscription anytime.
              </p>
            </div>

            <div className="flex gap-3 justify-end">
              <Button
                variant="outline-primary"
                size="sm"
                onClick={() => setShowCancelDialog(null)}
                disabled={actionLoading[`cancel_${showCancelDialog}`]}
              >
                Keep Subscription
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => confirmCancel(showCancelDialog)}
                disabled={actionLoading[`cancel_${showCancelDialog}`]}
                loading={actionLoading[`cancel_${showCancelDialog}`]}
              >
                Yes, Cancel Subscription
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});
