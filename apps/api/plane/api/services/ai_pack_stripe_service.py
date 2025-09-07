"""
AI Pack Stripe service for handling Core AI Pack and Scale AI Pack subscriptions
"""

import stripe
import traceback
import logging
from django.conf import settings
from typing import Dict, Any, Optional
from plane.db.models import Workspace, User

logger = logging.getLogger(__name__)


class AIPackStripeService:
    """Service class for handling AI Pack subscriptions with Stripe"""
    
    # AI Pack Configuration
    AI_PACKS = {
        'core_ai_pack': {
            'name': 'Core AI Pack',
            'price_id': settings.STRIPE_CORE_AI_PACK_PRICE_ID,
            'monthly_price': 59.00,
            'general_runs': 100,
            'code_runs': 20,
            'description': '100 general runs or 20 code runs per month. Perfect for small teams getting started with AI.',
        },
        'scale_ai_pack': {
            'name': 'Scale AI Pack',
            'price_id': settings.STRIPE_SCALE_AI_PACK_PRICE_ID,
            'monthly_price': 249.00,
            'general_runs': 500,
            'code_runs': 100,
            'description': '500 general runs or 100 code runs per month. Ideal for growing teams with high AI usage.',
        }
    }
    
    def __init__(self):
        # Validate Stripe configuration
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY is not configured")
        
        if not settings.STRIPE_CORE_AI_PACK_PRICE_ID or not settings.STRIPE_SCALE_AI_PACK_PRICE_ID:
            raise ValueError("AI Pack price IDs are not configured")
        
        # Initialize Stripe with API key
        stripe.api_key = settings.STRIPE_SECRET_KEY
        logger.info("AI Pack Stripe service initialized successfully")
    
    def get_ai_packs(self) -> Dict[str, Any]:
        """
        Get available AI Pack plans with current pricing
        
        Returns:
            Dictionary containing AI Pack plans data
        """
        try:
            result = {}
            
            for pack_type, pack_config in self.AI_PACKS.items():
                try:
                    # Get price details from Stripe
                    price = stripe.Price.retrieve(pack_config['price_id'])
                    product = stripe.Product.retrieve(price.product)
                    
                    result[pack_type] = {
                        'type': pack_type,
                        'name': pack_config['name'],
                        'price_id': pack_config['price_id'],
                        'monthly_price': pack_config['monthly_price'],
                        'general_runs': pack_config['general_runs'],
                        'code_runs': pack_config['code_runs'],
                        'description': pack_config['description'],
                        'stripe_price': {
                            'id': price.id,
                            'unit_amount': price.unit_amount,
                            'currency': price.currency,
                            'active': price.active,
                        },
                        'stripe_product': {
                            'id': product.id,
                            'name': product.name,
                            'description': product.description,
                            'active': product.active,
                        }
                    }
                except stripe.error.StripeError as e:
                    logger.error(f"Error fetching Stripe data for {pack_type}: {str(e)}")
                    result[pack_type] = {
                        'type': pack_type,
                        'name': pack_config['name'],
                        'price_id': pack_config['price_id'],
                        'monthly_price': pack_config['monthly_price'],
                        'general_runs': pack_config['general_runs'],
                        'code_runs': pack_config['code_runs'],
                        'description': pack_config['description'],
                        'error': f"Failed to fetch Stripe data: {str(e)}"
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting AI Pack plans: {str(e)}")
            raise Exception(f"Failed to get AI Pack plans: {str(e)}")
    
    def get_workspace_ai_pack_subscription(self, workspace_slug: str) -> Dict[str, Any]:
        """
        Get AI Pack subscription for a workspace from Stripe

        Args:
            workspace_slug: Workspace slug

        Returns:
            Dictionary containing subscription status
        """
        try:
            workspace = Workspace.objects.get(slug=workspace_slug)

            if not workspace.stripe_customer_id:
                return {
                    'active': False,
                    'subscription': None,
                    'pack_type': None
                }

            subscriptions = stripe.Subscription.list(
                customer=workspace.stripe_customer_id,
                status='active',
                limit=100
            )

            all_subscriptions = stripe.Subscription.list(
                customer=workspace.stripe_customer_id,
                limit=100
            )

            for pack_type, pack_config in self.AI_PACKS.items():
                price_id = pack_config['price_id']

                price_subscriptions = stripe.Subscription.list(
                    customer=workspace.stripe_customer_id,
                    status='active',
                    price=price_id,
                    limit=10
                )

                if price_subscriptions.data:
                    subscription = price_subscriptions.data[0]

                    period_start = getattr(subscription, 'current_period_start', None)
                    period_end = getattr(subscription, 'current_period_end', None)

                    if period_start is None or period_end is None:
                        try:
                            if hasattr(subscription.items, 'data'):
                                items_data = subscription.items.data
                            elif callable(subscription.items):
                                items_data = subscription.items().data
                            else:
                                items_data = subscription.items

                            if items_data:
                                period_start = getattr(items_data[0], 'current_period_start', period_start)
                                period_end = getattr(items_data[0], 'current_period_end', period_end)
                        except Exception:
                            pass

                    return {
                        'active': True,
                        'subscription': {
                            'id': subscription.id,
                            'status': subscription.status,
                            'current_period_start': period_start,
                            'current_period_end': period_end,
                            'cancel_at_period_end': getattr(subscription, 'cancel_at_period_end', False),
                            'customer': subscription.customer,
                            'price_id': price_id,
                        },
                        'pack_type': pack_type,
                        'pack_config': pack_config
                    }

            for subscription in subscriptions.data:
                try:
                    if hasattr(subscription.items, 'data'):
                        items_data = subscription.items.data
                    elif callable(subscription.items):
                        items_data = subscription.items().data
                    else:
                        items_data = subscription.items

                    for item in items_data:
                        price_id = item.price.id

                        for pack_type, pack_config in self.AI_PACKS.items():
                            if price_id == pack_config['price_id']:
                                period_start = getattr(subscription, 'current_period_start', None)
                                period_end = getattr(subscription, 'current_period_end', None)

                                if period_start is None or period_end is None:
                                    try:
                                        period_start = getattr(item, 'current_period_start', period_start)
                                        period_end = getattr(item, 'current_period_end', period_end)
                                    except Exception:
                                        pass

                                return {
                                    'active': True,
                                    'subscription': {
                                        'id': subscription.id,
                                        'status': subscription.status,
                                        'current_period_start': period_start,
                                        'current_period_end': period_end,
                                        'cancel_at_period_end': getattr(subscription, 'cancel_at_period_end', False),
                                        'customer': subscription.customer,
                                        'price_id': price_id,
                                    },
                                    'pack_type': pack_type,
                                    'pack_config': pack_config
                                }
                except Exception:
                    pass

            return {
                'active': False,
                'subscription': None,
                'pack_type': None
            }

        except Workspace.DoesNotExist:
            return {
                'active': False,
                'subscription': None,
                'pack_type': None
            }
        except Exception:
            return {
                'active': False,
                'subscription': None,
                'pack_type': None
            }
    
    def create_ai_pack_checkout_session(
        self,
        workspace: Workspace,
        user: User,
        pack_type: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for AI Pack subscription
        
        Args:
            workspace: The workspace object
            user: The user initiating the checkout
            pack_type: Type of AI Pack ('core_ai_pack' or 'scale_ai_pack')
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            
        Returns:
            Dictionary containing checkout session data
        """
        try:
            if pack_type not in self.AI_PACKS:
                raise ValueError(f"Invalid pack type: {pack_type}")
            
            pack_config = self.AI_PACKS[pack_type]
            
            # Check if workspace already has an AI Pack subscription
            existing_subscription = self.get_workspace_ai_pack_subscription(workspace.slug)
            if existing_subscription['active']:
                raise ValueError(f"Workspace already has an active AI Pack subscription: {existing_subscription['pack_type']}")
            
            logger.info(f"Creating AI Pack checkout session for workspace {workspace.slug}, user {user.id}, pack {pack_type}")
            
            # Create or get customer
            customer_id = workspace.stripe_customer_id
            if not customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=workspace.name,
                    metadata={
                        'workspace_slug': workspace.slug,
                        'workspace_id': str(workspace.id),
                        'user_id': str(user.id),
                    }
                )
                customer_id = customer.id
                workspace.stripe_customer_id = customer_id
                workspace.save(update_fields=['stripe_customer_id'])
            else:
                customer = stripe.Customer.retrieve(customer_id)
            
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': pack_config['price_id'],
                        'quantity': 1,
                    }
                ],
                mode='subscription',
                customer=customer_id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'workspace_slug': workspace.slug,
                    'workspace_id': str(workspace.id),
                    'user_id': str(user.id),
                    'pack_type': pack_type,
                },
                subscription_data={
                    'metadata': {
                        'workspace_slug': workspace.slug,
                        'workspace_id': str(workspace.id),
                        'pack_type': pack_type,
                    }
                }
            )
            
            return {
                'id': checkout_session.id,
                'url': checkout_session.url,
                'pack_type': pack_type,
                'pack_config': pack_config
            }
            
        except Exception as e:
            logger.error(f"Error creating AI Pack checkout session: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    def create_ai_pack_checkout_session_for_upgrade(
        self,
        workspace: Workspace,
        user: User,
        pack_type: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for AI Pack subscription during upgrade
        This method doesn't check for existing subscriptions since we handle cancellation separately
        
        Args:
            workspace: The workspace object
            user: The user initiating the checkout
            pack_type: Type of AI Pack ('core_ai_pack' or 'scale_ai_pack')
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            
        Returns:
            Dictionary containing checkout session data
        """
        try:
            if pack_type not in self.AI_PACKS:
                raise ValueError(f"Invalid pack type: {pack_type}")
            
            pack_config = self.AI_PACKS[pack_type]
            
            logger.info(f"Creating AI Pack checkout session for upgrade - workspace {workspace.slug}, user {user.id}, pack {pack_type}")
            
            # Create or get customer
            customer_id = workspace.stripe_customer_id
            if not customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=workspace.name,
                    metadata={
                        'workspace_slug': workspace.slug,
                        'workspace_id': str(workspace.id),
                        'user_id': str(user.id),
                    }
                )
                customer_id = customer.id
                workspace.stripe_customer_id = customer_id
                workspace.save(update_fields=['stripe_customer_id'])
            else:
                customer = stripe.Customer.retrieve(customer_id)
            
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': pack_config['price_id'],
                        'quantity': 1,
                    }
                ],
                mode='subscription',
                customer=customer_id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'workspace_slug': workspace.slug,
                    'workspace_id': str(workspace.id),
                    'user_id': str(user.id),
                    'pack_type': pack_type,
                    'is_upgrade': 'true',  # Mark this as an upgrade
                },
                subscription_data={
                    'metadata': {
                        'workspace_slug': workspace.slug,
                        'workspace_id': str(workspace.id),
                        'pack_type': pack_type,
                        'is_upgrade': 'true',
                    }
                }
            )
            
            return {
                'id': checkout_session.id,
                'url': checkout_session.url,
                'pack_type': pack_type,
                'pack_config': pack_config
            }
            
        except Exception as e:
            logger.error(f"Error creating AI Pack checkout session for upgrade: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    def cancel_ai_pack_subscription(self, workspace_slug: str) -> Dict[str, Any]:
        """
        Cancel AI Pack subscription immediately

        Args:
            workspace_slug: Workspace slug

        Returns:
            Dictionary containing cancellation result
        """
        try:
            subscription_data = self.get_workspace_ai_pack_subscription(workspace_slug)

            if not subscription_data['active']:
                raise ValueError("No active AI Pack subscription found")

            subscription_id = subscription_data['subscription']['id']

            # Cancel subscription immediately
            subscription = stripe.Subscription.delete(subscription_id)

            # Get subscription details safely since deleted subscriptions may not have all attributes
            current_period_end = getattr(subscription, 'current_period_end', None)
            canceled_at = getattr(subscription, 'canceled_at', None)
            status = getattr(subscription, 'status', 'canceled')

            return {
                'success': True,
                'subscription_id': subscription_id,
                'status': status,
                'cancel_at_period_end': False,  # Immediate cancellation
                'canceled_at': canceled_at,
                'current_period_end': current_period_end
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling AI Pack subscription for workspace {workspace_slug}: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error cancelling AI Pack subscription for workspace {workspace_slug}: {str(e)}")
            logger.exception("Full traceback:")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    def restart_ai_pack_subscription(self, workspace_slug: str) -> Dict[str, Any]:
        """
        Restart AI Pack subscription (remove cancellation)
        
        Args:
            workspace_slug: Workspace slug
            
        Returns:
            Dictionary containing restart result
        """
        try:
            subscription_data = self.get_workspace_ai_pack_subscription(workspace_slug)
            
            if not subscription_data['active']:
                raise ValueError("No active AI Pack subscription found")
            
            subscription_id = subscription_data['subscription']['id']
            
            # Remove cancellation
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            
            logger.info(f"Restarted AI Pack subscription {subscription_id} for workspace {workspace_slug}")
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'current_period_end': subscription.current_period_end
            }
            
        except Exception as e:
            logger.error(f"Error restarting AI Pack subscription for workspace {workspace_slug}: {str(e)}")
            raise Exception(f"Failed to restart subscription: {str(e)}")
    
    def upgrade_ai_pack_subscription(
        self,
        workspace: Workspace,
        user: User,
        new_pack_type: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Upgrade AI Pack subscription to a different pack

        Args:
            workspace: The workspace object
            user: The user initiating the upgrade
            new_pack_type: New pack type to upgrade to
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled

        Returns:
            Dictionary containing upgrade result
        """
        try:
            logger.debug(
                f"Starting upgrade_ai_pack_subscription for workspace={workspace.slug}, "
                f"user={getattr(user, 'id', user)}, new_pack_type={new_pack_type}, "
                f"success_url={success_url}, cancel_url={cancel_url}"
            )

            if new_pack_type not in self.AI_PACKS:
                logger.debug(f"Invalid pack type provided: {new_pack_type}")
                raise ValueError(f"Invalid pack type: {new_pack_type}")

            logger.debug("Fetching current subscription for workspace %s", workspace.slug)
            current_subscription = self.get_workspace_ai_pack_subscription(workspace.slug)
            logger.debug(f"Current subscription data: {current_subscription}")

            if not current_subscription['active']:
                logger.debug(
                    f"No active subscription found for workspace {workspace.slug}. "
                    f"Creating new checkout session for pack {new_pack_type}."
                )
                result = self.create_ai_pack_checkout_session(
                    workspace, user, new_pack_type, success_url, cancel_url
                )
                logger.debug(f"Created checkout session result: {result}")
                return result

            current_pack_type = current_subscription['pack_type']
            logger.debug(
                f"Current pack type for workspace {workspace.slug}: {current_pack_type}"
            )
            if current_pack_type == new_pack_type:
                logger.debug(
                    f"Workspace {workspace.slug} is already subscribed to {new_pack_type}."
                )
                raise ValueError(f"Already subscribed to {new_pack_type}")

            logger.debug(
                f"Upgrading workspace {workspace.slug} from {current_pack_type} to {new_pack_type}. "
                f"Cancelling old subscription and creating new checkout session."
            )
            
            # Cancel the existing subscription first
            logger.debug(f"Cancelling existing subscription for workspace {workspace.slug}")
            cancel_result = self.cancel_ai_pack_subscription(workspace.slug)
            logger.debug(f"Cancel result: {cancel_result}")
            
            # Create a new checkout session for the new pack type
            logger.debug(f"Creating new checkout session for pack {new_pack_type}")
            result = self.create_ai_pack_checkout_session_for_upgrade(
                workspace, user, new_pack_type, success_url, cancel_url
            )
            logger.debug(f"Created checkout session result: {result}")
            
            # Add upgrade information to the result
            result.update({
                'is_upgrade': True,
                'old_pack_type': current_pack_type,
                'new_pack_type': new_pack_type,
                'cancelled_subscription_id': cancel_result.get('subscription_id'),
            })
            
            logger.info(f"Successfully initiated AI Pack upgrade for workspace {workspace.slug} from {current_pack_type} to {new_pack_type}")
            return result

        except Exception as e:
            logger.error(f"Error upgrading AI Pack subscription: {traceback.format_exc()}")
            raise Exception(f"Failed to upgrade subscription: {str(e)}")
    
    def get_ai_pack_usage_limits(self, workspace_slug: str) -> Dict[str, Any]:
        """
        Get AI Pack usage limits for a workspace
        
        Args:
            workspace_slug: Workspace slug
            
        Returns:
            Dictionary containing usage limits
        """
        try:
            subscription_data = self.get_workspace_ai_pack_subscription(workspace_slug)
            
            if not subscription_data['active']:
                return {
                    'has_subscription': False,
                    'general_runs_limit': 0,
                    'code_runs_limit': 0,
                    'pack_type': None
                }
            
            pack_config = subscription_data['pack_config']
            
            return {
                'has_subscription': True,
                'general_runs_limit': pack_config['general_runs'],
                'code_runs_limit': pack_config['code_runs'],
                'pack_type': subscription_data['pack_type'],
                'pack_name': pack_config['name']
            }
            
        except Exception as e:
            logger.error(f"Error getting AI Pack usage limits for workspace {workspace_slug}: {str(e)}")
            return {
                'has_subscription': False,
                'general_runs_limit': 0,
                'code_runs_limit': 0,
                'pack_type': None
            }
