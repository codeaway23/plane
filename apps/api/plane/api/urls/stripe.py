"""
URL patterns for Stripe API endpoints
"""

from django.conf import settings
from django.urls import path
from plane.api.views import (
    StripeCheckoutView,
    StripeSubscriptionView,
    StripeSubscriptionUpdateView,
    StripeSubscriptionRestartView,
    StripeInvoicesView,
    StripeWebhookView,
    StripeSubscriptionStatusView,
    StripeCheckoutCompletionView
)

urlpatterns = [
    # Checkout session creation
    path(
        "workspaces/<str:slug>/stripe/checkout/",
        StripeCheckoutView.as_view(),
        name="stripe-checkout"
    ),
    
    # Checkout completion
    path(
        "stripe/checkout/complete/",
        StripeCheckoutCompletionView.as_view(),
        name="stripe-checkout-complete"
    ),
    
    # Subscription management
    path(
        "workspaces/<str:slug>/stripe/subscriptions/<str:subscription_id>/",
        StripeSubscriptionView.as_view(),
        name="stripe-subscription"
    ),
    
    # Subscription updates
    path(
        "workspaces/<str:slug>/stripe/subscriptions/<str:subscription_id>/update/",
        StripeSubscriptionUpdateView.as_view(),
        name="stripe-subscription-update"
    ),
    
    # Subscription restart
    path(
        "workspaces/<str:slug>/stripe/subscriptions/<str:subscription_id>/restart/",
        StripeSubscriptionRestartView.as_view(),
        name="stripe-subscription-restart"
    ),
    
    # Invoices
    path(
        "workspaces/<str:slug>/stripe/invoices/",
        StripeInvoicesView.as_view(),
        name="stripe-invoices"
    ),
    
    # Subscription status
    path(
        "workspaces/<str:slug>/stripe/subscription-status/",
        StripeSubscriptionStatusView.as_view(),
        name="stripe-subscription-status"
    ),
    
    # Webhook endpoint (no workspace slug needed)
    path(
        "stripe/webhook/",
        StripeWebhookView.as_view(),
        name="stripe-webhook"
    ),
]
