import { FC, useState } from "react";
import { observer } from "mobx-react";
// plane imports
import { EProductSubscriptionEnum } from "@plane/types";
import { Button, Loader } from "@plane/ui";
import { getSubscriptionName } from "@plane/utils";
import { ArrowUp, ArrowDown, Check, X } from "lucide-react";
// components
import { SettingsHeading } from "@/components/settings/heading";
// services
import { StripeService } from "@/services/stripe.service";
import { useWorkspace } from "@/hooks/store/use-workspace";
import { useUser } from "@/hooks/store/user";

interface PlanManagementProps {
  currentSubscriptionType: EProductSubscriptionEnum;
  subscriptionData?: {
    id: string;
    status: string;
    current_period_start: number;
    current_period_end: number;
    cancel_at_period_end: boolean;
    customer: string;
    price_id?: string;
  } | null;
  onPlanChange?: () => void;
}

interface PlanOption {
  type: EProductSubscriptionEnum;
  name: string;
  price: number;
  priceId: string;
  description: string;
  features: string[];
  isPopular?: boolean;
  isCurrent?: boolean;
}

const PLAN_OPTIONS: PlanOption[] = [
  {
    type: EProductSubscriptionEnum.FREE,
    name: "Free",
    price: 0,
    priceId: "",
    description: "Perfect for getting started",
    features: ["Up to 12 users", "Unlimited projects", "Basic features", "Community support"],
  },
  {
    type: EProductSubscriptionEnum.STARTER,
    name: "Starter",
    price: 8,
    priceId: "price_1S3sXzEPoCJr6b2KycIoGsqy",
    description: "Core PM features with AI assistance",
    features: ["Core PM features", "5 pooled general AI runs", "Unlimited users", "Basic support"],
  },
  {
    type: EProductSubscriptionEnum.PRO,
    name: "Pro",
    price: 14,
    priceId: "price_1S3sgqEPoCJr6b2K97l2hJU7",
    description: "Advanced features with more AI power",
    features: ["All Starter features", "10 pooled general AI runs", "Advanced features", "Priority support"],
    isPopular: true,
  },
  {
    type: EProductSubscriptionEnum.ENTERPRISE,
    name: "Enterprise",
    price: 0,
    priceId: "",
    description: "Custom solutions for large teams",
    features: ["Security & SSO", "SLAs", "Custom AI credits", "Dedicated support"],
  },
];

