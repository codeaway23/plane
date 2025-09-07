"""
Serializers for AI Pack subscription management
"""

from rest_framework import serializers


class AIPackCheckoutSerializer(serializers.Serializer):
    """Serializer for AI Pack checkout session creation"""
    
    pack_type = serializers.ChoiceField(
        choices=['core_ai_pack', 'scale_ai_pack'],
        help_text="Type of AI Pack to subscribe to"
    )
    
    def validate_pack_type(self, value):
        """Validate pack type"""
        if value not in ['core_ai_pack', 'scale_ai_pack']:
            raise serializers.ValidationError("Invalid pack type")
        return value


class AIPackUpgradeSerializer(serializers.Serializer):
    """Serializer for AI Pack subscription upgrade"""
    
    pack_type = serializers.ChoiceField(
        choices=['core_ai_pack', 'scale_ai_pack'],
        help_text="New AI Pack type to upgrade to"
    )
    
    def validate_pack_type(self, value):
        """Validate pack type"""
        if value not in ['core_ai_pack', 'scale_ai_pack']:
            raise serializers.ValidationError("Invalid pack type")
        return value
