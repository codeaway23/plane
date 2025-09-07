"""
Serializers for AI usage billing
"""

from rest_framework import serializers
from plane.db.models import AIUsageRecord


class AIUsageCheckoutSerializer(serializers.Serializer):
    """Serializer for AI usage checkout session creation"""
    
    plan_type = serializers.ChoiceField(
        choices=['general_run', 'code_run'],
        help_text="Type of AI usage plan"
    )
    success_url = serializers.URLField(
        required=False,
        help_text="URL to redirect after successful payment"
    )
    cancel_url = serializers.URLField(
        required=False,
        help_text="URL to redirect if payment is cancelled"
    )


class AIUsageRecordSerializer(serializers.Serializer):
    """Serializer for recording AI usage"""
    
    plan_type = serializers.ChoiceField(
        choices=['general_run', 'code_run'],
        help_text="Type of AI usage plan"
    )
    usage_count = serializers.IntegerField(
        min_value=1,
        default=1,
        help_text="Number of usage units"
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional metadata about the usage"
    )


class AIUsageHistorySerializer(serializers.ModelSerializer):
    """Serializer for AI usage history"""
    
    plan_type_display = serializers.CharField(source='get_plan_type_display', read_only=True)
    
    class Meta:
        model = AIUsageRecord
        fields = [
            'id',
            'plan_type',
            'plan_type_display',
            'usage_count',
            'cost_per_unit',
            'total_cost',
            'created_at',
            'metadata'
        ]
        read_only_fields = fields
