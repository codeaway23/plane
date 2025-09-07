"""
URL patterns for AI Usage API endpoints
"""

from django.urls import path
from plane.api.views.ai_usage import (
    AIUsagePlansView,
    AIUsageSubscriptionsView,
    AIUsageCheckoutView,
    AIUsageSubscriptionManagementView,
    AIUsageHistoryView,
    AIUsageRecordView
)

urlpatterns = [
    # AI Usage Plans
    path(
        "workspaces/<str:slug>/ai-usage/plans/",
        AIUsagePlansView.as_view(),
        name="ai-usage-plans"
    ),
    
    # AI Usage Subscriptions
    path(
        "workspaces/<str:slug>/ai-usage/subscriptions/",
        AIUsageSubscriptionsView.as_view(),
        name="ai-usage-subscriptions"
    ),
    
    # AI Usage Checkout
    path(
        "workspaces/<str:slug>/ai-usage/checkout/",
        AIUsageCheckoutView.as_view(),
        name="ai-usage-checkout"
    ),
    
    # AI Usage Subscription Management
    path(
        "workspaces/<str:slug>/ai-usage/subscriptions/<str:action_type>/",
        AIUsageSubscriptionManagementView.as_view(),
        name="ai-usage-subscription-management"
    ),
    
    # AI Usage History
    path(
        "workspaces/<str:slug>/ai-usage/history/",
        AIUsageHistoryView.as_view(),
        name="ai-usage-history"
    ),
    
    # AI Usage Recording
    path(
        "workspaces/<str:slug>/ai-usage/record/",
        AIUsageRecordView.as_view(),
        name="ai-usage-record"
    ),
]
