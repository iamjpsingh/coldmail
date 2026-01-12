import time
import random
from celery import shared_task
from django.utils import timezone
from django.db import transaction


@shared_task
def prepare_campaign_recipients(campaign_id: str):
    """Prepare recipients for a campaign."""
    from .models import Campaign
    from .services import CampaignService

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return {'error': 'Campaign not found'}

    service = CampaignService(campaign)
    result = service.prepare_recipients()

    return {
        'success': result.success,
        'message': result.message,
        'total_recipients': result.total_recipients,
        'skipped_count': result.skipped_count,
    }


@shared_task
def schedule_campaign_recipients(campaign_id: str):
    """Schedule recipients for sending."""
    from .models import Campaign
    from .services import CampaignService

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return {'error': 'Campaign not found'}

    service = CampaignService(campaign)

    # Assign A/B variants if applicable
    if campaign.is_ab_test:
        service.assign_ab_variants()

    # Schedule recipients
    service.schedule_recipients()

    return {
        'success': True,
        'message': 'Recipients scheduled',
        'total_recipients': campaign.total_recipients
    }


@shared_task
def start_campaign_sending(campaign_id: str):
    """Start sending a campaign."""
    from .models import Campaign
    from .services import CampaignService

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return {'error': 'Campaign not found'}

    service = CampaignService(campaign)
    success, message = service.start_sending()

    if success:
        # Queue the process task
        process_campaign_queue.delay(campaign_id)

    return {
        'success': success,
        'message': message
    }


@shared_task
def process_campaign_queue(campaign_id: str, batch_size: int = 10):
    """Process the campaign sending queue."""
    from .models import Campaign, CampaignRecipient
    from .services import CampaignService

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return {'error': 'Campaign not found'}

    # Check if campaign is still sending
    if campaign.status != Campaign.Status.SENDING:
        return {
            'status': campaign.status,
            'message': 'Campaign not in sending state'
        }

    service = CampaignService(campaign)

    # Get next batch of recipients
    recipients = service.get_next_recipients(limit=batch_size)

    if not recipients:
        # Check if there are still pending recipients
        pending_count = campaign.recipients.filter(
            status__in=[
                CampaignRecipient.Status.QUEUED,
                CampaignRecipient.Status.SENDING
            ]
        ).count()

        if pending_count == 0:
            # Campaign is complete
            service.check_completion()
            return {
                'status': 'completed',
                'sent_count': campaign.sent_count
            }
        else:
            # Still waiting for scheduled recipients
            # Reschedule this task to check again
            process_campaign_queue.apply_async(
                args=[campaign_id, batch_size],
                countdown=30  # Check again in 30 seconds
            )
            return {
                'status': 'waiting',
                'pending_count': pending_count
            }

    # Process recipients
    sent_count = 0
    failed_count = 0

    for recipient in recipients:
        # Check campaign status (might have been paused)
        campaign.refresh_from_db()
        if campaign.status != Campaign.Status.SENDING:
            break

        result = service.send_to_recipient(recipient)
        if result.success:
            sent_count += 1
        else:
            failed_count += 1

        # Add a small random delay between emails
        delay = random.uniform(0.5, 2.0)
        time.sleep(delay)

    # Queue next batch
    if campaign.status == Campaign.Status.SENDING:
        process_campaign_queue.apply_async(
            args=[campaign_id, batch_size],
            countdown=5  # Small delay before next batch
        )

    return {
        'status': 'processing',
        'batch_sent': sent_count,
        'batch_failed': failed_count,
        'total_sent': campaign.sent_count
    }


@shared_task
def send_single_campaign_email(recipient_id: str):
    """Send email to a single campaign recipient."""
    from .models import Campaign, CampaignRecipient
    from .services import CampaignService

    try:
        recipient = CampaignRecipient.objects.select_related(
            'campaign', 'contact', 'ab_variant'
        ).get(id=recipient_id)
    except CampaignRecipient.DoesNotExist:
        return {'error': 'Recipient not found'}

    campaign = recipient.campaign

    # Check campaign status
    if campaign.status != Campaign.Status.SENDING:
        return {
            'error': f'Campaign not in sending state: {campaign.status}'
        }

    service = CampaignService(campaign)
    result = service.send_to_recipient(recipient)

    # Check campaign completion
    service.check_completion()

    return {
        'success': result.success,
        'message': result.message,
        'message_id': result.message_id,
        'recipient_id': result.recipient_id
    }


@shared_task
def check_ab_test_winner(campaign_id: str):
    """Check and select A/B test winner if duration has elapsed."""
    from .models import Campaign
    from .services import CampaignService

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return {'error': 'Campaign not found'}

    if not campaign.is_ab_test:
        return {'error': 'Campaign is not an A/B test'}

    # Check if enough time has passed
    if campaign.started_at:
        elapsed_hours = (timezone.now() - campaign.started_at).total_seconds() / 3600
        if elapsed_hours < campaign.ab_test_duration_hours:
            return {
                'status': 'waiting',
                'elapsed_hours': elapsed_hours,
                'required_hours': campaign.ab_test_duration_hours
            }

    service = CampaignService(campaign)
    winner = service.select_ab_winner()

    if winner:
        return {
            'success': True,
            'winner': winner.name,
            'open_rate': winner.open_rate,
            'click_rate': winner.click_rate
        }

    return {'error': 'Could not determine winner'}


