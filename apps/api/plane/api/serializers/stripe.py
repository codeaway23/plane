"""
Serializers for Stripe-related operations
"""

from rest_framework import serializers
from plane.db.models import Workspace


class StripeCheckoutSessionSerializer(serializers.Serializer):
    """Serializer for creating Stripe checkout sessions"""
    
    price_id = serializers.CharField(max_length=255, help_text="Stripe price ID for the subscription")
    success_url = serializers.URLField(required=False, help_text="URL to redirect after successful payment")
    cancel_url = serializers.URLField(required=False, help_text="URL to redirect if payment is cancelled")
    
    def validate_price_id(self, value):
        """Validate that price_id is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Price ID cannot be empty")
        return value.strip()


class StripeWebhookSerializer(serializers.Serializer):
    """Serializer for Stripe webhook events"""
    
    id = serializers.CharField(max_length=255)
    object = serializers.CharField(max_length=50)
    type = serializers.CharField(max_length=100)
    data = serializers.DictField()
    created = serializers.IntegerField()
    livemode = serializers.BooleanField()
    pending_webhooks = serializers.IntegerField()
    request = serializers.DictField(required=False)


class SubscriptionSerializer(serializers.Serializer):
    """Serializer for subscription data"""
    
    id = serializers.CharField(max_length=255)
    status = serializers.CharField(max_length=50)
    current_period_start = serializers.IntegerField()
    current_period_end = serializers.IntegerField()
    cancel_at_period_end = serializers.BooleanField()
    customer = serializers.CharField(max_length=255)
    workspace_id = serializers.CharField(max_length=255, required=False)
    workspace_slug = serializers.CharField(max_length=255, required=False)
