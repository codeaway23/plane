import { FC, useState, useEffect } from "react";
import { observer } from "mobx-react";
// plane imports
import { EProductSubscriptionEnum } from "@plane/types";
import { Button, Loader } from "@plane/ui";
import { getSubscriptionName } from "@plane/utils";
import { Calendar, CreditCard, AlertCircle, CheckCircle, XCircle } from "lucide-react";
// components
import { SettingsHeading } from "@/components/settings/heading";
// services
import { StripeService } from "@/services/stripe.service";
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

interface SubscriptionStatusProps {
  subscriptionData?: SubscriptionData | null;
  onSubscriptionUpdate?: () => void;
}

export const SubscriptionStatus: FC<SubscriptionStatusProps> = observer(
  ({ subscriptionData, onSubscriptionUpdate }) => {
    const { currentWorkspace } = useWorkspace();
    const { isAuthenticated } = useUser();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Determine subscription type from price_id
    const getSubscriptionType = (priceId?: string): EProductSubscriptionEnum => {
      if (!priceId) return EProductSubscriptionEnum.FREE;

      // Map price IDs to subscription types
      const priceIdMap: Record<string, EProductSubscriptionEnum> = {
        price_1S3sXzEPoCJr6b2KycIoGsqy: EProductSubscriptionEnum.STARTER,
        price_1S3sgqEPoCJr6b2K97l2hJU7: EProductSubscriptionEnum.PRO,
      };

      return priceIdMap[priceId] || EProductSubscriptionEnum.FREE;
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

    const handleCancelSubscription = async () => {
      if (!currentWorkspace || !subscriptionData) return;

      setIsLoading(true);
      setError(null);

      try {
        const stripeService = new StripeService();
        await stripeService.cancelSubscription(currentWorkspace.slug, subscriptionData.id);

        // Refresh subscription data
        if (onSubscriptionUpdate) {
          onSubscriptionUpdate();
        }
      } catch (err) {
        setError("Failed to cancel subscription. Please try again.");
        console.error("Error canceling subscription:", err);
      } finally {
        setIsLoading(false);
      }
    };

    const handleRestartSubscription = async () => {
      if (!currentWorkspace || !subscriptionData) return;

      setIsLoading(true);
      setError(null);

      try {
        const stripeService = new StripeService();
        await stripeService.restartSubscription(currentWorkspace.slug, subscriptionData.id);

        // Refresh subscription data
        if (onSubscriptionUpdate) {
          onSubscriptionUpdate();
        }
      } catch (err) {
        setError("Failed to restart subscription. Please try again.");
        console.error("Error restarting subscription:", err);
      } finally {
        setIsLoading(false);
      }
    };

    if (!subscriptionData) {
      return (
        <div className="space-y-6">
          <SettingsHeading
            title="Current Plan"
            description="You're currently on the free plan. Upgrade to unlock more features."
          />
          <div className="bg-custom-background-100 border border-custom-border-200 rounded-lg p-6">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 bg-custom-primary-100/20 rounded-lg flex items-center justify-center">
                <CreditCard className="h-6 w-6 text-custom-primary-200" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-custom-text-100">Free Plan</h3>
                <p className="text-sm text-custom-text-300">No active subscription</p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    const subscriptionType = getSubscriptionType(subscriptionData.price_id);
    const subscriptionName = getSubscriptionName(subscriptionType);

    return (
      <div className="space-y-6">
        <SettingsHeading title="Current Plan" description="Manage your subscription and billing information." />

        <div className="bg-custom-background-100 border border-custom-border-200 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 bg-custom-primary-100/20 rounded-lg flex items-center justify-center">
                <CreditCard className="h-6 w-6 text-custom-primary-200" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-custom-text-100">{subscriptionName}</h3>
                  {getStatusIcon(subscriptionData.status)}
                </div>
                <p className="text-sm text-custom-text-300">
                  Status: <span className="font-medium">{getStatusText(subscriptionData.status)}</span>
                </p>
                {subscriptionData.cancel_at_period_end && (
                  <p className="text-sm text-yellow-600 font-medium">
                    Subscription will cancel at the end of the current period
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-custom-text-400" />
              <div>
                <p className="text-sm text-custom-text-400">Current Period</p>
                <p className="text-sm font-medium text-custom-text-100">
                  {formatDate(subscriptionData.current_period_start)} -{" "}
                  {formatDate(subscriptionData.current_period_end)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <CreditCard className="h-5 w-5 text-custom-text-400" />
              <div>
                <p className="text-sm text-custom-text-400">Next Billing Date</p>
                <p className="text-sm font-medium text-custom-text-100">
                  {formatDate(subscriptionData.current_period_end)}
                </p>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-100 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="mt-6 flex gap-3">
            {subscriptionData.status === "active" && !subscriptionData.cancel_at_period_end && (
              <Button variant="outline-danger" size="sm" onClick={handleCancelSubscription} disabled={isLoading}>
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <Loader.Item height="1rem" width="1rem" />
                    Canceling...
                  </div>
                ) : (
                  "Cancel Subscription"
                )}
              </Button>
            )}

            {subscriptionData.status === "active" && subscriptionData.cancel_at_period_end && (
              <Button variant="primary" size="sm" onClick={handleRestartSubscription} disabled={isLoading}>
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <Loader.Item height="1rem" width="1rem" />
                    Restarting...
                  </div>
                ) : (
                  "Restart Subscription"
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }
);