@shared_task
def process_scheduled_campaigns():
    """Process campaigns that are scheduled to start."""
    from .models import Campaign

    now = timezone.now()

    campaigns = Campaign.objects.filter(
        status=Campaign.Status.SCHEDULED,
        scheduled_at__lte=now
    )

    started_count = 0
    for campaign in campaigns:
        start_campaign_sending.delay(str(campaign.id))
        started_count += 1

    return {
        'started_count': started_count
    }


@shared_task
def retry_failed_recipients(campaign_id: str, max_retries: int = 3):
    """Retry sending to failed recipients."""
    from .models import Campaign, CampaignRecipient
    from .services import CampaignService

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return {'error': 'Campaign not found'}

    # Get failed recipients that haven't exceeded retry limit
    failed_recipients = campaign.recipients.filter(
        status=CampaignRecipient.Status.FAILED,
        retry_count__lt=max_retries
    )

    if not failed_recipients.exists():
        return {'message': 'No recipients to retry'}

    # Reset status to queued
    failed_recipients.update(
        status=CampaignRecipient.Status.QUEUED,
        send_after=timezone.now()
    )

    # Start processing if campaign is in a sendable state
    if campaign.status in [Campaign.Status.SENDING, Campaign.Status.PAUSED]:
        campaign.status = Campaign.Status.SENDING
        campaign.save(update_fields=['status'])
        process_campaign_queue.delay(str(campaign.id))

    return {
        'retrying_count': failed_recipients.count()
    }


@shared_task
def update_campaign_stats(campaign_id: str):
    """Update campaign statistics from recipient data."""
    from .models import Campaign, CampaignRecipient
    from django.db.models import Count, Q

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return {'error': 'Campaign not found'}

    recipients = campaign.recipients.all()

    # Count by status
    stats = recipients.aggregate(
        sent=Count('pk', filter=Q(status__in=[
            CampaignRecipient.Status.SENT,
            CampaignRecipient.Status.DELIVERED,
            CampaignRecipient.Status.OPENED,
            CampaignRecipient.Status.CLICKED,
            CampaignRecipient.Status.REPLIED,
        ])),
        delivered=Count('pk', filter=Q(status__in=[
            CampaignRecipient.Status.DELIVERED,
            CampaignRecipient.Status.OPENED,
            CampaignRecipient.Status.CLICKED,
            CampaignRecipient.Status.REPLIED,
        ])),
        opened=Count('pk', filter=Q(status__in=[
            CampaignRecipient.Status.OPENED,
            CampaignRecipient.Status.CLICKED,
            CampaignRecipient.Status.REPLIED,
        ])),
        clicked=Count('pk', filter=Q(status__in=[
            CampaignRecipient.Status.CLICKED,
            CampaignRecipient.Status.REPLIED,
        ])),
        replied=Count('pk', filter=Q(status=CampaignRecipient.Status.REPLIED)),
        bounced=Count('pk', filter=Q(status=CampaignRecipient.Status.BOUNCED)),
        unsubscribed=Count('pk', filter=Q(status=CampaignRecipient.Status.UNSUBSCRIBED)),
        complained=Count('pk', filter=Q(status=CampaignRecipient.Status.COMPLAINED)),
        failed=Count('pk', filter=Q(status=CampaignRecipient.Status.FAILED)),
    )

    # Count unique opens and clicks
    unique_opens = recipients.filter(opened_at__isnull=False).count()
    unique_clicks = recipients.filter(clicked_at__isnull=False).count()

    # Update campaign
    campaign.sent_count = stats['sent']
    campaign.delivered_count = stats['delivered']
    campaign.opened_count = stats['opened']
    campaign.clicked_count = stats['clicked']
    campaign.replied_count = stats['replied']
    campaign.bounced_count = stats['bounced']
    campaign.unsubscribed_count = stats['unsubscribed']
    campaign.complained_count = stats['complained']
    campaign.failed_count = stats['failed']
    campaign.unique_opens = unique_opens
    campaign.unique_clicks = unique_clicks
    campaign.save()

    return {
        'campaign_id': str(campaign.id),
        'stats': stats
    }


@shared_task
def cleanup_old_campaign_events(days: int = 90):
    """Clean up old campaign events to save space."""
    from .models import CampaignEvent

    cutoff_date = timezone.now() - timezone.timedelta(days=days)

    deleted_count, _ = CampaignEvent.objects.filter(
        created_at__lt=cutoff_date
    ).delete()

    return {
        'deleted_count': deleted_count
    }