export const PlanManagement: FC<PlanManagementProps> = observer(
  ({ currentSubscriptionType, subscriptionData, onPlanChange }) => {
    const { currentWorkspace } = useWorkspace();
    const { isAuthenticated } = useUser();
    const [isLoading, setIsLoading] = useState<EProductSubscriptionEnum | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handlePlanChange = async (targetPlan: PlanOption) => {
      if (!currentWorkspace || !isAuthenticated) return;

      // Don't allow changing to the same plan
      if (targetPlan.type === currentSubscriptionType) return;

      // Handle Enterprise plan
      if (targetPlan.type === EProductSubscriptionEnum.ENTERPRISE) {
        // For now, just show a message
        alert("Please contact sales for Enterprise pricing");
        return;
      }

      // Handle downgrade to Free
      if (targetPlan.type === EProductSubscriptionEnum.FREE) {
        // This would typically require canceling the current subscription
        alert("To downgrade to Free, please cancel your current subscription first");
        return;
      }

      setIsLoading(targetPlan.type);
      setError(null);

      try {
        const stripeService = new StripeService();

        // Check if we have an existing active subscription
        if (subscriptionData?.id && subscriptionData?.status === "active") {
          // Use updateSubscription for existing subscriptions (upgrades/downgrades)
          console.log(`Updating existing subscription ${subscriptionData.id} to ${targetPlan.priceId}`);

          const updatedSubscription = await stripeService.updateSubscription(
            currentWorkspace.slug,
            subscriptionData.id,
            targetPlan.priceId
          );

          console.log("Subscription updated successfully:", updatedSubscription);

          // Refresh the subscription data to show the updated plan
          if (onPlanChange) {
            onPlanChange();
          }
        } else {
          // No existing subscription, create new one via checkout
          console.log("No existing subscription, creating new one via checkout");

          const successUrl = `${window.location.origin}/${currentWorkspace.slug}/settings/billing?success=true`;
          const cancelUrl = `${window.location.origin}/${currentWorkspace.slug}/settings/billing?canceled=true`;

          // Redirect to Stripe checkout
          await stripeService.redirectToCheckout(currentWorkspace.slug, targetPlan.priceId, successUrl, cancelUrl);
        }
      } catch (err) {
        setError(`Failed to change plan. Please try again.`);
        console.error("Error changing plan:", err);
      } finally {
        setIsLoading(null);
      }
    };

    const getActionButton = (plan: PlanOption) => {
      const isCurrent = plan.type === currentSubscriptionType;
      const isPlanLoading = isLoading === plan.type;

      if (isCurrent) {
        return (
          <Button variant="outline-primary" size="sm" disabled className="w-full">
            <Check className="h-4 w-4 mr-2" />
            Current Plan
          </Button>
        );
      }

      if (plan.type === EProductSubscriptionEnum.ENTERPRISE) {
        return (
          <Button variant="outline-primary" size="sm" onClick={() => handlePlanChange(plan)} className="w-full">
            Contact Sales
          </Button>
        );
      }

      if (plan.type === EProductSubscriptionEnum.FREE) {
        return (
          <Button
            variant="outline-primary"
            size="sm"
            onClick={() => handlePlanChange(plan)}
            className="w-full"
            disabled
          >
            <X className="h-4 w-4 mr-2" />
            Downgrade
          </Button>
        );
      }

      const isUpgrade =
        plan.type === EProductSubscriptionEnum.PRO && currentSubscriptionType === EProductSubscriptionEnum.STARTER;
      const isDowngrade =
        plan.type === EProductSubscriptionEnum.STARTER && currentSubscriptionType === EProductSubscriptionEnum.PRO;

      return (
        <Button
          variant={isUpgrade ? "primary" : "outline-primary"}
          size="sm"
          onClick={() => handlePlanChange(plan)}
          disabled={isPlanLoading}
          className="w-full"
        >
          {isPlanLoading ? (
            <div className="flex items-center gap-2">
              <Loader.Item height="1rem" width="1rem" />
              Processing...
            </div>
          ) : (
            <div className="flex items-center gap-2">
              {isUpgrade ? <ArrowUp className="h-4 w-4" /> : isDowngrade ? <ArrowDown className="h-4 w-4" /> : null}
              {isUpgrade ? "Upgrade" : isDowngrade ? "Downgrade" : "Change Plan"}
            </div>
          )}
        </Button>
      );
    };

    return (
      <div className="space-y-6">
        <SettingsHeading
          title="Change Plan"
          description="Upgrade or downgrade your subscription to match your needs."
        />

        {error && (
          <div className="p-3 bg-red-100 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {PLAN_OPTIONS.map((plan) => (
            <div
              key={plan.type}
              className={`relative bg-custom-background-100 border rounded-lg p-6 ${
                plan.isCurrent ? "border-custom-primary-200 bg-custom-primary-50/20" : "border-custom-border-200"
              } ${plan.isPopular ? "ring-2 ring-custom-primary-200" : ""}`}
            >
              {plan.isPopular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-custom-primary-200 text-white text-xs font-semibold px-3 py-1 rounded-full">
                    Popular
                  </span>
                </div>
              )}

              <div className="text-center">
                <h3 className="text-lg font-semibold text-custom-text-100 mb-1">{plan.name}</h3>
                <p className="text-sm text-custom-text-300 mb-4">{plan.description}</p>

                <div className="mb-6">
                  {plan.type === EProductSubscriptionEnum.ENTERPRISE ? (
                    <div className="text-2xl font-bold text-custom-text-100">Let's Talk</div>
                  ) : plan.price === 0 ? (
                    <div className="text-2xl font-bold text-custom-text-100">Free</div>
                  ) : (
                    <div>
                      <span className="text-2xl font-bold text-custom-text-100">${plan.price}</span>
                      <span className="text-sm text-custom-text-300">/user/month</span>
                    </div>
                  )}
                </div>

                <ul className="text-left space-y-2 mb-6">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2 text-sm text-custom-text-300">
                      <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>

                {getActionButton(plan)}
              </div>
            </div>
          ))}
        </div>

        <div className="bg-custom-background-100 border border-custom-border-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-custom-text-100 mb-2">Plan Change Information</h4>
          <ul className="text-sm text-custom-text-300 space-y-1">
            <li>• Plan changes go through secure Stripe checkout</li>
            <li>• You'll be charged or credited prorated amounts</li>
            <li>• Previous subscriptions are automatically cancelled</li>
            <li>• Only one active subscription per workspace is allowed</li>
            <li>• Contact support if you need assistance</li>
          </ul>
        </div>
      </div>
    );
  }
);
