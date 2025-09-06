"""
Stripe service for handling payment processing and subscription management
"""

import stripe
import traceback
import logging
from django.conf import settings
from typing import Dict, Any, Optional
from plane.db.models import Workspace, User
from plane.api.serializers import StripeCheckoutSessionSerializer

logger = logging.getLogger(__name__)


class StripeService:
    """Service class for handling Stripe operations"""
    
    def __init__(self):
        # Validate Stripe configuration
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY is not configured. Please set the STRIPE_SECRET_KEY environment variable.")
        
        if not settings.STRIPE_SECRET_KEY.startswith(('sk_test_', 'sk_live_')):
            raise ValueError("Invalid STRIPE_SECRET_KEY format. Must start with 'sk_test_' or 'sk_live_'.")
        
        # Initialize Stripe with API key
        stripe.api_key = settings.STRIPE_SECRET_KEY
        logger.info("Stripe service initialized successfully")
    
    def test_connection(self) -> bool:
        """
        Test the Stripe connection
        
        Returns:
            Boolean indicating if connection is successful
        """
        try:
            stripe.Account.retrieve()
            logger.info("Stripe connection test successful")
            return True
        except stripe.error.AuthenticationError:
            logger.error("Stripe authentication failed")
            return False
        except Exception as e:
            logger.error(f"Stripe connection test failed: {str(e)}")
            return False
    
    def create_checkout_session(
        self, 
        workspace: Workspace, 
        user: User, 
        price_id: str, 
        success_url: str, 
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for subscription
        
        Args:
            workspace: The workspace object
            user: The user initiating the checkout
            price_id: Stripe price ID for the subscription
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            
        Returns:
            Dictionary containing checkout session data
        """
        try:
            # Validate inputs
            if not price_id or not price_id.strip():
                raise ValueError("Price ID is required")
            
            if not success_url or not success_url.strip():
                raise ValueError("Success URL is required")
                
            if not cancel_url or not cancel_url.strip():
                raise ValueError("Cancel URL is required")
            
            logger.info(f"Creating checkout session for workspace {workspace.slug}, user {user.id}, price {price_id}")
            
            # Check if workspace already has an active subscription
            existing_subscription = None
            try:
                subscription_data = self.get_subscription_status(workspace.slug)
                if subscription_data.get('id') and subscription_data.get('status') == 'active':
                    existing_subscription = subscription_data['id']
                    logger.info(f"Found existing subscription {existing_subscription} for workspace {workspace.slug}")
            except Exception as e:
                logger.info(f"No existing subscription found for workspace {workspace.slug}: {str(e)}")
            
            # Create checkout session according to Stripe documentation
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    }
                ],
                mode='subscription',
                success_url=f"{success_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                client_reference_id=str(workspace.id),
                customer_email=user.email if user.email else None,
                metadata={
                    'workspace_id': str(workspace.id),
                    'user_id': str(user.id),
                    'workspace_slug': workspace.slug,
                    'price_id': price_id,
                    'existing_subscription_id': existing_subscription or '',
                },
                subscription_data={
                    'metadata': {
                        'workspace_id': str(workspace.id),
                        'workspace_slug': workspace.slug,
                        'user_id': str(user.id),
                        'price_id': price_id,
                        'existing_subscription_id': existing_subscription or '',
                    }
                },
                # Add billing address collection for better customer data
                billing_address_collection='required',
                # Allow promotion codes
                allow_promotion_codes=True,
            )
            
            logger.info(f"Checkout session created successfully: {checkout_session.id}")
            
            return {
                'id': checkout_session.id,
                'url': checkout_session.url,
                'status': checkout_session.status,
                'payment_status': checkout_session.payment_status,
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe request: {str(e)}")
            raise ValueError(f"Invalid request to Stripe: {str(e)}")
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe authentication error: {str(e)}")
            raise ValueError("Stripe authentication failed. Please check your API key.")
        except stripe.error.APIConnectionError as e:
            logger.error(f"Stripe API connection error: {str(e)}")
            raise Exception("Unable to connect to Stripe. Please try again later.")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating checkout session: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    def handle_checkout_completion(self, session_id: str) -> Dict[str, Any]:
        """
        Handle checkout session completion and cancel old subscription if needed
        
        Args:
            session_id: Stripe checkout session ID
            
        Returns:
            Dictionary containing completion results
        """
        try:
            # Retrieve the checkout session
            session = stripe.checkout.Session.retrieve(session_id)
            
            if not session.subscription:
                logger.warning(f"No subscription found in checkout session {session_id}")
                return {'success': False, 'error': 'No subscription found'}
            
            new_subscription_id = session.subscription
            metadata = session.metadata or {}
            existing_subscription_id = metadata.get('existing_subscription_id')
            
            logger.info(f"Checkout completed. New subscription: {new_subscription_id}, Old subscription: {existing_subscription_id}")
            
            # Cancel old subscription if it exists
            if existing_subscription_id and existing_subscription_id.strip():
                try:
                    logger.info(f"Cancelling old subscription: {existing_subscription_id}")
                    self.cancel_subscription(existing_subscription_id)
                    logger.info(f"Successfully cancelled old subscription: {existing_subscription_id}")
                except Exception as e:
                    logger.error(f"Failed to cancel old subscription {existing_subscription_id}: {str(e)}")
                    # Don't fail the whole process if old subscription cancellation fails
            
            # Get the new subscription details
            subscription = stripe.Subscription.retrieve(new_subscription_id)
            
            # Update workspace with new subscription
            workspace_id = metadata.get('workspace_id')
            if workspace_id:
                try:
                    from plane.db.models import Workspace
                    workspace = Workspace.objects.get(id=workspace_id)
                    
                    # Update workspace subscription data
                    self.update_workspace_subscription(workspace, {
                        'subscription': {
                            'id': subscription.id,
                            'status': subscription.status,
                            'current_period_start': subscription.current_period_start,
                            'current_period_end': subscription.current_period_end,
                            'cancel_at_period_end': subscription.cancel_at_period_end,
                            'customer': subscription.customer,
                            'created': subscription.created,
                            'price_id': subscription.items.data[0].price.id if subscription.items.data else None,
                            'product_id': subscription.items.data[0].price.product if subscription.items.data else None,
                        },
                        'has_active_subscription': True
                    })
                    
                    logger.info(f"Updated workspace {workspace.slug} with new subscription {subscription.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to update workspace {workspace_id}: {str(e)}")
            
            return {
                'success': True,
                'subscription_id': new_subscription_id,
                'cancelled_old': bool(existing_subscription_id and existing_subscription_id.strip())
            }
            
        except Exception as e:
            logger.error(f"Error handling checkout completion for session {session_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Retrieve subscription details from Stripe
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Dictionary containing subscription data
        """
        try:
            if not subscription_id or not subscription_id.strip():
                raise ValueError("Subscription ID is required")
            
            logger.info(f"Retrieving subscription: {subscription_id}")
            
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'customer': subscription.customer,
                'created': subscription.created,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe request for subscription {subscription_id}: {str(e)}")
            raise ValueError(f"Invalid subscription ID: {str(e)}")
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe authentication error: {str(e)}")
            raise ValueError("Stripe authentication failed. Please check your API key.")
        except stripe.error.APIConnectionError as e:
            logger.error(f"Stripe API connection error: {str(e)}")
            raise Exception("Unable to connect to Stripe. Please try again later.")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving subscription {subscription_id}: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving subscription {subscription_id}: {str(e)}")
            raise Exception(f"Failed to retrieve subscription: {str(e)}")
    
    def get_subscription_status(self, workspace_slug: str) -> Dict[str, Any]:
        """
        Get subscription status for a workspace
        
        Args:
            workspace_slug: Workspace slug
            
        Returns:
            Dictionary containing subscription status data
        """
        try:
            from plane.db.models import Workspace
            
            workspace = Workspace.objects.get(slug=workspace_slug)
            
            if not workspace.stripe_customer_id:
                return {}
            
            # Get customer subscriptions
            subscriptions = self.get_customer_subscriptions(workspace.stripe_customer_id)
            
            # Find active subscription
            if subscriptions.get('has_active_subscription') and subscriptions.get('subscription'):
                return subscriptions['subscription']
            
            return {}
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {workspace_slug}")
            return {}
        except Exception as e:
            logger.error(f"Error getting subscription status for workspace {workspace_slug}: {str(e)}")
            return {}
    
    def sync_workspace_with_stripe(self, workspace_slug: str) -> Dict[str, Any]:
        """
        Sync workspace with Stripe data by finding the customer and subscription
        
        Args:
            workspace_slug: Workspace slug
            
        Returns:
            Dictionary containing sync results
        """
        try:
            from plane.db.models import Workspace
            
            workspace = Workspace.objects.get(slug=workspace_slug)
            
            # If workspace already has customer ID, use it
            if workspace.stripe_customer_id:
                logger.info(f"Workspace already has customer ID: {workspace.stripe_customer_id}")
                return self.get_customer_subscriptions(workspace.stripe_customer_id)
            
            # Search for customer by email or workspace name
            # First, try to find customer by workspace owner's email
            workspace_owner = workspace.owner
            if workspace_owner and workspace_owner.email:
                try:
                    customers = stripe.Customer.list(
                        email=workspace_owner.email,
                        limit=10
                    )
                    
                    for customer in customers.data:
                        # Check if this customer has active subscriptions
                        subscriptions = stripe.Subscription.list(
                            customer=customer.id,
                            status='active',
                            limit=1
                        )
                        
                        if subscriptions.data:
                            # Found a customer with active subscription
                            logger.info(f"Found customer {customer.id} with active subscription for workspace {workspace_slug}")
                            
                            # Update workspace with customer ID
                            workspace.stripe_customer_id = customer.id
                            workspace.save()
                            
                            # Get subscription data
                            subscription_data = self.get_customer_subscriptions(customer.id)
                            
                            # Update workspace with subscription data
                            self.update_workspace_subscription(workspace, subscription_data)
                            
                            return subscription_data
                            
                except Exception as e:
                    logger.warning(f"Error searching for customer by email: {str(e)}")
            
            # If no customer found by email, try to find by workspace metadata
            # This is a fallback - in practice, customers should be found by email
            logger.warning(f"No Stripe customer found for workspace {workspace_slug}")
            return {}
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {workspace_slug}")
            return {}
        except Exception as e:
            logger.error(f"Error syncing workspace {workspace_slug} with Stripe: {str(e)}")
            return {}
    
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Dictionary containing cancellation data
        """
        try:
            if not subscription_id or not subscription_id.strip():
                raise ValueError("Subscription ID is required")
            
            logger.info(f"Cancelling subscription: {subscription_id}")
            
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            
            logger.info(f"Subscription {subscription_id} cancelled successfully")
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'canceled_at': subscription.canceled_at,
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe request for subscription {subscription_id}: {str(e)}")
            raise ValueError(f"Invalid subscription ID: {str(e)}")
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe authentication error: {str(e)}")
            raise ValueError("Stripe authentication failed. Please check your API key.")
        except stripe.error.APIConnectionError as e:
            logger.error(f"Stripe API connection error: {str(e)}")
            raise Exception("Unable to connect to Stripe. Please try again later.")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription {subscription_id}: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error cancelling subscription {subscription_id}: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    def restart_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Restart a cancelled subscription
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Dictionary containing restart data
        """
        try:
            if not subscription_id or not subscription_id.strip():
                raise ValueError("Subscription ID is required")
            
            logger.info(f"Restarting subscription: {subscription_id}")
            
            # Get current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Check if subscription is cancelled
            if not subscription.cancel_at_period_end:
                raise ValueError("Subscription is not cancelled")
            
            # Restart subscription by removing cancel_at_period_end
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            
            logger.info(f"Subscription {subscription_id} restarted successfully")
            
            # Retrieve the updated subscription to get all fields properly
            refreshed_subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                'id': refreshed_subscription.id,
                'status': refreshed_subscription.status,
                'current_period_start': getattr(refreshed_subscription, 'current_period_start', None),
                'current_period_end': getattr(refreshed_subscription, 'current_period_end', None),
                'cancel_at_period_end': refreshed_subscription.cancel_at_period_end,
                'customer': refreshed_subscription.customer,
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe request for subscription {subscription_id}: {str(e)}")
            raise ValueError(f"Invalid subscription ID: {str(e)}")
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe authentication error: {str(e)}")
            raise ValueError("Stripe authentication failed. Please check your API key.")
        except stripe.error.APIConnectionError as e:
            logger.error(f"Stripe API connection error: {str(e)}")
            raise Exception("Unable to connect to Stripe. Please try again later.")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error restarting subscription {subscription_id}: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error restarting subscription {subscription_id}: {str(e)}")
            raise Exception(f"Failed to restart subscription: {str(e)}")
    
    def update_subscription(self, subscription_id: str, new_price_id: str) -> Dict[str, Any]:
        """
        Update subscription to a new price
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe price ID
            
        Returns:
            Dictionary containing updated subscription data
        """
        try:
            if not subscription_id or not subscription_id.strip():
                raise ValueError("Subscription ID is required")
            
            if not new_price_id or not new_price_id.strip():
                raise ValueError("New price ID is required")
            
            logger.info(f"Updating subscription {subscription_id} to price {new_price_id}")
            
            # Get current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update subscription with new price
            stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0]['id'],
                    'price': new_price_id,
                }],
                proration_behavior='create_prorations'
            )
            
            logger.info(f"Subscription {subscription_id} updated successfully")
            
            # Retrieve the updated subscription to get all fields
            refreshed_subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                'id': refreshed_subscription.id,
                'status': refreshed_subscription.status,
                'current_period_start': getattr(refreshed_subscription, 'current_period_start', None),
                'current_period_end': getattr(refreshed_subscription, 'current_period_end', None),
                'cancel_at_period_end': getattr(refreshed_subscription, 'cancel_at_period_end', False),
                'customer': refreshed_subscription.customer,
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe request for subscription {subscription_id}: {str(e)}")
            raise ValueError(f"Invalid subscription or price ID: {str(e)}")
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe authentication error: {str(e)}")
            raise ValueError("Stripe authentication failed. Please check your API key.")
        except stripe.error.APIConnectionError as e:
            logger.error(f"Stripe API connection error: {str(e)}")
            raise Exception("Unable to connect to Stripe. Please try again later.")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription {subscription_id}: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error updating subscription {subscription_id}: {str(e)}")
            raise Exception(f"Failed to update subscription: {str(e)}")
    
    def get_customer_subscriptions(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer's active subscriptions
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Dictionary containing subscription data
        """
        try:
            if not customer_id or not customer_id.strip():
                raise ValueError("Customer ID is required")
            
            logger.info(f"Retrieving subscriptions for customer {customer_id}")
            
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='active',
                limit=1
            )
            
            if not subscriptions.data:
                return {
                    'subscription': None,
                    'has_active_subscription': False
                }
            
            subscription = subscriptions.data[0]
            
            # Get subscription details from items
            items = subscription.get('items', {}).get('data', [])
            if items:
                item = items[0]
                current_period_start = item.get('current_period_start', subscription.get('start_date'))
                current_period_end = item.get('current_period_end')
                price_id = item.get('price', {}).get('id', subscription.get('plan', {}).get('id'))
                product_id = item.get('price', {}).get('product', subscription.get('plan', {}).get('product'))
            else:
                current_period_start = subscription.get('start_date')
                current_period_end = None
                price_id = subscription.get('plan', {}).get('id')
                product_id = subscription.get('plan', {}).get('product')

            return {
                'subscription': {
                    'id': subscription.id,
                    'status': subscription.status,
                    'current_period_start': current_period_start,
                    'current_period_end': current_period_end,
                    'cancel_at_period_end': subscription.cancel_at_period_end,
                    'customer': subscription.customer,
                    'created': subscription.created,
                    'price_id': price_id,
                    'product_id': product_id,
                },
                'has_active_subscription': True
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe request for customer {customer_id}: {str(e)}")
            raise ValueError(f"Invalid customer ID: {str(e)}")
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe authentication error: {str(e)}")
            raise ValueError("Stripe authentication failed. Please check your API key.")
        except stripe.error.APIConnectionError as e:
            logger.error(f"Stripe API connection error: {str(e)}")
            raise Exception("Unable to connect to Stripe. Please try again later.")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving subscriptions for customer {customer_id}: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving subscriptions for customer {customer_id}: {str(e)}")
            raise Exception(f"Failed to retrieve subscriptions: {str(e)}")

    def get_customer_invoices(self, customer_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get customer invoices
        
        Args:
            customer_id: Stripe customer ID
            limit: Number of invoices to retrieve
            
        Returns:
            Dictionary containing invoices data
        """
        try:
            if not customer_id or not customer_id.strip():
                raise ValueError("Customer ID is required")
            
            logger.info(f"Retrieving invoices for customer {customer_id}")
            
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit,
                expand=['data.subscription']
            )
            
            return {
                'invoices': [
                    {
                        'id': invoice.id,
                        'number': invoice.number,
                        'status': invoice.status,
                        'amount_paid': invoice.amount_paid,
                        'amount_due': invoice.amount_due,
                        'currency': invoice.currency,
                        'created': invoice.created,
                        'due_date': invoice.due_date,
                        'invoice_pdf': invoice.invoice_pdf,
                        'hosted_invoice_url': invoice.hosted_invoice_url,
                        'description': invoice.description,
                    }
                    for invoice in invoices.data
                ],
                'has_more': invoices.has_more,
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe request for customer {customer_id}: {str(e)}")
            raise ValueError(f"Invalid customer ID: {str(e)}")
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe authentication error: {str(e)}")
            raise ValueError("Stripe authentication failed. Please check your API key.")
        except stripe.error.APIConnectionError as e:
            logger.error(f"Stripe API connection error: {str(e)}")
            raise Exception("Unable to connect to Stripe. Please try again later.")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving invoices for customer {customer_id}: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving invoices for customer {customer_id}: {str(e)}")
            raise Exception(f"Failed to retrieve invoices: {str(e)}")

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
            
        Returns:
            Boolean indicating if signature is valid
        """
        try:
            if not settings.STRIPE_WEBHOOK_SECRET:
                logger.error("STRIPE_WEBHOOK_SECRET is not configured")
                return False
            
            if not signature:
                logger.error("No signature provided for webhook verification")
                return False
            
            stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            logger.info("Webhook signature verified successfully")
            return True
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error verifying webhook signature: {str(e)}")
            return False
    
    def update_workspace_subscription(self, workspace, subscription_data: Dict[str, Any]) -> None:
        """
        Update workspace with subscription data
        
        Args:
            workspace: Workspace instance
            subscription_data: Subscription data from Stripe
        """
        try:
            from django.utils import timezone
            
            if subscription_data and subscription_data.get('subscription'):
                sub = subscription_data['subscription']
                workspace.stripe_customer_id = sub.get('customer')
                workspace.stripe_subscription_id = sub.get('id')
                workspace.subscription_status = sub.get('status', 'free')
                workspace.subscription_price_id = sub.get('price_id')
                workspace.subscription_current_period_start = timezone.datetime.fromtimestamp(
                    sub.get('current_period_start', 0), tz=timezone.utc
                ) if sub.get('current_period_start') else None
                workspace.subscription_current_period_end = timezone.datetime.fromtimestamp(
                    sub.get('current_period_end', 0), tz=timezone.utc
                ) if sub.get('current_period_end') else None
                workspace.subscription_cancel_at_period_end = sub.get('cancel_at_period_end', False)
            else:
                # No active subscription
                workspace.stripe_customer_id = None
                workspace.stripe_subscription_id = None
                workspace.subscription_status = 'free'
                workspace.subscription_price_id = None
                workspace.subscription_current_period_start = None
                workspace.subscription_current_period_end = None
                workspace.subscription_cancel_at_period_end = False
            
            workspace.save()
            logger.info(f"Updated workspace {workspace.slug} subscription data")
            
        except Exception as e:
            logger.error(f"Error updating workspace subscription: {str(e)}")
            raise Exception(f"Failed to update workspace subscription: {str(e)}")
    
    def update_subscription_quantity(self, workspace_slug: str, quantity_change: int) -> Dict[str, Any]:
        """
        Update Stripe subscription quantity when users are added/removed
        
        Args:
            workspace_slug: Workspace slug
            quantity_change: Change in quantity (+1 for add, -1 for remove)
            
        Returns:
            Dictionary containing update results
        """
        try:
            from plane.db.models import Workspace
            
            workspace = Workspace.objects.get(slug=workspace_slug)
            
            if not workspace.stripe_subscription_id:
                logger.warning(f"No active subscription found for workspace {workspace_slug}")
                return {'success': False, 'error': 'No active subscription'}
            
            # Get current subscription
            subscription = stripe.Subscription.retrieve(workspace.stripe_subscription_id)
            
            if not subscription['items']['data']:
                logger.error(f"No subscription items found for subscription {workspace.stripe_subscription_id}")
                return {'success': False, 'error': 'No subscription items found'}
            
            # Get current quantity
            current_quantity = subscription['items']['data'][0]['quantity']
            new_quantity = max(1, current_quantity + quantity_change)  # Ensure minimum quantity of 1
            
            if new_quantity == current_quantity:
                logger.info(f"Quantity unchanged for workspace {workspace_slug}: {current_quantity}")
                return {'success': True, 'quantity': current_quantity, 'message': 'Quantity unchanged'}
            
            # Update subscription quantity
            stripe.Subscription.modify(
                workspace.stripe_subscription_id,
                items=[{
                    'id': subscription['items']['data'][0]['id'],
                    'quantity': new_quantity,
                }],
                proration_behavior='create_prorations'
            )
            
            logger.info(f"Updated subscription quantity for workspace {workspace_slug}: {current_quantity} -> {new_quantity}")
            
            return {
                'success': True,
                'old_quantity': current_quantity,
                'new_quantity': new_quantity,
                'change': quantity_change
            }
            
        except Workspace.DoesNotExist:
            logger.error(f"Workspace not found: {workspace_slug}")
            return {'success': False, 'error': 'Workspace not found'}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription quantity for workspace {workspace_slug}: {str(e)}")
            return {'success': False, 'error': f'Stripe error: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error updating subscription quantity for workspace {workspace_slug}: {str(e)}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def can_manage_users(self, workspace_slug: str) -> bool:
        """
        Check if workspace can manage users based on subscription plan
        
        Args:
            workspace_slug: Workspace slug
            
        Returns:
            Boolean indicating if workspace can manage users
        """
        try:
            from plane.db.models import Workspace
            
            workspace = Workspace.objects.get(slug=workspace_slug)
            
            # Check if workspace has an active subscription
            if not workspace.stripe_subscription_id:
                return False
            
            # Get subscription status
            subscription_data = self.get_subscription_status(workspace_slug)
            
            if not subscription_data or subscription_data.get('status') != 'active':
                return False
            
            # Check if it's a paid plan (not free)
            price_id = subscription_data.get('price_id', '')
            if not price_id or 'free' in price_id.lower():
                return False
            
            return True
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {workspace_slug}")
            return False
        except Exception as e:
            logger.error(f"Error checking user management capability for workspace {workspace_slug}: {str(e)}")
            return False
    
    def get_subscription_plan_type(self, workspace_slug: str) -> str:
        """
        Get the current subscription plan type for a workspace
        
        Args:
            workspace_slug: Workspace slug
            
        Returns:
            String indicating plan type ('free', 'starter', 'pro', 'enterprise')
        """
        try:
            from plane.db.models import Workspace
            
            workspace = Workspace.objects.get(slug=workspace_slug)
            
            if not workspace.stripe_subscription_id:
                return 'free'
            
            subscription_data = self.get_subscription_status(workspace_slug)
            
            if not subscription_data or subscription_data.get('status') != 'active':
                return 'free'
            
            # Determine plan type based on price_id or product_id
            price_id = subscription_data.get('price_id', '')
            product_id = subscription_data.get('product_id', '')
            
            # This is a simplified mapping - you may need to adjust based on your actual Stripe price IDs
            if 'starter' in price_id.lower() or 'starter' in product_id.lower():
                return 'starter'
            elif 'pro' in price_id.lower() or 'pro' in product_id.lower():
                return 'pro'
            elif 'enterprise' in price_id.lower() or 'enterprise' in product_id.lower():
                return 'enterprise'
            else:
                return 'paid'  # Generic paid plan
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {workspace_slug}")
            return 'free'
        except Exception as e:
            logger.error(f"Error getting subscription plan type for workspace {workspace_slug}: {str(e)}")
            return 'free'
    
    def get_workspace_user_count(self, workspace_slug: str) -> int:
        """
        Get current active user count for a workspace
        
        Args:
            workspace_slug: Workspace slug
            
        Returns:
            Number of active users in the workspace
        """
        try:
            from plane.db.models import Workspace, WorkspaceMember
            
            workspace = Workspace.objects.get(slug=workspace_slug)
            
            # Count active workspace members (excluding bots)
            user_count = WorkspaceMember.objects.filter(
                workspace=workspace,
                is_active=True,
                member__is_bot=False
            ).count()
            
            return user_count
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {workspace_slug}")
            return 0
        except Exception as e:
            logger.error(f"Error getting user count for workspace {workspace_slug}: {str(e)}")
            return 0