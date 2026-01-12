"""Webhook dispatching and delivery services."""
import json
import uuid
import logging
import requests
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from .models import Webhook, WebhookDelivery, WebhookEventLog

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """Service for dispatching webhook events."""

    def __init__(self, workspace):
        self.workspace = workspace

    def dispatch(self, event_type, payload, **metadata):
        """
        Dispatch an event to all subscribed webhooks.

        Args:
            event_type: The event type (e.g., 'contact.created')
            payload: The event payload dict
            **metadata: Additional metadata (contact_id, campaign_id, etc.)

        Returns:
            WebhookEventLog instance
        """
        event_id = str(uuid.uuid4())

        # Create event log
        event_log = WebhookEventLog.objects.create(
            workspace=self.workspace,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            contact_id=metadata.get('contact_id'),
            campaign_id=metadata.get('campaign_id'),
            sequence_id=metadata.get('sequence_id'),
        )

        # Find all active webhooks that subscribe to this event
        webhooks = Webhook.objects.filter(
            workspace=self.workspace,
            is_active=True,
        )

        subscribed_webhooks = [w for w in webhooks if w.subscribes_to(event_type)]

        if not subscribed_webhooks:
            event_log.processed_at = timezone.now()
            event_log.webhooks_triggered = 0
            event_log.save(update_fields=['processed_at', 'webhooks_triggered'])
            return event_log

        # Create delivery records for each webhook
        deliveries = []
        for webhook in subscribed_webhooks:
            delivery = WebhookDelivery.objects.create(
                webhook=webhook,
                event_type=event_type,
                event_id=event_id,
                payload=self._build_payload(event_type, event_id, payload),
                status=WebhookDelivery.Status.PENDING,
            )
            deliveries.append(delivery)

        event_log.webhooks_triggered = len(deliveries)
        event_log.save(update_fields=['webhooks_triggered'])

        # Queue deliveries for async processing
        from .tasks import deliver_webhook
        for delivery in deliveries:
            deliver_webhook.delay(delivery.id)

        event_log.processed_at = timezone.now()
        event_log.save(update_fields=['processed_at'])

        return event_log

    def _build_payload(self, event_type, event_id, data):
        """Build the full webhook payload."""
        return {
            'id': event_id,
            'type': event_type,
            'created_at': timezone.now().isoformat(),
            'workspace_id': str(self.workspace.id),
            'data': data,
        }


class WebhookDeliveryService:
    """Service for delivering webhooks."""

    def __init__(self, delivery):
        self.delivery = delivery
        self.webhook = delivery.webhook

    def deliver(self):
        """
        Attempt to deliver the webhook.

        Returns:
            bool: True if delivery was successful, False otherwise
        """
        self.delivery.status = WebhookDelivery.Status.PROCESSING
        self.delivery.save(update_fields=['status', 'updated_at'])

        try:
            # Prepare payload
            payload_str = json.dumps(self.delivery.payload, default=str)

            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'ColdMail-Webhook/1.0',
                'X-Webhook-ID': str(self.webhook.id),
                'X-Webhook-Event': self.delivery.event_type,
                'X-Webhook-Delivery': str(self.delivery.id),
                'X-Webhook-Signature': self.webhook.sign_payload(payload_str),
            }

            # Add custom headers
            if self.webhook.headers:
                headers.update(self.webhook.headers)

            self.delivery.request_headers = headers

            # Make the request
            start_time = timezone.now()

            response = requests.post(
                self.webhook.url,
                data=payload_str,
                headers=headers,
                timeout=self.webhook.timeout_seconds,
                verify=self.webhook.verify_ssl,
            )

            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Record response
            self.delivery.response_status_code = response.status_code
            self.delivery.response_body = response.text[:10000]  # Limit response body size
            self.delivery.duration_ms = duration_ms
            self.delivery.delivered_at = end_time

            try:
                self.delivery.response_headers = dict(response.headers)
            except Exception:
                self.delivery.response_headers = {}

            # Check if successful (2xx status code)
            if 200 <= response.status_code < 300:
                self.delivery.status = WebhookDelivery.Status.SUCCESS
                self.delivery.save()
                self.webhook.record_delivery(success=True)
                return True
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                self.delivery.error_message = error_msg
                self._handle_failure(error_msg)
                return False

        except requests.Timeout as e:
            error_msg = f"Request timed out after {self.webhook.timeout_seconds}s"
            self.delivery.error_message = error_msg
            self._handle_failure(error_msg)
            return False

        except requests.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            self.delivery.error_message = error_msg
            self._handle_failure(error_msg)
            return False

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(f"Webhook delivery error for {self.delivery.id}")
            self.delivery.error_message = error_msg
            self._handle_failure(error_msg)
            return False

    def _handle_failure(self, error_message):
        """Handle a failed delivery attempt."""
        self.delivery.save()

        # Record failure on webhook
        self.webhook.record_delivery(success=False, error_message=error_message)

        # Schedule retry if applicable
        if self.delivery.schedule_retry():
            from .tasks import deliver_webhook
            # Schedule retry task
            eta = self.delivery.next_retry_at
            deliver_webhook.apply_async(
                args=[self.delivery.id],
                eta=eta,
            )
        else:
            self.delivery.status = WebhookDelivery.Status.FAILED
            self.delivery.save(update_fields=['status', 'updated_at'])


