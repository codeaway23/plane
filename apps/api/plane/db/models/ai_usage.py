"""
AI Usage models for tracking metered usage records only
All plan details and status will be fetched from Stripe API
"""

from django.db import models
from django.conf import settings
from .base import BaseModel


class AIUsageRecord(BaseModel):
    """
    Model to track individual AI usage events for billing
    This is the only model we need - everything else comes from Stripe API
    """
    
    PLAN_TYPES = (
        ('general_run', 'General Run'),
        ('code_run', 'Code Run'),
    )
    
    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="ai_usage_records"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_usage_records"
    )
    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPES,
        help_text="Type of AI usage plan used"
    )
    usage_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of runs/usage units"
    )
    cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cost per usage unit in USD"
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total cost for this usage record"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about the usage"
    )
    stripe_usage_record_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Stripe usage record ID for metered billing"
    )
    
    class Meta:
        verbose_name = "AI Usage Record"
        verbose_name_plural = "AI Usage Records"
        db_table = "ai_usage_records"
        ordering = ("-created_at",)
    
    def __str__(self):
        return f"{self.workspace.name} - {self.get_plan_type_display()} - {self.usage_count} units"
    
    def save(self, *args, **kwargs):
        """Calculate total cost before saving"""
        self.total_cost = self.usage_count * self.cost_per_unit
        super().save(*args, **kwargs)
