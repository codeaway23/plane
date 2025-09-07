import { EProductSubscriptionEnum, IPaymentProduct, TBillingFrequency, TProductBillingFrequency } from "@plane/types";

/**
 * Default billing frequency for each product subscription type
 */
export const DEFAULT_PRODUCT_BILLING_FREQUENCY: TProductBillingFrequency = {
  [EProductSubscriptionEnum.FREE]: undefined,
  [EProductSubscriptionEnum.STARTER]: "month",
  [EProductSubscriptionEnum.PRO]: "month",
  [EProductSubscriptionEnum.ENTERPRISE]: "month",
  [EProductSubscriptionEnum.CORE_AI_PACK]: "month",
  [EProductSubscriptionEnum.SCALE_AI_PACK]: "month",
};

/**
 * Subscription types that support billing frequency toggle (monthly/yearly)
 */
export const SUBSCRIPTION_WITH_BILLING_FREQUENCY = [
  EProductSubscriptionEnum.STARTER,
  EProductSubscriptionEnum.PRO,
  EProductSubscriptionEnum.ENTERPRISE,
  EProductSubscriptionEnum.CORE_AI_PACK,
  EProductSubscriptionEnum.SCALE_AI_PACK,
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
  [EProductSubscriptionEnum.CORE_AI_PACK]: {
    id: EProductSubscriptionEnum.CORE_AI_PACK,
    name: "Core AI Pack",
    description: "100 general runs or 20 code runs per month. Perfect for small teams getting started with AI.",
    type: "CORE_AI_PACK",
    prices: [
      {
        id: `price_monthly_${EProductSubscriptionEnum.CORE_AI_PACK}`,
        unit_amount: 5900, // $59.00 per month
        recurring: "month",
        currency: "usd",
        workspace_amount: 5900,
        product: EProductSubscriptionEnum.CORE_AI_PACK,
      },
    ],
    payment_quantity: 1,
    is_active: true,
  },
  [EProductSubscriptionEnum.SCALE_AI_PACK]: {
    id: EProductSubscriptionEnum.SCALE_AI_PACK,
    name: "Scale AI Pack",
    description: "500 general runs or 100 code runs per month. Ideal for growing teams with high AI usage.",
    type: "SCALE_AI_PACK",
    prices: [
      {
        id: `price_monthly_${EProductSubscriptionEnum.SCALE_AI_PACK}`,
        unit_amount: 24900, // $249.00 per month
        recurring: "month",
        currency: "usd",
        workspace_amount: 24900,
        product: EProductSubscriptionEnum.SCALE_AI_PACK,
      },
    ],
    payment_quantity: 1,
    is_active: true,
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
  [EProductSubscriptionEnum.CORE_AI_PACK]: {
    month: "/settings/billing?plan=core-ai-pack&frequency=month", // Will be handled by direct Stripe checkout
    year: "/settings/billing?plan=core-ai-pack&frequency=year", // Will be handled by direct Stripe checkout
  },
  [EProductSubscriptionEnum.SCALE_AI_PACK]: {
    month: "/settings/billing?plan=scale-ai-pack&frequency=month", // Will be handled by direct Stripe checkout
    year: "/settings/billing?plan=scale-ai-pack&frequency=year", // Will be handled by direct Stripe checkout
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
  [EProductSubscriptionEnum.CORE_AI_PACK]: "https://plane.so/ai-packs/core",
  [EProductSubscriptionEnum.SCALE_AI_PACK]: "https://plane.so/ai-packs/scale",
};
