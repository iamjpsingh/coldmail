"""Selectors for campaigns app - handles all complex query operations."""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from django.db.models import QuerySet, Count, Q, F, Sum, Avg, Case, When, IntegerField
from django.utils import timezone

from .models import (
    Campaign,
    CampaignRecipient,
    CampaignEvent,
    CampaignLog,
    EmailTemplate,
    ABTestVariant,
)


class CampaignSelector:
    """Selectors for Campaign queries."""

    @staticmethod
    def get_workspace_campaigns(
        workspace_id: UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
        ordering: str = '-created_at',
    ) -> QuerySet[Campaign]:
        """
        Fetch campaigns for a workspace with filters and optimized relations.

        Args:
            workspace_id: UUID of the workspace.
            status: Optional status filter.
            search: Optional search term for name/description.
            ordering: Field to order by (prefix with - for descending).

        Returns:
            Annotated QuerySet with optimized related data.
        """
        qs = Campaign.objects.filter(
            workspace_id=workspace_id
        ).select_related(
            'email_account',
            'template',
            'created_by',
        ).annotate(
            recipient_count=Count('recipients'),
            pending_count=Count(
                'recipients',
                filter=Q(recipients__status__in=['pending', 'queued'])
            ),
        )

        if status:
            qs = qs.filter(status=status)

        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return qs.order_by(ordering)

    @staticmethod
    def get_campaign_with_stats(campaign_id: UUID) -> Optional[Campaign]:
        """
        Get single campaign with comprehensive statistics.

        Args:
            campaign_id: UUID of the campaign.

        Returns:
            Campaign with annotated stats, or None if not found.
        """
        return Campaign.objects.filter(
            id=campaign_id
        ).select_related(
            'email_account',
            'template',
            'created_by',
            'workspace',
        ).prefetch_related(
            'ab_variants',
            'contact_lists',
            'contact_tags',
        ).annotate(
            recipient_count=Count('recipients'),
            pending_count=Count('recipients', filter=Q(recipients__status='pending')),
            queued_count=Count('recipients', filter=Q(recipients__status='queued')),
            sending_count=Count('recipients', filter=Q(recipients__status='sending')),
            sent_count_calc=Count('recipients', filter=Q(recipients__status='sent')),
            delivered_count_calc=Count('recipients', filter=Q(recipients__status='delivered')),
            opened_count_calc=Count('recipients', filter=Q(recipients__opened_at__isnull=False)),
            clicked_count_calc=Count('recipients', filter=Q(recipients__clicked_at__isnull=False)),
            replied_count_calc=Count('recipients', filter=Q(recipients__replied_at__isnull=False)),
            bounced_count_calc=Count('recipients', filter=Q(recipients__status='bounced')),
            failed_count_calc=Count('recipients', filter=Q(recipients__status='failed')),
        ).first()

    @staticmethod
    def get_campaigns_summary(workspace_id: UUID) -> Dict[str, Any]:
        """
        Get summary statistics for all campaigns in a workspace.

        Args:
            workspace_id: UUID of the workspace.

        Returns:
            Dictionary with campaign counts and aggregate stats.
        """
        base_qs = Campaign.objects.filter(workspace_id=workspace_id)

        # Status counts
        status_counts = base_qs.values('status').annotate(
            count=Count('id')
        )

        status_dict = {item['status']: item['count'] for item in status_counts}

        # Aggregate stats from completed campaigns
        completed_stats = base_qs.filter(
            status=Campaign.Status.COMPLETED
        ).aggregate(
            total_sent=Sum('sent_count'),
            total_opened=Sum('unique_opens'),
            total_clicked=Sum('unique_clicks'),
            total_replied=Sum('replied_count'),
            total_bounced=Sum('bounced_count'),
        )

        return {
            'total': base_qs.count(),
            'draft': status_dict.get('draft', 0),
            'scheduled': status_dict.get('scheduled', 0),
            'sending': status_dict.get('sending', 0),
            'paused': status_dict.get('paused', 0),
            'completed': status_dict.get('completed', 0),
            'cancelled': status_dict.get('cancelled', 0),
            'total_emails_sent': completed_stats['total_sent'] or 0,
            'total_opens': completed_stats['total_opened'] or 0,
            'total_clicks': completed_stats['total_clicked'] or 0,
            'total_replies': completed_stats['total_replied'] or 0,
            'total_bounces': completed_stats['total_bounced'] or 0,
        }

    @staticmethod
    def get_active_campaigns(workspace_id: UUID) -> QuerySet[Campaign]:
        """Get campaigns that are currently active (sending or scheduled)."""
        return Campaign.objects.filter(
            workspace_id=workspace_id,
            status__in=[Campaign.Status.SENDING, Campaign.Status.SCHEDULED]
        ).select_related('email_account').order_by('-started_at')

    @staticmethod
    def get_recent_campaigns(
        workspace_id: UUID,
        limit: int = 10
    ) -> QuerySet[Campaign]:
        """Get most recently updated campaigns."""
        return Campaign.objects.filter(
            workspace_id=workspace_id
        ).select_related('email_account', 'template').order_by('-updated_at')[:limit]


