import { EProductSubscriptionEnum, IPaymentProduct, TBillingFrequency, TProductBillingFrequency } from "@plane/types";

/**
 * Default billing frequency for each product subscription type
 */
export const DEFAULT_PRODUCT_BILLING_FREQUENCY: TProductBillingFrequency = {
  [EProductSubscriptionEnum.FREE]: undefined,
  [EProductSubscriptionEnum.STARTER]: "month",
  [EProductSubscriptionEnum.PRO]: "month",
  [EProductSubscriptionEnum.ENTERPRISE]: "month",
};

/**
 * Subscription types that support billing frequency toggle (monthly/yearly)
 */
export const SUBSCRIPTION_WITH_BILLING_FREQUENCY = [
  EProductSubscriptionEnum.STARTER,
  EProductSubscriptionEnum.PRO,
  EProductSubscriptionEnum.ENTERPRISE,
];

/**
 * Mapping of product subscription types to their respective payment product details
 * Used to provide information about each product's pricing and features
 */
export const PLANE_COMMUNITY_PRODUCTS: Record<string, IPaymentProduct> = {
  [EProductSubscriptionEnum.PRO]: {
    id: EProductSubscriptionEnum.PRO,
    name: "Pro Plan",
    description:
      "Advanced features with more AI power. Includes all Starter features, 10 pooled general AI runs, advanced features, and priority support.",
    type: "PRO",
    prices: [
      {
        id: `price_monthly_${EProductSubscriptionEnum.PRO}`,
        unit_amount: 1400, // $14.00 per month
        recurring: "month",
        currency: "usd",
        workspace_amount: 1400,
        product: EProductSubscriptionEnum.PRO,
      },
    ],
    payment_quantity: 1,
    is_active: true,
  },
  [EProductSubscriptionEnum.STARTER]: {
    id: EProductSubscriptionEnum.STARTER,
    name: "Starter Plan",
    description:
      "Core PM features with AI assistance. Includes 5 pooled general AI runs, unlimited users, and basic support.",
    type: "STARTER",
    prices: [
      {
        id: `price_monthly_${EProductSubscriptionEnum.STARTER}`,
        unit_amount: 800, // $8.00 per month
        recurring: "month",
        currency: "usd",
        workspace_amount: 800,
        product: EProductSubscriptionEnum.STARTER,
      },
    ],
    payment_quantity: 1,
    is_active: true,
  },
  [EProductSubscriptionEnum.ENTERPRISE]: {
    id: EProductSubscriptionEnum.ENTERPRISE,
    name: "Plane Enterprise",
    description: "",
    type: "ENTERPRISE",
    prices: [
      {
        id: `price_yearly_${EProductSubscriptionEnum.ENTERPRISE}`,
        unit_amount: 0,
        recurring: "year",
        currency: "usd",
        workspace_amount: 0,
        product: EProductSubscriptionEnum.ENTERPRISE,
      },
      {
        id: `price_monthly_${EProductSubscriptionEnum.ENTERPRISE}`,
        unit_amount: 0,
        recurring: "month",
        currency: "usd",
        workspace_amount: 0,
        product: EProductSubscriptionEnum.ENTERPRISE,
      },
    ],
    payment_quantity: 1,
    is_active: false,
  },
};

/**
 * URL for the "Talk to Sales" page where users can contact sales team
 */
export const TALK_TO_SALES_URL = "https://plane.so/talk-to-sales";

/**
 * Mapping of subscription types to their respective upgrade/redirection URLs based on billing frequency
 * Used for self-hosted installations to redirect users to appropriate upgrade pages
 */
export const SUBSCRIPTION_REDIRECTION_URLS: Record<EProductSubscriptionEnum, Record<TBillingFrequency, string>> = {
  [EProductSubscriptionEnum.FREE]: {
    month: TALK_TO_SALES_URL,
    year: TALK_TO_SALES_URL,
  },
  [EProductSubscriptionEnum.STARTER]: {
    month: "/settings/billing?plan=starter&frequency=month", // Will be handled by direct Stripe checkout
    year: "/settings/billing?plan=starter&frequency=year", // Will be handled by direct Stripe checkout
  },
  [EProductSubscriptionEnum.PRO]: {
    month: "/settings/billing?plan=pro&frequency=month", // Will be handled by direct Stripe checkout
    year: "/settings/billing?plan=pro&frequency=year", // Will be handled by direct Stripe checkout
  },
  [EProductSubscriptionEnum.ENTERPRISE]: {
    month: TALK_TO_SALES_URL,
    year: TALK_TO_SALES_URL,
  },
};

/**
 * Mapping of subscription types to their respective marketing webpage URLs
 * Used to direct users to learn more about each plan's features and pricing
 */
export const SUBSCRIPTION_WEBPAGE_URLS: Record<EProductSubscriptionEnum, string> = {
  [EProductSubscriptionEnum.FREE]: TALK_TO_SALES_URL,
  [EProductSubscriptionEnum.STARTER]: "https://plane.so/starter",
  [EProductSubscriptionEnum.PRO]: "https://plane.so/pro",
  [EProductSubscriptionEnum.ENTERPRISE]: "https://plane.so/enterprise",
};