def dispatch_webhook_event(workspace, event_type, payload, **metadata):
    """
    Convenience function to dispatch a webhook event.

    Args:
        workspace: Workspace instance
        event_type: Event type string
        payload: Event data dict
        **metadata: Additional metadata

    Returns:
        WebhookEventLog instance
    """
    dispatcher = WebhookDispatcher(workspace)
    return dispatcher.dispatch(event_type, payload, **metadata)


# Event dispatcher helpers for common events

def dispatch_contact_created(contact):
    """Dispatch contact.created event."""
    from apps.contacts.serializers import ContactSerializer
    payload = ContactSerializer(contact).data
    return dispatch_webhook_event(
        contact.workspace,
        'contact.created',
        payload,
        contact_id=contact.id,
    )


def dispatch_contact_updated(contact):
    """Dispatch contact.updated event."""
    from apps.contacts.serializers import ContactSerializer
    payload = ContactSerializer(contact).data
    return dispatch_webhook_event(
        contact.workspace,
        'contact.updated',
        payload,
        contact_id=contact.id,
    )


def dispatch_contact_deleted(workspace, contact_id, contact_email):
    """Dispatch contact.deleted event."""
    payload = {
        'id': str(contact_id),
        'email': contact_email,
    }
    return dispatch_webhook_event(
        workspace,
        'contact.deleted',
        payload,
        contact_id=contact_id,
    )


def dispatch_email_sent(email_log):
    """Dispatch email.sent event."""
    payload = {
        'id': str(email_log.id),
        'campaign_id': str(email_log.campaign_id) if email_log.campaign_id else None,
        'contact_id': str(email_log.contact_id) if email_log.contact_id else None,
        'email_account_id': str(email_log.email_account_id),
        'to_email': email_log.to_email,
        'subject': email_log.subject,
        'sent_at': email_log.sent_at.isoformat() if email_log.sent_at else None,
    }
    return dispatch_webhook_event(
        email_log.workspace,
        'email.sent',
        payload,
        contact_id=email_log.contact_id,
        campaign_id=email_log.campaign_id,
    )


def dispatch_email_opened(email_log):
    """Dispatch email.opened event."""
    payload = {
        'id': str(email_log.id),
        'campaign_id': str(email_log.campaign_id) if email_log.campaign_id else None,
        'contact_id': str(email_log.contact_id) if email_log.contact_id else None,
        'to_email': email_log.to_email,
        'opened_at': email_log.opened_at.isoformat() if email_log.opened_at else None,
        'open_count': email_log.open_count,
    }
    return dispatch_webhook_event(
        email_log.workspace,
        'email.opened',
        payload,
        contact_id=email_log.contact_id,
        campaign_id=email_log.campaign_id,
    )


def dispatch_email_clicked(email_log, link_url):
    """Dispatch email.clicked event."""
    payload = {
        'id': str(email_log.id),
        'campaign_id': str(email_log.campaign_id) if email_log.campaign_id else None,
        'contact_id': str(email_log.contact_id) if email_log.contact_id else None,
        'to_email': email_log.to_email,
        'link_url': link_url,
        'click_count': email_log.click_count,
    }
    return dispatch_webhook_event(
        email_log.workspace,
        'email.clicked',
        payload,
        contact_id=email_log.contact_id,
        campaign_id=email_log.campaign_id,
    )


