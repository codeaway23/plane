"""
AI Usage Stripe service for handling metered billing subscriptions
Uses Stripe API for all plan details, status, and subscription management
"""

import stripe
import traceback
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.db import models
from plane.db.models import Workspace, User, AIUsageRecord
from django.utils import timezone

logger = logging.getLogger(__name__)


class AIUsageStripeService:
    """Service class for handling AI usage metered billing with Stripe"""
    
    # AI Usage Plan Configuration
    AI_PLANS = {
        'general_run': {
            'name': 'General Run',
            'price_id': settings.STRIPE_AI_GENERAL_RUN_PRICE_ID,
            'cost_per_unit': 0.55,
            'description': '~50k input + 10k output tokens (GPT-5-class)',
            'unit_name': 'run'
        },
        'code_run': {
            'name': 'Code Run', 
            'price_id': settings.STRIPE_AI_CODE_RUN_PRICE_ID,
            'cost_per_unit': 2.50,
            'description': '~150k input + 30k output tokens (Claude Sonnet/Opus-class)',
            'unit_name': 'run'
        }
    }
    
    def __init__(self):
        # Validate Stripe configuration
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY is not configured")
        
        if not settings.STRIPE_AI_GENERAL_RUN_PRICE_ID or not settings.STRIPE_AI_CODE_RUN_PRICE_ID:
            raise ValueError("AI usage price IDs are not configured")
        
        # Initialize Stripe with API key
        stripe.api_key = settings.STRIPE_SECRET_KEY
        logger.info("AI Usage Stripe service initialized successfully")
    
    def get_ai_plans(self) -> Dict[str, Any]:
        """
        Get available AI usage plans with current pricing from Stripe
        
        Returns:
            Dictionary containing AI plan details
        """
        try:
            plans = {}
            
            for plan_type, plan_config in self.AI_PLANS.items():
                try:
                    # Fetch current price details from Stripe
                    price = stripe.Price.retrieve(plan_config['price_id'])
                    product = stripe.Product.retrieve(price.product)
                    
                    plans[plan_type] = {
                        'type': plan_type,
                        'name': plan_config['name'],
                        'price_id': plan_config['price_id'],
                        'cost_per_unit': plan_config['cost_per_unit'],
                        'description': plan_config['description'],
                        'unit_name': plan_config['unit_name'],
                        'stripe_price': {
                            'id': price.id,
                            'unit_amount': price.unit_amount,
                            'currency': price.currency,
                            'recurring': price.recurring,
                            'active': price.active
                        },
                        'stripe_product': {
                            'id': product.id,
                            'name': product.name,
                            'description': product.description,
                            'active': product.active
                        }
                    }
                except stripe.error.StripeError as e:
                    logger.error(f"Error fetching Stripe price for {plan_type}: {str(e)}")
                    # Fallback to config values
                    plans[plan_type] = {
                        'type': plan_type,
                        'name': plan_config['name'],
                        'price_id': plan_config['price_id'],
                        'cost_per_unit': plan_config['cost_per_unit'],
                        'description': plan_config['description'],
                        'unit_name': plan_config['unit_name'],
                        'error': f"Unable to fetch current pricing: {str(e)}"
                    }
            
            return plans
            
        except Exception as e:
            logger.error(f"Error getting AI plans: {str(e)}")
            raise Exception(f"Failed to get AI plans: {str(e)}")
    
    def get_workspace_ai_subscriptions(self, workspace_slug: str) -> Dict[str, Any]:
        """
        Get AI usage subscriptions for a workspace from Stripe

        Args:
            workspace_slug: Workspace slug

        Returns:
            Dictionary containing subscription status for each AI plan
        """
        try:
            workspace = Workspace.objects.get(slug=workspace_slug)

            if not workspace.stripe_customer_id:
                return {
                    'general_run': {'active': False, 'subscription': None},
                    'code_run': {'active': False, 'subscription': None}
                }

            subscriptions = stripe.Subscription.list(
                customer=workspace.stripe_customer_id,
                status='active',
                limit=100
            )

            result = {
                'general_run': {'active': False, 'subscription': None},
                'code_run': {'active': False, 'subscription': None}
            }

            # Check each subscription for AI usage plans
            for subscription in subscriptions.data:
                # Fetch subscription items separately
                try:
                    subscription_items = stripe.SubscriptionItem.list(subscription=subscription.id)
                    for item in subscription_items.data:
                        try:
                            price_id = item.price.id

                            # Check if this is an AI usage subscription
                            if price_id == settings.STRIPE_AI_GENERAL_RUN_PRICE_ID:
                                result['general_run'] = {
                                    'active': True,
                                    'subscription': self._format_subscription_data(subscription, item)
                                }
                            elif price_id == settings.STRIPE_AI_CODE_RUN_PRICE_ID:
                                result['code_run'] = {
                                    'active': True,
                                    'subscription': self._format_subscription_data(subscription, item)
                                }
                        except Exception as item_error:
                            logger.error(f"[AIUsageStripeService] Error processing item for subscription {subscription.id}: {str(item_error)}")
                except Exception as e:
                    logger.error(f"[AIUsageStripeService] Error fetching items for subscription {subscription.id}: {str(e)}")

            return result
        except Workspace.DoesNotExist:
            logger.warning(f"[AIUsageStripeService] Workspace not found: {workspace_slug}")
            return {
                'general_run': {'active': False, 'subscription': None},
                'code_run': {'active': False, 'subscription': None}
            }
        except Exception as e:
            logger.error(f"[AIUsageStripeService] Error getting workspace AI subscriptions: {traceback.format_exc()}")
            return {
                'general_run': {'active': False, 'subscription': None},
                'code_run': {'active': False, 'subscription': None}
            }
    
    def create_ai_usage_checkout_session(
        self, 
        workspace: Workspace, 
        user: User, 
        plan_type: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for AI usage subscription
        
        Args:
            workspace: The workspace object
            user: The user initiating the checkout
            plan_type: Type of AI plan ('general_run' or 'code_run')
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            
        Returns:
            Dictionary containing checkout session data
        """
        try:
            if plan_type not in self.AI_PLANS:
                raise ValueError(f"Invalid plan type: {plan_type}")
            
            plan_config = self.AI_PLANS[plan_type]
            
            # Check if workspace already has this AI plan active
            current_subscriptions = self.get_workspace_ai_subscriptions(workspace.slug)
            if current_subscriptions[plan_type]['active']:
                raise ValueError(f"Workspace already has {plan_config['name']} subscription active")
            
            logger.info(f"Creating AI usage checkout session for workspace {workspace.slug}, plan {plan_type}")
            
            # Create checkout session for metered subscription
            checkout_params = {
                'payment_method_types': ['card'],
                'line_items': [
                    {
                        'price': plan_config['price_id'],
                        # No quantity specified for metered billing
                    }
                ],
                'mode': 'subscription',
                'success_url': f"{success_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}&plan_type={plan_type}",
                'cancel_url': cancel_url,
                'client_reference_id': str(workspace.id),
                'metadata': {
                    'workspace_id': str(workspace.id),
                    'user_id': str(user.id),
                    'workspace_slug': workspace.slug,
                    'plan_type': plan_type,
                    'ai_usage': 'true'
                },
                'subscription_data': {
                    'metadata': {
                        'workspace_id': str(workspace.id),
                        'workspace_slug': workspace.slug,
                        'user_id': str(user.id),
                        'plan_type': plan_type,
                        'ai_usage': 'true'
                    }
                },
                'billing_address_collection': 'required',
                'allow_promotion_codes': True,
            }
            
            # Use existing customer if available, otherwise create new one
            if workspace.stripe_customer_id:
                checkout_params['customer'] = workspace.stripe_customer_id
                logger.info(f"Using existing customer {workspace.stripe_customer_id} for AI usage checkout")
            else:
                checkout_params['customer_email'] = user.email if user.email else None
                logger.info(f"Creating new customer for AI usage checkout")
            
            checkout_session = stripe.checkout.Session.create(**checkout_params)
            
            logger.info(f"AI usage checkout session created successfully: {checkout_session.id}")
            
            return {
                'id': checkout_session.id,
                'url': checkout_session.url,
                'status': checkout_session.status,
                'payment_status': checkout_session.payment_status,
                'plan_type': plan_type,
                'plan_name': plan_config['name']
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating AI usage checkout session: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating AI usage checkout session: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    def cancel_ai_usage_subscription(self, workspace_slug: str, plan_type: str) -> Dict[str, Any]:
        """
        Cancel an AI usage subscription
        
        Args:
            workspace_slug: Workspace slug
            plan_type: Type of AI plan to cancel
            
        Returns:
            Dictionary containing cancellation results
        """
        try:
            if plan_type not in self.AI_PLANS:
                raise ValueError(f"Invalid plan type: {plan_type}")
            
            subscriptions = self.get_workspace_ai_subscriptions(workspace_slug)
            
            if not subscriptions[plan_type]['active']:
                raise ValueError(f"No active {plan_type} subscription found")
            
            subscription_id = subscriptions[plan_type]['subscription']['id']
            
            logger.info(f"Cancelling AI usage subscription {subscription_id} for workspace {workspace_slug}")
            
            # Cancel subscription immediately
            subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f"AI usage subscription {subscription_id} cancelled successfully")
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'cancelled_immediately': True,
                'status': getattr(subscription, 'status', 'canceled')
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling AI usage subscription: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error cancelling AI usage subscription: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    def restart_ai_usage_subscription(self, workspace_slug: str, plan_type: str) -> Dict[str, Any]:
        """
        Restart a cancelled AI usage subscription
        
        Args:
            workspace_slug: Workspace slug
            plan_type: Type of AI plan to restart
            
        Returns:
            Dictionary containing restart results
        """
        try:
            if plan_type not in self.AI_PLANS:
                raise ValueError(f"Invalid plan type: {plan_type}")
            
            subscriptions = self.get_workspace_ai_subscriptions(workspace_slug)
            
            if not subscriptions[plan_type]['active']:
                raise ValueError(f"No active {plan_type} subscription found")
            
            subscription_id = subscriptions[plan_type]['subscription']['id']
            
            logger.info(f"Restarting AI usage subscription {subscription_id} for workspace {workspace_slug}")
            
            # Restart subscription by removing cancel_at_period_end
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            
            logger.info(f"AI usage subscription {subscription_id} restarted successfully")
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'cancel_at_period_end': getattr(subscription, 'cancel_at_period_end', False),
                'current_period_end': getattr(subscription, 'current_period_end', None)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error restarting AI usage subscription: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error restarting AI usage subscription: {str(e)}")
            raise Exception(f"Failed to restart subscription: {str(e)}")
    
    def record_ai_usage(
        self, 
        workspace_slug: str, 
        user: User, 
        plan_type: str, 
        usage_count: int = 1,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Record AI usage for metered billing
        
        Args:
            workspace_slug: Workspace slug
            user: User who used the AI
            plan_type: Type of AI usage
            usage_count: Number of usage units
            metadata: Additional metadata
            
        Returns:
            Dictionary containing usage record results
        """
        try:
            if plan_type not in self.AI_PLANS:
                raise ValueError(f"Invalid plan type: {plan_type}")
            
            workspace = Workspace.objects.get(slug=workspace_slug)
            plan_config = self.AI_PLANS[plan_type]
            
            # Check if workspace has active subscription for this plan
            subscriptions = self.get_workspace_ai_subscriptions(workspace_slug)
            if not subscriptions[plan_type]['active']:
                raise ValueError(f"No active {plan_type} subscription found")
            
            subscription_id = subscriptions[plan_type]['subscription']['id']
            
            # Create usage record in Stripe
            usage_record = stripe.UsageRecord.create(
                subscription_item=subscriptions[plan_type]['subscription']['subscription_item_id'],
                quantity=usage_count,
                timestamp=int(timezone.now().timestamp()),
                action='increment'
            )
            
            # Store usage record in our database
            ai_usage_record = AIUsageRecord.objects.create(
                workspace=workspace,
                user=user,
                plan_type=plan_type,
                usage_count=usage_count,
                cost_per_unit=plan_config['cost_per_unit'],
                metadata=metadata or {},
                stripe_usage_record_id=usage_record.id
            )
            
            logger.info(f"Recorded AI usage: {usage_count} {plan_type} units for workspace {workspace_slug}")
            
            return {
                'success': True,
                'usage_record_id': ai_usage_record.id,
                'stripe_usage_record_id': usage_record.id,
                'usage_count': usage_count,
                'total_cost': ai_usage_record.total_cost
            }
            
        except Workspace.DoesNotExist:
            raise ValueError(f"Workspace not found: {workspace_slug}")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error recording AI usage: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error recording AI usage: {str(e)}")
            raise Exception(f"Failed to record usage: {str(e)}")
    
    def get_ai_usage_history(self, workspace_slug: str, plan_type: str = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get AI usage history for a workspace
        
        Args:
            workspace_slug: Workspace slug
            plan_type: Optional filter by plan type
            limit: Number of records to return
            
        Returns:
            Dictionary containing usage history
        """
        try:
            workspace = Workspace.objects.get(slug=workspace_slug)
            
            # Build query
            query = AIUsageRecord.objects.filter(workspace=workspace)
            if plan_type:
                query = query.filter(plan_type=plan_type)
            
            usage_records = query.order_by('-created_at')[:limit]
            
            # Calculate totals
            total_usage = query.aggregate(
                total_count=models.Sum('usage_count'),
                total_cost=models.Sum('total_cost')
            )
            
            return {
                'usage_records': [
                    {
                        'id': record.id,
                        'plan_type': record.plan_type,
                        'usage_count': record.usage_count,
                        'cost_per_unit': float(record.cost_per_unit),
                        'total_cost': float(record.total_cost),
                        'created_at': record.created_at,
                        'metadata': record.metadata
                    }
                    for record in usage_records
                ],
                'total_usage_count': total_usage['total_count'] or 0,
                'total_cost': float(total_usage['total_cost'] or 0)
            }
            
        except Workspace.DoesNotExist:
            raise ValueError(f"Workspace not found: {workspace_slug}")
        except Exception as e:
            logger.error(f"Error getting AI usage history: {str(e)}")
            raise Exception(f"Failed to get usage history: {str(e)}")
    
    def _format_subscription_data(self, subscription: Any, item: Any) -> Dict[str, Any]:
        """Format Stripe subscription data for our use"""
        try:
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_start': getattr(subscription, 'current_period_start', None),
                'current_period_end': getattr(subscription, 'current_period_end', None),
                'cancel_at_period_end': getattr(subscription, 'cancel_at_period_end', False),
                'canceled_at': getattr(subscription, 'canceled_at', None),
                'created': getattr(subscription, 'created', None),
                'subscription_item_id': item.id,
                'quantity': item.quantity,
                'price_id': item.price.id
            }
        except Exception as e:
            logger.error(f"[AIUsageStripeService] Error formatting subscription data: {str(e)}")
            # Return minimal data if formatting fails
            return {
                'id': getattr(subscription, 'id', 'unknown'),
                'status': getattr(subscription, 'status', 'unknown'),
                'current_period_start': None,
                'current_period_end': None,
                'cancel_at_period_end': False,
                'canceled_at': None,
                'created': None,
                'subscription_item_id': getattr(item, 'id', 'unknown'),
                'quantity': getattr(item, 'quantity', 1),
                'price_id': getattr(item.price, 'id', 'unknown')
            }
