"""Celery tasks for webhook delivery."""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=0,  # We handle retries ourselves
    acks_late=True,
)
def deliver_webhook(self, delivery_id):
    """
    Deliver a webhook.

    Args:
        delivery_id: ID of the WebhookDelivery to process
    """
    from .models import WebhookDelivery
    from .services import WebhookDeliveryService

    try:
        delivery = WebhookDelivery.objects.select_related('webhook').get(id=delivery_id)
    except WebhookDelivery.DoesNotExist:
        logger.error(f"WebhookDelivery {delivery_id} not found")
        return

    # Check if already processed
    if delivery.status == WebhookDelivery.Status.SUCCESS:
        logger.info(f"WebhookDelivery {delivery_id} already successful, skipping")
        return

    # Check if webhook is still active
    if not delivery.webhook.is_active:
        logger.info(f"Webhook {delivery.webhook.id} is disabled, skipping delivery")
        delivery.status = WebhookDelivery.Status.FAILED
        delivery.error_message = "Webhook was disabled"
        delivery.save(update_fields=['status', 'error_message', 'updated_at'])
        return

    # Increment attempt number for retries
    if delivery.status == WebhookDelivery.Status.RETRYING:
        delivery.attempt_number += 1
        delivery.save(update_fields=['attempt_number'])

    # Perform delivery
    service = WebhookDeliveryService(delivery)
    success = service.deliver()

    if success:
        logger.info(f"WebhookDelivery {delivery_id} succeeded")
    else:
        logger.warning(f"WebhookDelivery {delivery_id} failed: {delivery.error_message}")


@shared_task
def process_pending_webhook_retries():
    """
    Process any pending webhook retries that are due.
    This task should be run periodically (e.g., every minute).
    """
    from .models import WebhookDelivery

    now = timezone.now()

    # Find deliveries that need to be retried
    pending_retries = WebhookDelivery.objects.filter(
        status=WebhookDelivery.Status.RETRYING,
        next_retry_at__lte=now,
    ).select_related('webhook')

    count = 0
    for delivery in pending_retries:
        if delivery.webhook.is_active:
            deliver_webhook.delay(delivery.id)
            count += 1
        else:
            # Webhook was disabled, fail the delivery
            delivery.status = WebhookDelivery.Status.FAILED
            delivery.error_message = "Webhook was disabled"
            delivery.save(update_fields=['status', 'error_message', 'updated_at'])

    if count:
        logger.info(f"Queued {count} webhook deliveries for retry")

    return count


@shared_task
def cleanup_old_webhook_deliveries(days=30):
    """
    Clean up old webhook delivery logs.

    Args:
        days: Number of days to keep delivery logs
    """
    from .models import WebhookDelivery

    cutoff = timezone.now() - timezone.timedelta(days=days)

    deleted_count, _ = WebhookDelivery.objects.filter(
        created_at__lt=cutoff,
        status__in=[
            WebhookDelivery.Status.SUCCESS,
            WebhookDelivery.Status.FAILED,
        ]
    ).delete()

    if deleted_count:
        logger.info(f"Cleaned up {deleted_count} old webhook delivery logs")

    return deleted_count


@shared_task
def cleanup_old_webhook_events(days=30):
    """
    Clean up old webhook event logs.

    Args:
        days: Number of days to keep event logs
    """
    from .models import WebhookEventLog

    cutoff = timezone.now() - timezone.timedelta(days=days)

    deleted_count, _ = WebhookEventLog.objects.filter(
        created_at__lt=cutoff,
    ).delete()

    if deleted_count:
        logger.info(f"Cleaned up {deleted_count} old webhook event logs")

    return deleted_count


@shared_task
def test_webhook(webhook_id):
    """
    Send a test webhook event.

    Args:
        webhook_id: ID of the Webhook to test
    """
    from .models import Webhook, WebhookDelivery
    from .services import WebhookDeliveryService
    import uuid

    try:
        webhook = Webhook.objects.get(id=webhook_id)
    except Webhook.DoesNotExist:
        logger.error(f"Webhook {webhook_id} not found")
        return None

    # Create a test delivery
    event_id = str(uuid.uuid4())
    test_payload = {
        'id': event_id,
        'type': 'webhook.test',
        'created_at': timezone.now().isoformat(),
        'workspace_id': str(webhook.workspace_id),
        'data': {
            'message': 'This is a test webhook event',
            'webhook_id': str(webhook.id),
            'webhook_name': webhook.name,
        },
    }

    delivery = WebhookDelivery.objects.create(
        webhook=webhook,
        event_type='webhook.test',
        event_id=event_id,
        payload=test_payload,
        status=WebhookDelivery.Status.PENDING,
    )

    # Deliver synchronously for immediate feedback
    service = WebhookDeliveryService(delivery)
    success = service.deliver()

    return {
        'success': success,
        'delivery_id': str(delivery.id),
        'status_code': delivery.response_status_code,
        'error': delivery.error_message if not success else None,
    }


@shared_task
def reactivate_webhook(webhook_id):
    """
    Reactivate a disabled webhook.

    Args:
        webhook_id: ID of the Webhook to reactivate
    """
    from .models import Webhook

    try:
        webhook = Webhook.objects.get(id=webhook_id)
    except Webhook.DoesNotExist:
        logger.error(f"Webhook {webhook_id} not found")
        return False

    webhook.is_active = True
    webhook.consecutive_failures = 0
    webhook.disabled_at = None
    webhook.disabled_reason = ''
    webhook.save(update_fields=[
        'is_active', 'consecutive_failures', 'disabled_at', 'disabled_reason', 'updated_at'
    ])

    logger.info(f"Webhook {webhook_id} reactivated")
    return True
