"""
Stripe API views for payment processing and subscription management
"""

import json
import logging
import traceback
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from .base import BaseAPIView
from plane.app.permissions import WorkspaceEntityPermission
from plane.authentication.session import BaseSessionAuthentication
from plane.db.models import Workspace, WorkspaceMember
from plane.api.services.stripe_service import StripeService
from plane.api.serializers.stripe import (
    StripeCheckoutSessionSerializer,
    StripeWebhookSerializer,
    SubscriptionSerializer
)

logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StripeCheckoutView(BaseAPIView):
    """API view for creating Stripe checkout sessions"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def options(self, request, slug):
        """Handle preflight CORS requests"""
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken, X-Requested-With'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'
        return response
    
    def post(self, request, slug):
        """
        Create a Stripe checkout session for subscription
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with checkout session data
        """
        try:
            workspace = Workspace.objects.get(slug=slug)            
            # Check if user has admin permissions
            if not WorkspaceMember.objects.filter(
                workspace=workspace,
                member=request.user,
                role__in=[20, 15]  # Admin or Owner roles
            ).exists():
                return Response(
                    {"error": "Insufficient permissions"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = StripeCheckoutSessionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                stripe_service = StripeService()
            except Exception as e:
                logger.error(f"Stripe service initialization failed: {str(e)}")
                return Response(
                    {"error": "Payment service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Use provided URLs or defaults
            success_url = serializer.validated_data.get('success_url') or settings.STRIPE_SUCCESS_URL
            cancel_url = serializer.validated_data.get('cancel_url') or settings.STRIPE_CANCEL_URL
            
            # Replace placeholders in URLs
            success_url = success_url.replace('{workspace_slug}', slug)
            cancel_url = cancel_url.replace('{workspace_slug}', slug)
            
            checkout_data = stripe_service.create_checkout_session(
                workspace=workspace,
                user=request.user,
                price_id=serializer.validated_data['price_id'],
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            return Response(checkout_data, status=status.HTTP_201_CREATED)
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {slug}")
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            logger.warning(f"Permission denied for user {request.user.id} on workspace {slug}: {str(e)}")
            return Response(
                {"error": "Insufficient permissions to create checkout session"},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            # logger.error(f"Error creating checkout session: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {"error": "Failed to create checkout session"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StripeSubscriptionView(BaseAPIView):
    """API view for managing Stripe subscriptions"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def options(self, request, slug, subscription_id):
        """Handle preflight CORS requests"""
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'GET, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken, X-Requested-With'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'
        return response
    
    def get(self, request, slug, subscription_id):
        """
        Get subscription details
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            subscription_id: Stripe subscription ID
            
        Returns:
            Response with subscription data
        """
        try:
            workspace = Workspace.objects.get(slug=slug)
            
            # Check if user has admin permissions
            if not WorkspaceMember.objects.filter(
                workspace=workspace,
                member=request.user,
                role__in=[20, 15]  # Admin or Owner roles
            ).exists():
                return Response(
                    {"error": "Insufficient permissions"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                stripe_service = StripeService()
            except Exception as e:
                logger.error(f"Stripe service initialization failed: {str(e)}")
                return Response(
                    {"error": "Payment service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            subscription_data = stripe_service.get_subscription(subscription_id)
            
            return Response(subscription_data, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {slug}")
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            logger.warning(f"Permission denied for user {request.user.id} on workspace {slug}: {str(e)}")
            return Response(
                {"error": "Insufficient permissions to view subscription"},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            return Response(
                {"error": "Failed to retrieve subscription"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, slug, subscription_id):
        """
        Cancel subscription
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            subscription_id: Stripe subscription ID
            
        Returns:
            Response with cancellation data
        """
        try:
            workspace = Workspace.objects.get(slug=slug)
            
            # Check if user has admin permissions
            if not WorkspaceMember.objects.filter(
                workspace=workspace,
                member=request.user,
                role__in=[20, 15]  # Admin or Owner roles
            ).exists():
                return Response(
                    {"error": "Insufficient permissions"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                stripe_service = StripeService()
            except Exception as e:
                logger.error(f"Stripe service initialization failed: {str(e)}")
                return Response(
                    {"error": "Payment service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            cancellation_data = stripe_service.cancel_subscription(subscription_id)
            
            return Response(cancellation_data, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {slug}")
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            logger.warning(f"Permission denied for user {request.user.id} on workspace {slug}: {str(e)}")
            return Response(
                {"error": "Insufficient permissions to cancel subscription"},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            return Response(
                {"error": "Failed to cancel subscription"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(BaseAPIView):
    """API view for handling Stripe webhooks"""
    
    permission_classes = []  # No authentication required for webhooks
    
    def options(self, request, *args, **kwargs):
        """Handle preflight CORS requests for webhook endpoint"""
        from django.http import HttpResponse
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Stripe-Signature'
        response['Access-Control-Max-Age'] = '86400'
        return response
    
    def post(self, request):
        """
        Handle Stripe webhook events
        
        Args:
            request: HTTP request object with Stripe webhook payload
            
        Returns:
            HTTP response
        """
        try:
            payload = request.body
            signature = request.META.get('HTTP_STRIPE_SIGNATURE')
            
            if not signature:
                logger.error("Missing Stripe signature")
                return HttpResponse("Missing signature", status=400)
            
            stripe_service = StripeService()
            
            # Verify webhook signature
            if not stripe_service.verify_webhook_signature(payload, signature):
                logger.error("Invalid Stripe signature")
                return HttpResponse("Invalid signature", status=400)
            
            # Parse webhook event
            event = json.loads(payload)
            event_type = event.get('type')
            
            logger.info(f"Received Stripe webhook: {event_type}")
            logger.info(f"Event data: {json.dumps(event, indent=2)}")
            
            # Handle different event types
            if event_type == 'checkout.session.completed':
                self._handle_checkout_completed(event)
            elif event_type == 'customer.subscription.created':
                self._handle_subscription_created(event)
            elif event_type == 'customer.subscription.updated':
                self._handle_subscription_updated(event)
            elif event_type == 'customer.subscription.deleted':
                self._handle_subscription_deleted(event)
            elif event_type == 'invoice.payment_succeeded':
                self._handle_payment_succeeded(event)
            elif event_type == 'invoice.payment_failed':
                self._handle_payment_failed(event)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
            
            return HttpResponse("Webhook processed", status=200)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            return HttpResponse("Invalid JSON", status=400)
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return HttpResponse("Webhook processing failed", status=500)
    
    def _handle_checkout_completed(self, event):
        """Handle checkout.session.completed event"""
        session = event.get('data', {}).get('object', {})
        workspace_id = session.get('metadata', {}).get('workspace_id')
        ai_usage = session.get('metadata', {}).get('ai_usage')
        
        if workspace_id:
            logger.info(f"Checkout completed for workspace: {workspace_id}")
            try:
                workspace = Workspace.objects.get(id=workspace_id)
                customer_id = session.get('customer')
                
                if customer_id:
                    # Always ensure workspace has customer ID
                    if not workspace.stripe_customer_id:
                        workspace.stripe_customer_id = customer_id
                        workspace.save()
                        logger.info(f"Updated workspace {workspace_id} with customer ID: {customer_id}")
                    
                    # Handle AI usage subscriptions separately
                    if ai_usage == 'true':
                        logger.info(f"AI usage checkout completed for workspace {workspace_id}")
                        # AI usage subscriptions are handled by the AI usage service
                        # No need to update main workspace subscription data
                    else:
                        # Fetch and update subscription data
                        stripe_service = StripeService()
                        subscription_data = stripe_service.get_customer_subscriptions(customer_id)
                        stripe_service.update_workspace_subscription(workspace, subscription_data)
                    
            except Workspace.DoesNotExist:
                logger.error(f"Workspace {workspace_id} not found for checkout completion")
            except Exception as e:
                logger.error(f"Error handling checkout completion: {str(e)}")
    
    def _handle_subscription_created(self, event):
        """Handle customer.subscription.created event"""
        subscription = event.get('data', {}).get('object', {})
        workspace_id = subscription.get('metadata', {}).get('workspace_id')
        existing_subscription_id = subscription.get('metadata', {}).get('existing_subscription_id')
        ai_usage = subscription.get('metadata', {}).get('ai_usage')
        
        if workspace_id:
            logger.info(f"Subscription created for workspace: {workspace_id}")
            try:
                workspace = Workspace.objects.get(id=workspace_id)
                customer_id = subscription.get('customer')
                
                if customer_id:
                    # Always ensure workspace has customer ID
                    if not workspace.stripe_customer_id:
                        workspace.stripe_customer_id = customer_id
                        workspace.save()
                        logger.info(f"Updated workspace {workspace_id} with customer ID: {customer_id}")
                    
                    # Handle AI usage subscriptions separately
                    if ai_usage == 'true':
                        logger.info(f"AI usage subscription created for workspace {workspace_id}")
                        # AI usage subscriptions are handled by the AI usage service
                        # No need to update main workspace subscription data
                    else:
                        # Cancel existing subscription if there is one
                        if existing_subscription_id and existing_subscription_id.strip():
                            try:
                                stripe_service = StripeService()
                                logger.info(f"Cancelling existing subscription: {existing_subscription_id}")
                                stripe_service.cancel_subscription(existing_subscription_id)
                                logger.info(f"Successfully cancelled existing subscription: {existing_subscription_id}")
                            except Exception as e:
                                logger.error(f"Error cancelling existing subscription {existing_subscription_id}: {str(e)}")
                        
                        # Update subscription data
                        stripe_service = StripeService()
                        subscription_data = {
                            'subscription': {
                                'id': subscription.get('id'),
                                'status': subscription.get('status'),
                                'current_period_start': subscription.get('current_period_start'),
                                'current_period_end': subscription.get('current_period_end'),
                                'cancel_at_period_end': subscription.get('cancel_at_period_end'),
                                'customer': customer_id,
                                'price_id': subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id'),
                                'product_id': subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('product'),
                            }
                        }
                        stripe_service.update_workspace_subscription(workspace, subscription_data)
                    
            except Workspace.DoesNotExist:
                logger.error(f"Workspace {workspace_id} not found for subscription creation")
            except Exception as e:
                logger.error(f"Error handling subscription creation: {str(e)}")
    
    def _handle_subscription_updated(self, event):
        """Handle customer.subscription.updated event"""
        subscription = event.get('data', {}).get('object', {})
        workspace_id = subscription.get('metadata', {}).get('workspace_id')
        
        if workspace_id:
            logger.info(f"Subscription updated for workspace: {workspace_id}")
            try:
                workspace = Workspace.objects.get(id=workspace_id)
                customer_id = subscription.get('customer')
                
                if customer_id:
                    # Update subscription data
                    stripe_service = StripeService()
                    subscription_data = {
                        'subscription': {
                            'id': subscription.get('id'),
                            'status': subscription.get('status'),
                            'current_period_start': subscription.get('current_period_start'),
                            'current_period_end': subscription.get('current_period_end'),
                            'cancel_at_period_end': subscription.get('cancel_at_period_end'),
                            'customer': customer_id,
                            'price_id': subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id'),
                            'product_id': subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('product'),
                        }
                    }
                    stripe_service.update_workspace_subscription(workspace, subscription_data)
                    
            except Workspace.DoesNotExist:
                logger.error(f"Workspace {workspace_id} not found for subscription update")
            except Exception as e:
                logger.error(f"Error handling subscription update: {str(e)}")
    
    def _handle_subscription_deleted(self, event):
        """Handle customer.subscription.deleted event"""
        subscription = event.get('data', {}).get('object', {})
        workspace_id = subscription.get('metadata', {}).get('workspace_id')
        
        if workspace_id:
            logger.info(f"Subscription deleted for workspace: {workspace_id}")
            try:
                workspace = Workspace.objects.get(id=workspace_id)
                
                # Clear subscription data
                stripe_service = StripeService()
                stripe_service.update_workspace_subscription(workspace, None)
                    
            except Workspace.DoesNotExist:
                logger.error(f"Workspace {workspace_id} not found for subscription deletion")
            except Exception as e:
                logger.error(f"Error handling subscription deletion: {str(e)}")
    
    def _handle_payment_succeeded(self, event):
        """Handle invoice.payment_succeeded event"""
        invoice = event.get('data', {}).get('object', {})
        subscription_id = invoice.get('subscription')
        
        if subscription_id:
            logger.info(f"Payment succeeded for subscription: {subscription_id}")
            # TODO: Update payment status
    
    def _handle_payment_failed(self, event):
        """Handle invoice.payment_failed event"""
        invoice = event.get('data', {}).get('object', {})
        subscription_id = invoice.get('subscription')
        
        if subscription_id:
            logger.info(f"Payment failed for subscription: {subscription_id}")
            # TODO: Handle payment failure


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StripeSubscriptionUpdateView(BaseAPIView):
    """API view for updating subscriptions"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def post(self, request, slug, subscription_id):
        """
        Update subscription to a new price
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            subscription_id: Stripe subscription ID
            
        Returns:
            Response with updated subscription data
        """
        try:
            workspace = Workspace.objects.get(slug=slug)
            
            # Check if user has admin permissions
            if not WorkspaceMember.objects.filter(
                workspace=workspace,
                member=request.user,
                role__in=[20, 15]  # Admin or Owner roles
            ).exists():
                return Response(
                    {"error": "Insufficient permissions"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            new_price_id = request.data.get('new_price_id')
            if not new_price_id:
                return Response(
                    {"error": "new_price_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                stripe_service = StripeService()
            except Exception as e:
                logger.error(f"Stripe service initialization failed: {str(e)}")
                return Response(
                    {"error": "Payment service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            updated_subscription = stripe_service.update_subscription(subscription_id, new_price_id)
            
            return Response(updated_subscription, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {slug}")
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            logger.warning(f"Permission denied for user {request.user.id} on workspace {slug}: {str(e)}")
            return Response(
                {"error": "Insufficient permissions to update subscription"},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            logger.warning(f"Invalid request data: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error updating subscription: {str(e)}")
            return Response(
                {"error": "Failed to update subscription"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StripeSubscriptionRestartView(BaseAPIView):
    """API view for restarting cancelled subscriptions"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def post(self, request, slug, subscription_id):
        """
        Restart a cancelled subscription
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            subscription_id: Stripe subscription ID
            
        Returns:
            Response with restart data
        """
        try:
            workspace = Workspace.objects.get(slug=slug)
            
            # Check if user has admin permissions
            if not WorkspaceMember.objects.filter(
                workspace=workspace,
                member=request.user,
                role__in=[20, 15]  # Admin or Owner roles
            ).exists():
                return Response(
                    {"error": "Insufficient permissions"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                stripe_service = StripeService()
            except Exception as e:
                logger.error(f"Stripe service initialization failed: {str(e)}")
                return Response(
                    {"error": "Payment service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            restart_data = stripe_service.restart_subscription(subscription_id)
            
            return Response(restart_data, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {slug}")
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            logger.warning(f"Permission denied for user {request.user.id} on workspace {slug}: {str(e)}")
            return Response(
                {"error": "Insufficient permissions to restart subscription"},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            logger.warning(f"Invalid request data: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error restarting subscription: {str(e)}")
            return Response(
                {"error": "Failed to restart subscription"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StripeInvoicesView(BaseAPIView):
    """API view for retrieving customer invoices"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def get(self, request, slug):
        """
        Get customer invoices
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with invoices data
        """
        try:
            workspace = Workspace.objects.get(slug=slug)
            
            # Check if user has admin permissions
            if not WorkspaceMember.objects.filter(
                workspace=workspace,
                member=request.user,
                role__in=[20, 15]  # Admin or Owner roles
            ).exists():
                return Response(
                    {"error": "Insufficient permissions"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            customer_id = request.query_params.get('customer_id')
            if not customer_id:
                return Response(
                    {"error": "customer_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            limit = int(request.query_params.get('limit', 10))
            
            try:
                stripe_service = StripeService()
            except Exception as e:
                logger.error(f"Stripe service initialization failed: {str(e)}")
                return Response(
                    {"error": "Payment service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            invoices_data = stripe_service.get_customer_invoices(customer_id, limit)
            
            return Response(invoices_data, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {slug}")
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            logger.warning(f"Permission denied for user {request.user.id} on workspace {slug}: {str(e)}")
            return Response(
                {"error": "Insufficient permissions to view invoices"},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            logger.warning(f"Invalid request data: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error retrieving invoices: {str(e)}")
            return Response(
                {"error": "Failed to retrieve invoices"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StripeCheckoutCompletionView(BaseAPIView):
    """API view for handling checkout completion"""
    
    authentication_classes = [BaseSessionAuthentication]
    
    def post(self, request):
        """
        Handle checkout session completion
        
        Args:
            request: HTTP request object with session_id
            
        Returns:
            Response with completion results
        """
        try:
            session_id = request.data.get('session_id')
            
            if not session_id:
                return Response(
                    {"error": "Session ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            stripe_service = StripeService()
            result = stripe_service.handle_checkout_completion(session_id)
            
            if result.get('success'):
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": result.get('error', 'Checkout completion failed')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error handling checkout completion: {str(e)}")
            return Response(
                {"error": "Failed to process checkout completion"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StripeSubscriptionStatusView(BaseAPIView):
    """API view for getting current subscription status"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def get(self, request, slug):
        """
        Get current subscription status for workspace
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with subscription data
        """
        try:
            workspace = Workspace.objects.get(slug=slug)
            
            # Check if user has access to workspace
            if not WorkspaceMember.objects.filter(
                workspace=workspace,
                member=request.user,
                is_active=True
            ).exists():
                return Response(
                    {"error": "Insufficient permissions"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Debug logging
            logger.info(f"Workspace stripe_customer_id: {workspace.stripe_customer_id}")
            logger.info(f"Workspace subscription_status: {workspace.subscription_status}")
            logger.info(f"Workspace stripe_subscription_id: {workspace.stripe_subscription_id}")
            
            # Try to get fresh data from Stripe
            stripe_service = StripeService()
            
            if workspace.stripe_customer_id:
                try:
                    logger.info(f"Fetching fresh subscription data for customer: {workspace.stripe_customer_id}")
                    subscription_data = stripe_service.get_customer_subscriptions(workspace.stripe_customer_id)
                    
                    logger.info(f"Stripe subscription data: {subscription_data}")
                    
                    # Update workspace with fresh data
                    stripe_service.update_workspace_subscription(workspace, subscription_data)
                    
                    # Return fresh data from Stripe if available
                    if subscription_data.get('subscription') and subscription_data.get('has_active_subscription'):
                        subscription = subscription_data['subscription']
                        logger.info(f"Returning fresh subscription data: {subscription}")
                        return Response({
                            'id': subscription.get('id'),
                            'status': subscription.get('status'),
                            'current_period_start': subscription.get('current_period_start'),
                            'current_period_end': subscription.get('current_period_end'),
                            'cancel_at_period_end': subscription.get('cancel_at_period_end'),
                            'customer': subscription.get('customer'),
                            'price_id': subscription.get('price_id'),
                        }, status=status.HTTP_200_OK)
                    else:
                        logger.info("No active subscription found in Stripe data")
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch fresh subscription data from Stripe: {str(e)}")
                    # Continue with stored data if Stripe fetch fails
            else:
                # No customer ID, try to sync with Stripe
                logger.info(f"No customer ID found, attempting to sync workspace {workspace.slug} with Stripe")
                try:
                    subscription_data = stripe_service.sync_workspace_with_stripe(workspace.slug)
                    
                    if subscription_data.get('subscription') and subscription_data.get('has_active_subscription'):
                        subscription = subscription_data['subscription']
                        logger.info(f"Synced and returning subscription data: {subscription}")
                        return Response({
                            'id': subscription.get('id'),
                            'status': subscription.get('status'),
                            'current_period_start': subscription.get('current_period_start'),
                            'current_period_end': subscription.get('current_period_end'),
                            'cancel_at_period_end': subscription.get('cancel_at_period_end'),
                            'customer': subscription.get('customer'),
                            'price_id': subscription.get('price_id'),
                        }, status=status.HTTP_200_OK)
                    else:
                        logger.info("No active subscription found after sync")
                        
                except Exception as e:
                    logger.warning(f"Failed to sync workspace with Stripe: {str(e)}")
            
            # Return subscription data from workspace model
            subscription_data = {
                'id': workspace.stripe_subscription_id,
                'status': workspace.subscription_status,
                'current_period_start': int(workspace.subscription_current_period_start.timestamp()) if workspace.subscription_current_period_start else None,
                'current_period_end': int(workspace.subscription_current_period_end.timestamp()) if workspace.subscription_current_period_end else None,
                'cancel_at_period_end': workspace.subscription_cancel_at_period_end,
                'customer': workspace.stripe_customer_id,
                'price_id': workspace.subscription_price_id,
            }
            
            return Response(subscription_data, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace not found: {slug}")
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error retrieving subscription status: {str(e)}")
            return Response(
                {"error": "Failed to retrieve subscription status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
