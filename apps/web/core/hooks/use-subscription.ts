import { useState, useEffect } from "react";
import { EProductSubscriptionEnum } from "@plane/types";
import { StripeService } from "@/services/stripe.service";
import { useWorkspace } from "@/hooks/store/use-workspace";

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

export const useSubscription = () => {
  const { currentWorkspace } = useWorkspace();
  const [subscriptionData, setSubscriptionData] = useState<SubscriptionData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscriptionData = async () => {
    if (!currentWorkspace) return;

    setIsLoading(true);
    setError(null);

    try {
      const stripeService = new StripeService();
      const data = await stripeService.getSubscriptionStatus(currentWorkspace.slug);

      if (data.id && data.status === "active") {
        setSubscriptionData({
          id: data.id,
          status: data.status,
          current_period_start: data.current_period_start || 0,
          current_period_end: data.current_period_end || 0,
          cancel_at_period_end: data.cancel_at_period_end,
          customer: data.customer || "",
          price_id: data.price_id || undefined,
        });
      } else {
        setSubscriptionData(null);
      }
    } catch (err: any) {
      const errorMessage = err?.response?.data?.error || err?.message || "Failed to load subscription data.";
      setError(errorMessage);
      console.error("Error fetching subscription data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const getCurrentSubscriptionType = (): EProductSubscriptionEnum => {
    if (!subscriptionData?.price_id) return EProductSubscriptionEnum.FREE;

    const priceIdMap: Record<string, EProductSubscriptionEnum> = {
      price_1S3sXzEPoCJr6b2KycIoGsqy: EProductSubscriptionEnum.STARTER,
      price_1S3sgqEPoCJr6b2K97l2hJU7: EProductSubscriptionEnum.PRO,
    };

    return priceIdMap[subscriptionData.price_id] || EProductSubscriptionEnum.FREE;
  };

  const canManageUsers = (): boolean => {
    const planType = getCurrentSubscriptionType();
    return (
      planType === EProductSubscriptionEnum.STARTER ||
      planType === EProductSubscriptionEnum.PRO ||
      planType === EProductSubscriptionEnum.ENTERPRISE
    );
  };

  const isActiveSubscription = (): boolean => {
    return subscriptionData?.status === "active";
  };

  useEffect(() => {
    if (currentWorkspace) {
      fetchSubscriptionData();
    }
  }, [currentWorkspace]);

  return {
    subscriptionData,
    isLoading,
    error,
    getCurrentSubscriptionType,
    canManageUsers,
    isActiveSubscription,
    refetch: fetchSubscriptionData,
  };
};
