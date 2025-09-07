"""
URL patterns for AI Pack API endpoints
"""

from django.urls import path
from plane.api.views.ai_pack import (
    AIPackPlansView,
    AIPackSubscriptionView,
    AIPackCheckoutView,
    AIPackSubscriptionManagementView,
    AIPackUpgradeView,
    AIPackUsageLimitsView
)

urlpatterns = [
    # AI Pack Plans
    path(
        "workspaces/<str:slug>/ai-packs/plans/",
        AIPackPlansView.as_view(),
        name="ai-pack-plans"
    ),
    
    # AI Pack Subscription
    path(
        "workspaces/<str:slug>/ai-packs/subscription/",
        AIPackSubscriptionView.as_view(),
        name="ai-pack-subscription"
    ),
    
    # AI Pack Checkout
    path(
        "workspaces/<str:slug>/ai-packs/checkout/",
        AIPackCheckoutView.as_view(),
        name="ai-pack-checkout"
    ),
    
    # AI Pack Subscription Management
    path(
        "workspaces/<str:slug>/ai-packs/subscription/<str:action_type>/",
        AIPackSubscriptionManagementView.as_view(),
        name="ai-pack-subscription-management"
    ),
    
    # AI Pack Upgrade
    path(
        "workspaces/<str:slug>/ai-packs/upgrade/",
        AIPackUpgradeView.as_view(),
        name="ai-pack-upgrade"
    ),
    
    # AI Pack Usage Limits
    path(
        "workspaces/<str:slug>/ai-packs/usage-limits/",
        AIPackUsageLimitsView.as_view(),
        name="ai-pack-usage-limits"
    ),
]