def dispatch_email_bounced(email_log, bounce_type=None):
    """Dispatch email.bounced event."""
    payload = {
        'id': str(email_log.id),
        'campaign_id': str(email_log.campaign_id) if email_log.campaign_id else None,
        'contact_id': str(email_log.contact_id) if email_log.contact_id else None,
        'to_email': email_log.to_email,
        'bounce_type': bounce_type,
        'bounced_at': email_log.bounced_at.isoformat() if email_log.bounced_at else None,
    }
    return dispatch_webhook_event(
        email_log.workspace,
        'email.bounced',
        payload,
        contact_id=email_log.contact_id,
        campaign_id=email_log.campaign_id,
    )


def dispatch_email_replied(email_log):
    """Dispatch email.replied event."""
    payload = {
        'id': str(email_log.id),
        'campaign_id': str(email_log.campaign_id) if email_log.campaign_id else None,
        'contact_id': str(email_log.contact_id) if email_log.contact_id else None,
        'to_email': email_log.to_email,
        'replied_at': email_log.replied_at.isoformat() if email_log.replied_at else None,
    }
    return dispatch_webhook_event(
        email_log.workspace,
        'email.replied',
        payload,
        contact_id=email_log.contact_id,
        campaign_id=email_log.campaign_id,
    )


def dispatch_campaign_started(campaign):
    """Dispatch campaign.started event."""
    payload = {
        'id': str(campaign.id),
        'name': campaign.name,
        'status': campaign.status,
        'started_at': timezone.now().isoformat(),
    }
    return dispatch_webhook_event(
        campaign.workspace,
        'campaign.started',
        payload,
        campaign_id=campaign.id,
    )


def dispatch_campaign_completed(campaign):
    """Dispatch campaign.completed event."""
    payload = {
        'id': str(campaign.id),
        'name': campaign.name,
        'status': campaign.status,
        'completed_at': timezone.now().isoformat(),
        'stats': {
            'total_contacts': campaign.total_contacts,
            'emails_sent': campaign.emails_sent,
            'emails_opened': campaign.emails_opened,
            'emails_clicked': campaign.emails_clicked,
        },
    }
    return dispatch_webhook_event(
        campaign.workspace,
        'campaign.completed',
        payload,
        campaign_id=campaign.id,
    )


def dispatch_sequence_enrolled(enrollment):
    """Dispatch sequence.enrolled event."""
    payload = {
        'id': str(enrollment.id),
        'sequence_id': str(enrollment.sequence_id),
        'contact_id': str(enrollment.contact_id),
        'enrolled_at': enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
    }
    return dispatch_webhook_event(
        enrollment.sequence.workspace,
        'sequence.enrolled',
        payload,
        contact_id=enrollment.contact_id,
        sequence_id=enrollment.sequence_id,
    )


def dispatch_sequence_completed(enrollment):
    """Dispatch sequence.completed event."""
    payload = {
        'id': str(enrollment.id),
        'sequence_id': str(enrollment.sequence_id),
        'contact_id': str(enrollment.contact_id),
        'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None,
    }
    return dispatch_webhook_event(
        enrollment.sequence.workspace,
        'sequence.completed',
        payload,
        contact_id=enrollment.contact_id,
        sequence_id=enrollment.sequence_id,
    )


def dispatch_visitor_identified(visitor):
    """Dispatch visitor.identified event."""
    payload = {
        'id': str(visitor.id),
        'visitor_id': visitor.visitor_id,
        'contact_id': str(visitor.contact_id) if visitor.contact_id else None,
        'email': visitor.email,
        'identified_at': timezone.now().isoformat(),
    }
    return dispatch_webhook_event(
        visitor.workspace,
        'visitor.identified',
        payload,
        contact_id=visitor.contact_id,
    )


def dispatch_visitor_page_view(page_view):
    """Dispatch visitor.page_view event."""
    payload = {
        'id': str(page_view.id),
        'visitor_id': str(page_view.visitor_id),
        'url': page_view.url,
        'title': page_view.title,
        'viewed_at': page_view.created_at.isoformat(),
    }
    return dispatch_webhook_event(
        page_view.visitor.workspace,
        'visitor.page_view',
        payload,
    )