class CampaignRecipientSelector:
    """Selectors for CampaignRecipient queries."""

    @staticmethod
    def get_campaign_recipients(
        campaign_id: UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> QuerySet[CampaignRecipient]:
        """
        Get recipients for a campaign with filters.

        Args:
            campaign_id: UUID of the campaign.
            status: Optional status filter.
            search: Optional search term for contact email/name.
            limit: Maximum number of results.

        Returns:
            QuerySet of recipients with related data.
        """
        qs = CampaignRecipient.objects.filter(
            campaign_id=campaign_id
        ).select_related(
            'contact',
            'ab_variant',
            'email_account',
        )

        if status:
            qs = qs.filter(status=status)

        if search:
            qs = qs.filter(
                Q(contact__email__icontains=search) |
                Q(contact__first_name__icontains=search) |
                Q(contact__last_name__icontains=search)
            )

        return qs.order_by('-created_at')[:limit]

    @staticmethod
    def get_pending_recipients(
        campaign_id: UUID,
        limit: int = 50,
    ) -> List[CampaignRecipient]:
        """
        Get recipients ready to be sent.

        Args:
            campaign_id: UUID of the campaign.
            limit: Maximum number of recipients to return.

        Returns:
            List of recipients ready for sending.
        """
        now = timezone.now()
        return list(
            CampaignRecipient.objects.filter(
                campaign_id=campaign_id,
                status=CampaignRecipient.Status.QUEUED,
                send_after__lte=now,
            ).select_related(
                'contact',
                'ab_variant',
            ).order_by('scheduled_at')[:limit]
        )

    @staticmethod
    def get_failed_recipients(
        campaign_id: UUID,
        max_retries: int = 3,
    ) -> QuerySet[CampaignRecipient]:
        """Get failed recipients eligible for retry."""
        return CampaignRecipient.objects.filter(
            campaign_id=campaign_id,
            status=CampaignRecipient.Status.FAILED,
            retry_count__lt=max_retries,
        ).select_related('contact')

    @staticmethod
    def get_recipient_status_counts(campaign_id: UUID) -> Dict[str, int]:
        """Get count of recipients by status."""
        counts = CampaignRecipient.objects.filter(
            campaign_id=campaign_id
        ).values('status').annotate(count=Count('id'))

        return {item['status']: item['count'] for item in counts}


class CampaignEventSelector:
    """Selectors for CampaignEvent queries."""

    @staticmethod
    def get_campaign_events(
        campaign_id: UUID,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> QuerySet[CampaignEvent]:
        """
        Get events for a campaign.

        Args:
            campaign_id: UUID of the campaign.
            event_type: Optional event type filter.
            limit: Maximum number of results.

        Returns:
            QuerySet of events with related data.
        """
        qs = CampaignEvent.objects.filter(
            recipient__campaign_id=campaign_id
        ).select_related(
            'recipient',
            'recipient__contact',
        )

        if event_type:
            qs = qs.filter(event_type=event_type)

        return qs.order_by('-created_at')[:limit]

    @staticmethod
    def get_event_timeline(
        campaign_id: UUID,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Get event counts by hour for the last N hours.

        Args:
            campaign_id: UUID of the campaign.
            hours: Number of hours to look back.

        Returns:
            List of hourly event counts.
        """
        since = timezone.now() - timedelta(hours=hours)

        events = CampaignEvent.objects.filter(
            recipient__campaign_id=campaign_id,
            created_at__gte=since,
        ).values('event_type').annotate(
            count=Count('id')
        )

        return list(events)


class TemplateSelector:
    """Selectors for EmailTemplate queries."""

    @staticmethod
    def get_workspace_templates(
        workspace_id: UUID,
        category: Optional[str] = None,
        search: Optional[str] = None,
        folder_id: Optional[UUID] = None,
    ) -> QuerySet[EmailTemplate]:
        """
        Get templates for a workspace with filters.

        Args:
            workspace_id: UUID of the workspace.
            category: Optional category filter.
            search: Optional search term.
            folder_id: Optional folder filter.

        Returns:
            QuerySet of templates.
        """
        qs = EmailTemplate.objects.filter(
            workspace_id=workspace_id
        ).select_related(
            'signature',
            'created_by',
        )

        if category:
            qs = qs.filter(category=category)

        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(subject__icontains=search) |
                Q(description__icontains=search)
            )

        if folder_id:
            qs = qs.filter(folders__id=folder_id)

        return qs.order_by('-updated_at')

    @staticmethod
    def get_popular_templates(
        workspace_id: UUID,
        limit: int = 5,
    ) -> QuerySet[EmailTemplate]:
        """Get most frequently used templates."""
        return EmailTemplate.objects.filter(
            workspace_id=workspace_id
        ).order_by('-times_used')[:limit]
