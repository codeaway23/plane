"""
AI Pack API views for Core AI Pack and Scale AI Pack subscription management
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
from plane.api.services.ai_pack_stripe_service import AIPackStripeService
from plane.api.serializers.ai_pack import (
    AIPackCheckoutSerializer,
    AIPackUpgradeSerializer
)

logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIPackPlansView(BaseAPIView):
    """API view for getting available AI Pack plans"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def get(self, request, slug):
        """
        Get available AI Pack plans with current pricing
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with AI Pack plans data
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
                ai_pack_service = AIPackStripeService()
            except Exception as e:
                logger.error(f"AI Pack service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI Pack service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            plans = ai_pack_service.get_ai_packs()
            
            return Response(plans, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting AI Pack plans: {str(e)}")
            return Response(
                {"error": "Failed to get AI Pack plans"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIPackSubscriptionView(BaseAPIView):
    """API view for managing AI Pack subscriptions"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def get(self, request, slug):
        """
        Get current AI Pack subscription for workspace
        
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
                ai_pack_service = AIPackStripeService()
            except Exception as e:
                logger.error(f"AI Pack service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI Pack service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            subscription = ai_pack_service.get_workspace_ai_pack_subscription(slug)
            
            return Response(subscription, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting AI Pack subscription: {str(e)}")
            return Response(
                {"error": "Failed to get AI Pack subscription"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIPackCheckoutView(BaseAPIView):
    """API view for creating AI Pack checkout sessions"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def post(self, request, slug):
        """
        Create a Stripe checkout session for AI Pack subscription
        
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
            
            serializer = AIPackCheckoutSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                ai_pack_service = AIPackStripeService()
            except Exception as e:
                logger.error(f"AI Pack service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI Pack service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            success_url = settings.STRIPE_SUCCESS_URL.replace('{workspace_slug}', slug)
            cancel_url = settings.STRIPE_CANCEL_URL.replace('{workspace_slug}', slug)

            checkout_data = ai_pack_service.create_ai_pack_checkout_session(
                workspace=workspace,
                user=request.user,
                pack_type=serializer.validated_data['pack_type'],
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
            logger.error(f"Error creating AI Pack checkout session: {str(e)}")
            return Response(
                {"error": "Failed to create checkout session"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIPackSubscriptionManagementView(BaseAPIView):
    """API view for managing AI Pack subscriptions (cancel/restart)"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def post(self, request, slug, action_type):
        """
        Cancel or restart an AI Pack subscription
        
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
            
            try:
                ai_pack_service = AIPackStripeService()
            except Exception as e:
                logger.error(f"AI Pack service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI Pack service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            if action_type == 'cancel':
                result = ai_pack_service.cancel_ai_pack_subscription(slug)
            elif action_type == 'restart':
                result = ai_pack_service.restart_ai_pack_subscription(slug)
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
            logger.error(f"Error managing AI Pack subscription: {str(e)}")
            return Response(
                {"error": "Failed to manage subscription"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIPackUpgradeView(BaseAPIView):
    """API view for upgrading AI Pack subscriptions"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def post(self, request, slug):
        """
        Upgrade AI Pack subscription to a different pack
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with upgrade result
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
            
            serializer = AIPackUpgradeSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                ai_pack_service = AIPackStripeService()
            except Exception as e:
                logger.error(f"AI Pack service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI Pack service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            success_url = settings.STRIPE_SUCCESS_URL.replace('{workspace_slug}', slug)
            cancel_url = settings.STRIPE_CANCEL_URL.replace('{workspace_slug}', slug)

            upgrade_data = ai_pack_service.upgrade_ai_pack_subscription(
                workspace=workspace,
                user=request.user,
                new_pack_type=serializer.validated_data['pack_type'],
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            return Response(upgrade_data, status=status.HTTP_200_OK)
            
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
            logger.error(f"Error upgrading AI Pack subscription: {str(e)}")
            return Response(
                {"error": "Failed to upgrade subscription"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AIPackUsageLimitsView(BaseAPIView):
    """API view for getting AI Pack usage limits"""
    
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [WorkspaceEntityPermission]
    
    def get(self, request, slug):
        """
        Get AI Pack usage limits for workspace
        
        Args:
            request: HTTP request object
            slug: Workspace slug
            
        Returns:
            Response with usage limits
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
            
            try:
                ai_pack_service = AIPackStripeService()
            except Exception as e:
                logger.error(f"AI Pack service initialization failed: {str(e)}")
                return Response(
                    {"error": "AI Pack service is not configured. Please contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            limits = ai_pack_service.get_ai_pack_usage_limits(slug)
            
            return Response(limits, status=status.HTTP_200_OK)
            
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting AI Pack usage limits: {str(e)}")
            return Response(
                {"error": "Failed to get usage limits"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
