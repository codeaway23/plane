"""
Management command to link existing Stripe subscriptions to workspaces
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from plane.db.models import Workspace, User
from plane.api.services.stripe_service import StripeService
import stripe
from django.conf import settings


class Command(BaseCommand):
    help = 'Link existing Stripe subscriptions to workspaces'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to find customer and link subscription',
        )
        parser.add_argument(
            '--workspace-slug',
            type=str,
            help='Workspace slug to link subscription to',
        )
        parser.add_argument(
            '--customer-id',
            type=str,
            help='Stripe customer ID to link subscription to',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        # Set up Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        email = options.get('email')
        workspace_slug = options.get('workspace_slug')
        customer_id = options.get('customer_id')
        dry_run = options.get('dry_run', False)

        if not any([email, customer_id]):
            raise CommandError('Must provide either --email or --customer-id')

        try:
            # Find workspace
            if workspace_slug:
                workspace = Workspace.objects.get(slug=workspace_slug)
            else:
                # Get the first workspace if not specified
                workspace = Workspace.objects.first()
                if not workspace:
                    raise CommandError('No workspace found')

            self.stdout.write(f'Target workspace: {workspace.slug}')

            # Find customer
            if customer_id:
                customer = stripe.Customer.retrieve(customer_id)
            elif email:
                customers = stripe.Customer.list(email=email, limit=1)
                if not customers.data:
                    raise CommandError(f'No Stripe customer found for email: {email}')
                customer = customers.data[0]
            else:
                raise CommandError('Must provide either email or customer ID')

            self.stdout.write(f'Found Stripe customer: {customer.id} ({customer.email})')

            # Get active subscriptions
            subscriptions = stripe.Subscription.list(customer=customer.id, status='active')
            if not subscriptions.data:
                self.stdout.write(self.style.WARNING('No active subscriptions found for this customer'))
                return

            subscription = subscriptions.data[0]
            self.stdout.write(f'Found active subscription: {subscription.id}')

            # Get subscription details
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

            self.stdout.write(f'Subscription details:')
            self.stdout.write(f'  Status: {subscription.status}')
            self.stdout.write(f'  Price ID: {price_id}')
            self.stdout.write(f'  Product ID: {product_id}')
            self.stdout.write(f'  Period start: {current_period_start}')
            self.stdout.write(f'  Period end: {current_period_end}')

            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN - No changes made'))
                return

            # Update workspace
            with transaction.atomic():
                workspace.stripe_customer_id = customer.id
                workspace.save()

                # Update subscription data
                stripe_service = StripeService()
                subscription_data = {
                    'subscription': {
                        'id': subscription.id,
                        'status': subscription.status,
                        'current_period_start': current_period_start,
                        'current_period_end': current_period_end,
                        'cancel_at_period_end': subscription.cancel_at_period_end,
                        'customer': customer.id,
                        'price_id': price_id,
                        'product_id': product_id,
                    }
                }
                stripe_service.update_workspace_subscription(workspace, subscription_data)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully linked subscription {subscription.id} to workspace {workspace.slug}'
                )
            )

        except Workspace.DoesNotExist:
            raise CommandError(f'Workspace not found: {workspace_slug}')
        except stripe.error.StripeError as e:
            raise CommandError(f'Stripe error: {e}')
        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')
