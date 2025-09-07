"""
AI Usage API views for metered billing management
"""

import logging
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from .base import BaseAPIView
from plane.app.permissions import WorkspaceEntityPermission
from plane.authentication.session import BaseSessionAuthentication
from plane.db.models import Workspace, WorkspaceMember
from plane.api.services.ai_usage_stripe_service import AIUsageStripeService
from plane.api.serializers.ai_usage import (
    AIUsageCheckoutSerializer,
    AIUsageRecordSerializer,
    AIUsageHistorySerializer
)

logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIUsagePlansView(BaseAPIView):
    """API view for getting available AI usage plans"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def get(self, request, slug):
        """
        Get available AI usage plans with current pricing
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with AI plans data
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
                ai_service = AIUsageStripeService()
            except Exception as e:
                logger.error(f"AI Usage service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI usage service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            plans = ai_service.get_ai_plans()
            
            return Response(plans, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting AI usage plans: {str(e)}")
            return Response(
                {"error": "Failed to get AI usage plans"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIUsageSubscriptionsView(BaseAPIView):
    """API view for managing AI usage subscriptions"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def get(self, request, slug):
        """
        Get current AI usage subscriptions for workspace
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with subscription status
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
                ai_service = AIUsageStripeService()
            except Exception as e:
                logger.error(f"AI Usage service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI usage service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            subscriptions = ai_service.get_workspace_ai_subscriptions(slug)
            
            return Response(subscriptions, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting AI usage subscriptions: {str(e)}")
            return Response(
                {"error": "Failed to get AI usage subscriptions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIUsageCheckoutView(BaseAPIView):
    """API view for creating AI usage checkout sessions"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def post(self, request, slug):
        """
        Create a Stripe checkout session for AI usage subscription
        
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
            
            serializer = AIUsageCheckoutSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                ai_service = AIUsageStripeService()
            except Exception as e:
                logger.error(f"AI Usage service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI usage service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            success_url = settings.STRIPE_SUCCESS_URL.replace('{workspace_slug}', slug)
            cancel_url = settings.STRIPE_CANCEL_URL.replace('{workspace_slug}', slug)

            checkout_data = ai_service.create_ai_usage_checkout_session(
                workspace=workspace,
                user=request.user,
                plan_type=serializer.validated_data['plan_type'],
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            return Response(checkout_data, status=status.HTTP_201_CREATED)
            
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating AI usage checkout session: {str(e)}")
            return Response(
                {"error": "Failed to create checkout session"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIUsageSubscriptionManagementView(BaseAPIView):
    """API view for managing AI usage subscriptions (cancel/restart)"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def post(self, request, slug, action_type):
        """
        Cancel or restart an AI usage subscription
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            action_type: 'cancel' or 'restart'
            
        Returns:
            Response with action results
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
            
            plan_type = request.data.get('plan_type')
            if not plan_type:
                return Response(
                    {"error": "plan_type is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                ai_service = AIUsageStripeService()
            except Exception as e:
                logger.error(f"AI Usage service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI usage service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            if action_type == 'cancel':
                result = ai_service.cancel_ai_usage_subscription(slug, plan_type)
            elif action_type == 'restart':
                result = ai_service.restart_ai_usage_subscription(slug, plan_type)
            else:
                return Response(
                    {"error": "Invalid action type. Must be 'cancel' or 'restart'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error managing AI usage subscription: {str(e)}")
            return Response(
                {"error": "Failed to manage subscription"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIUsageHistoryView(BaseAPIView):
    """API view for getting AI usage history"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def get(self, request, slug):
        """
        Get AI usage history for workspace
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with usage history
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
                ai_service = AIUsageStripeService()
            except Exception as e:
                logger.error(f"AI Usage service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI usage service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            plan_type = request.query_params.get('plan_type')
            limit = int(request.query_params.get('limit', 50))
            
            history = ai_service.get_ai_usage_history(slug, plan_type, limit)
            
            return Response(history, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting AI usage history: {str(e)}")
            return Response(
                {"error": "Failed to get usage history"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIUsageRecordView(BaseAPIView):
    """API view for recording AI usage"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def post(self, request, slug):
        """
        Record AI usage for metered billing
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with usage record data
        """
        try:
            workspace = Workspace.objects.get(slug=slug)
            
            # Check if user has permissions to use AI
            if not WorkspaceMember.objects.filter(
                workspace=workspace,
                member=request.user,
                is_active=True
            ).exists():
                return Response(
                    {"error": "Insufficient permissions"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = AIUsageRecordSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                ai_service = AIUsageStripeService()
            except Exception as e:
                logger.error(f"AI Usage service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI usage service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            result = ai_service.record_ai_usage(
                workspace_slug=slug,
                user=request.user,
                plan_type=serializer.validated_data['plan_type'],
                usage_count=serializer.validated_data.get('usage_count', 1),
                metadata=serializer.validated_data.get('metadata', {})
            )
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error recording AI usage: {str(e)}")
            return Response(
                {"error": "Failed to record usage"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
