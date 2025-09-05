import { FC, useState } from "react";
import { observer } from "mobx-react";
// plane imports
import {
  SUBSCRIPTION_WITH_BILLING_FREQUENCY,
  WORKSPACE_SETTINGS_TRACKER_ELEMENTS,
  WORKSPACE_SETTINGS_TRACKER_EVENTS,
} from "@plane/constants";
import { useTranslation } from "@plane/i18n";
import { EProductSubscriptionEnum, TBillingFrequency } from "@plane/types";
import { getButtonStyling, getUpgradeButtonStyle, Loader } from "@plane/ui";
import { cn, getSubscriptionName } from "@plane/utils";
// components
import { DiscountInfo } from "@/components/license/modal/card/discount-info";
import { TPlanDetail } from "@/constants/plans";
// local imports
import { captureSuccess } from "@/helpers/event-tracker.helper";
import { PlanFrequencyToggle } from "./frequency-toggle";
import { StripeService } from "@/services/stripe.service";
import { useWorkspace } from "@/hooks/store/use-workspace";
import { useUser } from "@/hooks/store/user";

type TPlanDetailProps = {
  subscriptionType: EProductSubscriptionEnum;
  planDetail: TPlanDetail;
  billingFrequency: TBillingFrequency | undefined;
  setBillingFrequency: (frequency: TBillingFrequency) => void;
};

const COMMON_BUTTON_STYLE =
  "relative inline-flex items-center justify-center w-full px-4 py-1.5 text-xs font-medium rounded-lg focus:outline-none transition-all duration-300 animate-slide-up";

export const PlanDetail: FC<TPlanDetailProps> = observer((props) => {
  const { subscriptionType, planDetail, billingFrequency, setBillingFrequency } = props;
  // plane hooks
  const { t } = useTranslation();
  const { currentWorkspace } = useWorkspace();
  const { isAuthenticated } = useUser();
  // state
  const [isLoading, setIsLoading] = useState(false);
  // services
  const stripeService = new StripeService();

  // subscription details
  const subscriptionName = getSubscriptionName(subscriptionType);
  const isSubscriptionActive = planDetail.isActive;
  // pricing details
  const displayPrice = planDetail.monthlyPrice;
  const pricingDescription = isSubscriptionActive ? "per user per month" : "Quote on request";
  const pricingSecondaryDescription = planDetail.monthlyPriceSecondaryDescription;
  // helper styles
  const upgradeButtonStyle = getUpgradeButtonStyle(subscriptionType, isLoading) ?? getButtonStyling("primary", "lg");

  const handleStripeCheckout = async () => {
    if (!currentWorkspace || !isSubscriptionActive) return;

    // Handle Enterprise plan - do nothing for now
    if (subscriptionType === EProductSubscriptionEnum.ENTERPRISE) {
      console.log("Enterprise plan selected - no action taken");
      return;
    }

    // Check if user is authenticated
    if (!isAuthenticated) {
      console.error("User must be authenticated to create checkout session");
      // Redirect to login page
      window.location.href = "/";
      return;
    }

    setIsLoading(true);

    try {
      // Get the price ID based on subscription type
      const priceId = getPriceId(subscriptionType);

      if (!priceId) {
        throw new Error("Price ID not found for this plan");
      }

      // Create success and cancel URLs
      const successUrl = `${window.location.origin}/${currentWorkspace.slug}/settings/billing?success=true`;
      const cancelUrl = `${window.location.origin}/${currentWorkspace.slug}/settings/billing?canceled=true`;

      // Track the event
      captureSuccess({
        eventName: WORKSPACE_SETTINGS_TRACKER_EVENTS.upgrade_plan_redirected,
        payload: {
          subscriptionType,
        },
      });

      // Redirect to Stripe checkout
      await stripeService.redirectToCheckout(currentWorkspace.slug, priceId, successUrl, cancelUrl);
    } catch (error) {
      console.error("Error creating checkout session:", error);
      // You might want to show a toast notification here
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to get price ID based on subscription type
  const getPriceId = (subscriptionType: EProductSubscriptionEnum): string | null => {
    // Updated with actual Stripe price IDs from your dashboard
    const priceMap: Record<string, string> = {
      [EProductSubscriptionEnum.STARTER]: "price_1S3sXzEPoCJr6b2KycIoGsqy", // $8.00 USD Per month (Starter plan)
      [EProductSubscriptionEnum.PRO]: "price_1S3sgqEPoCJr6b2K97l2hJU7", // $14.00 USD Per month (Pro plan)
    };

    return priceMap[subscriptionType] || null;
  };

  return (
    <div className="flex flex-col justify-between col-span-1 p-3 space-y-0.5">
      {/* Plan name and pricing section */}
      <div className="flex flex-col items-start">
        <div className="flex w-full gap-2 items-center text-xl font-medium">
          <span className="transition-all duration-300">{subscriptionName}</span>
          {subscriptionType === EProductSubscriptionEnum.PRO && (
            <span className="px-2 rounded text-custom-primary-200 bg-custom-primary-100/20 text-xs">Popular</span>
          )}
        </div>
        <div className="flex gap-x-2 items-start text-custom-text-300 pb-1 transition-all duration-300 animate-slide-up">
          {isSubscriptionActive && displayPrice !== undefined && (
            <div className="flex items-center gap-1 text-2xl text-custom-text-100 font-semibold transition-all duration-300">
              <DiscountInfo
                currency="$"
                frequency="month"
                price={displayPrice}
                subscriptionType={subscriptionType}
                className="mr-1.5"
              />
            </div>
          )}
          <div className="pt-1">
            {pricingDescription && <div className="transition-all duration-300">{pricingDescription}</div>}
            {pricingSecondaryDescription && (
              <div className="text-xs text-custom-text-400 transition-all duration-300">
                {pricingSecondaryDescription}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Billing frequency toggle - removed for monthly-only pricing */}

      {/* Subscription button */}
      <div className={cn("flex flex-col gap-1 py-3 items-start transition-all duration-300")}>
        <button
          onClick={isSubscriptionActive ? handleStripeCheckout : undefined}
          disabled={isLoading || !isSubscriptionActive || !isAuthenticated}
          className={cn(upgradeButtonStyle, COMMON_BUTTON_STYLE)}
          data-ph-element={
            isSubscriptionActive
              ? WORKSPACE_SETTINGS_TRACKER_ELEMENTS.BILLING_UPGRADE_BUTTON(subscriptionType)
              : WORKSPACE_SETTINGS_TRACKER_ELEMENTS.BILLING_TALK_TO_SALES_BUTTON
          }
        >
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Loader.Item height="1rem" width="1rem" />
              <span>Redirecting to Stripe...</span>
            </div>
          ) : isSubscriptionActive ? (
            `Upgrade to ${subscriptionName}`
          ) : subscriptionType === EProductSubscriptionEnum.ENTERPRISE ? (
            "Contact Sales"
          ) : (
            "Contact Sales"
          )}
        </button>
      </div>
    </div>
  );
});
