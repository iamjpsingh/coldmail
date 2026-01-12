import csv
import io
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from django.db.models import Count, Sum, Avg, F, Q, Case, When, Value, IntegerField
from django.db.models.functions import TruncDate, TruncHour, TruncDay, TruncWeek, TruncMonth
from django.utils import timezone


class ReportsService:
    """Service for generating reports and analytics."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id

    # ==================== Dashboard Statistics ====================

    def get_dashboard_stats(self, days: int = 30) -> dict:
        """Get overall dashboard statistics.

        Args:
            days: Number of days to look back

        Returns:
            Dict with dashboard statistics
        """
        from apps.contacts.models import Contact
        from apps.campaigns.models import Campaign, CampaignRecipient
        from apps.tracking.models import TrackingEvent, SuppressionList

        start_date = timezone.now() - timedelta(days=days)

        # Contact stats
        total_contacts = Contact.objects.filter(
            workspace_id=self.workspace_id
        ).count()

        new_contacts = Contact.objects.filter(
            workspace_id=self.workspace_id,
            created_at__gte=start_date
        ).count()

        active_contacts = Contact.objects.filter(
            workspace_id=self.workspace_id,
            is_unsubscribed=False,
            is_bounced=False
        ).count()

        # Campaign stats
        total_campaigns = Campaign.objects.filter(
            workspace_id=self.workspace_id
        ).count()

        active_campaigns = Campaign.objects.filter(
            workspace_id=self.workspace_id,
            status__in=['sending', 'scheduled']
        ).count()

        completed_campaigns = Campaign.objects.filter(
            workspace_id=self.workspace_id,
            status='completed',
            completed_at__gte=start_date
        ).count()

        # Email stats (from campaigns in the time range)
        campaign_stats = Campaign.objects.filter(
            workspace_id=self.workspace_id,
            started_at__gte=start_date
        ).aggregate(
            total_sent=Sum('sent_count'),
            total_delivered=Sum('delivered_count'),
            total_opened=Sum('unique_opens'),
            total_clicked=Sum('unique_clicks'),
            total_replied=Sum('replied_count'),
            total_bounced=Sum('bounced_count'),
            total_unsubscribed=Sum('unsubscribed_count'),
        )

        total_sent = campaign_stats['total_sent'] or 0
        total_opened = campaign_stats['total_opened'] or 0
        total_clicked = campaign_stats['total_clicked'] or 0
        total_replied = campaign_stats['total_replied'] or 0

        # Calculate rates
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0
        reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0

        # Suppression stats
        suppressed_count = SuppressionList.objects.filter(
            workspace_id=self.workspace_id
        ).count()

        # Hot leads (score >= hot threshold)
        from apps.contacts.models import ScoreThreshold
        try:
            hot_threshold = ScoreThreshold.objects.get(
                workspace_id=self.workspace_id,
                name='hot'
            )
            hot_leads_count = Contact.objects.filter(
                workspace_id=self.workspace_id,
                score__gte=hot_threshold.min_score,
                is_unsubscribed=False
            ).count()
        except ScoreThreshold.DoesNotExist:
            hot_leads_count = Contact.objects.filter(
                workspace_id=self.workspace_id,
                score__gte=70,
                is_unsubscribed=False
            ).count()

        return {
            'contacts': {
                'total': total_contacts,
                'new': new_contacts,
                'active': active_contacts,
                'hot_leads': hot_leads_count,
            },
            'campaigns': {
                'total': total_campaigns,
                'active': active_campaigns,
                'completed': completed_campaigns,
            },
            'emails': {
                'sent': total_sent,
                'delivered': campaign_stats['total_delivered'] or 0,
                'opened': total_opened,
                'clicked': total_clicked,
                'replied': total_replied,
                'bounced': campaign_stats['total_bounced'] or 0,
                'unsubscribed': campaign_stats['total_unsubscribed'] or 0,
            },
            'rates': {
                'open_rate': round(open_rate, 1),
                'click_rate': round(click_rate, 1),
                'reply_rate': round(reply_rate, 1),
            },
            'suppressed': suppressed_count,
            'period_days': days,
        }

    def get_email_stats_over_time(
        self,
        days: int = 30,
        granularity: str = 'day'
    ) -> List[dict]:
        """Get email statistics over time.

        Args:
            days: Number of days to look back
            granularity: 'hour', 'day', 'week', 'month'

        Returns:
            List of stats per time period
        """
        from apps.tracking.models import TrackingEvent

        start_date = timezone.now() - timedelta(days=days)

        # Choose truncation function
        trunc_func = {
            'hour': TruncHour,
            'day': TruncDay,
            'week': TruncWeek,
            'month': TruncMonth,
        }.get(granularity, TruncDay)

        # Get events grouped by time
        events = TrackingEvent.objects.filter(
            campaign_recipient__campaign__workspace_id=self.workspace_id,
            created_at__gte=start_date,
            is_bot=False
        ).annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            opens=Count('id', filter=Q(event_type='open')),
            clicks=Count('id', filter=Q(event_type='click')),
            unsubscribes=Count('id', filter=Q(event_type='unsubscribe')),
            bounces=Count('id', filter=Q(event_type='bounce')),
        ).order_by('period')

        return [
            {
                'date': e['period'].isoformat() if e['period'] else None,
                'opens': e['opens'],
                'clicks': e['clicks'],
                'unsubscribes': e['unsubscribes'],
                'bounces': e['bounces'],
            }
            for e in events
        ]

    # ==================== Campaign Reports ====================

    def get_campaign_report(self, campaign_id: str) -> dict:
        """Get detailed report for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Dict with campaign report data
        """
        from apps.campaigns.models import Campaign, CampaignRecipient
        from apps.tracking.models import TrackingEvent

        campaign = Campaign.objects.get(id=campaign_id, workspace_id=self.workspace_id)

        # Basic stats
        stats = {
            'campaign': {
                'id': str(campaign.id),
                'name': campaign.name,
                'status': campaign.status,
                'created_at': campaign.created_at.isoformat(),
                'started_at': campaign.started_at.isoformat() if campaign.started_at else None,
                'completed_at': campaign.completed_at.isoformat() if campaign.completed_at else None,
            },
            'recipients': {
                'total': campaign.total_recipients,
                'sent': campaign.sent_count,
                'delivered': campaign.delivered_count,
                'pending': CampaignRecipient.objects.filter(
                    campaign=campaign,
                    status__in=['pending', 'queued']
                ).count(),
                'failed': campaign.failed_count,
            },
            'engagement': {
                'opened': campaign.unique_opens,
                'clicked': campaign.unique_clicks,
                'replied': campaign.replied_count,
                'unsubscribed': campaign.unsubscribed_count,
            },
            'deliverability': {
                'bounced': campaign.bounced_count,
                'complained': campaign.complained_count,
            },
            'rates': {
                'delivery_rate': round(
                    (campaign.delivered_count / campaign.sent_count * 100)
                    if campaign.sent_count > 0 else 0, 1
                ),
                'open_rate': campaign.open_rate,
                'click_rate': campaign.click_rate,
                'reply_rate': campaign.reply_rate,
                'bounce_rate': campaign.bounce_rate,
            },
        }

        # A/B test results if applicable
        if campaign.is_ab_test:
            variants = []
            for variant in campaign.ab_variants.all():
                variants.append({
                    'id': str(variant.id),
                    'name': variant.name,
                    'sent': variant.sent_count,
                    'opened': variant.opened_count,
                    'clicked': variant.clicked_count,
                    'open_rate': variant.open_rate,
                    'click_rate': variant.click_rate,
                    'is_winner': variant.is_winner,
                    'is_control': variant.is_control,
                })
            stats['ab_test'] = {
                'variants': variants,
                'winner_criteria': campaign.ab_test_winner_criteria,
            }

        # Timeline of events
        events_timeline = TrackingEvent.objects.filter(
            campaign_recipient__campaign=campaign,
            is_bot=False
        ).annotate(
            hour=TruncHour('created_at')
        ).values('hour').annotate(
            opens=Count('id', filter=Q(event_type='open')),
            clicks=Count('id', filter=Q(event_type='click')),
        ).order_by('hour')

        stats['timeline'] = [
            {
                'time': e['hour'].isoformat() if e['hour'] else None,
                'opens': e['opens'],
                'clicks': e['clicks'],
            }
            for e in events_timeline
        ]

        # Top clicked links
        from apps.tracking.models import TrackingLink
        top_links = TrackingLink.objects.filter(
            campaign_recipient__campaign=campaign
        ).values('original_url').annotate(
            total_clicks=Sum('click_count')
        ).order_by('-total_clicks')[:10]

        stats['top_links'] = [
            {'url': l['original_url'], 'clicks': l['total_clicks']}
            for l in top_links
        ]

        return stats

    def get_campaigns_comparison(
        self,
        campaign_ids: List[str],
    ) -> List[dict]:
        """Compare multiple campaigns.

        Args:
            campaign_ids: List of campaign IDs to compare

        Returns:
            List of campaign stats for comparison
        """
        from apps.campaigns.models import Campaign

        campaigns = Campaign.objects.filter(
            id__in=campaign_ids,
            workspace_id=self.workspace_id
        )

        return [
            {
                'id': str(c.id),
                'name': c.name,
                'status': c.status,
                'sent': c.sent_count,
                'delivered': c.delivered_count,
                'opened': c.unique_opens,
                'clicked': c.unique_clicks,
                'replied': c.replied_count,
                'bounced': c.bounced_count,
                'open_rate': c.open_rate,
                'click_rate': c.click_rate,
                'reply_rate': c.reply_rate,
                'started_at': c.started_at.isoformat() if c.started_at else None,
            }
            for c in campaigns
        ]

    # ==================== Activity Timeline ====================

    def get_activity_timeline(
        self,
        limit: int = 50,
        event_types: Optional[List[str]] = None,
        contact_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> List[dict]:
        """Get activity timeline.

        Args:
            limit: Maximum number of events
            event_types: Filter by event types
            contact_id: Filter by contact
            campaign_id: Filter by campaign

        Returns:
            List of activity events
        """
        from apps.tracking.models import TrackingEvent
        from apps.contacts.models import ContactActivity

        activities = []

        # Get tracking events
        tracking_filter = Q(campaign_recipient__campaign__workspace_id=self.workspace_id)
        if event_types:
            tracking_filter &= Q(event_type__in=event_types)
        if contact_id:
            tracking_filter &= Q(campaign_recipient__contact_id=contact_id)
        if campaign_id:
            tracking_filter &= Q(campaign_recipient__campaign_id=campaign_id)

        tracking_events = TrackingEvent.objects.filter(
            tracking_filter,
            is_bot=False
        ).select_related(
            'campaign_recipient__contact',
            'campaign_recipient__campaign'
        ).order_by('-created_at')[:limit]

        for event in tracking_events:
            activities.append({
                'id': str(event.id),
                'type': event.event_type,
                'contact_id': str(event.campaign_recipient.contact_id),
                'contact_email': event.campaign_recipient.contact.email,
                'contact_name': f"{event.campaign_recipient.contact.first_name} {event.campaign_recipient.contact.last_name}".strip(),
                'campaign_id': str(event.campaign_recipient.campaign_id),
                'campaign_name': event.campaign_recipient.campaign.name,
                'details': {
                    'clicked_url': event.clicked_url if event.event_type == 'click' else None,
                    'device': event.device_type,
                    'location': f"{event.city}, {event.country}" if event.city and event.country else event.country or None,
                },
                'created_at': event.created_at.isoformat(),
            })

        # Sort by date
        activities.sort(key=lambda x: x['created_at'], reverse=True)
        return activities[:limit]

    # ==================== Hot Leads Report ====================

    def get_hot_leads_report(
        self,
        limit: int = 50,
        min_score: Optional[int] = None,
    ) -> dict:
        """Get hot leads report.

        Args:
            limit: Maximum number of leads
            min_score: Minimum score threshold

        Returns:
            Dict with hot leads and stats
        """
        from apps.contacts.models import Contact, ScoreThreshold, ScoreHistory

        # Get threshold if not specified
        if min_score is None:
            try:
                hot_threshold = ScoreThreshold.objects.get(
                    workspace_id=self.workspace_id,
                    name='hot'
                )
                min_score = hot_threshold.min_score
            except ScoreThreshold.DoesNotExist:
                min_score = 70

        # Get hot leads
        hot_leads = Contact.objects.filter(
            workspace_id=self.workspace_id,
            score__gte=min_score,
            is_unsubscribed=False,
            is_bounced=False
        ).order_by('-score', '-updated_at')[:limit]

        leads_data = []
        for contact in hot_leads:
            # Get recent score changes
            recent_history = ScoreHistory.objects.filter(
                contact=contact
            ).order_by('-created_at')[:5]

            score_trend = 'stable'
            if recent_history.count() >= 2:
                scores = [h.new_score for h in recent_history]
                if scores[0] > scores[-1]:
                    score_trend = 'up'
                elif scores[0] < scores[-1]:
                    score_trend = 'down'

            leads_data.append({
                'id': str(contact.id),
                'email': contact.email,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'company': contact.company,
                'score': contact.score,
                'score_trend': score_trend,
                'last_activity_at': contact.last_activity_at.isoformat() if contact.last_activity_at else None,
                'total_opens': contact.total_opens,
                'total_clicks': contact.total_clicks,
                'total_replies': contact.total_replies,
                'created_at': contact.created_at.isoformat(),
            })

        # Score distribution
        all_contacts = Contact.objects.filter(
            workspace_id=self.workspace_id,
            is_unsubscribed=False
        )

        distribution = {
            'hot': all_contacts.filter(score__gte=min_score).count(),
            'warm': all_contacts.filter(score__gte=40, score__lt=min_score).count(),
            'cold': all_contacts.filter(score__lt=40).count(),
        }

        return {
            'leads': leads_data,
            'total_hot_leads': len(leads_data),
            'threshold': min_score,
            'distribution': distribution,
        }

    def get_score_distribution(self) -> dict:
        """Get contact score distribution.

        Returns:
            Dict with score distribution data
        """
        from apps.contacts.models import Contact

        contacts = Contact.objects.filter(
            workspace_id=self.workspace_id,
            is_unsubscribed=False
        )

        # Score ranges
        ranges = [
            (0, 10), (10, 20), (20, 30), (30, 40), (40, 50),
            (50, 60), (60, 70), (70, 80), (80, 90), (90, 100), (100, 1000)
        ]

        distribution = []
        for low, high in ranges:
            count = contacts.filter(score__gte=low, score__lt=high).count()
            label = f"{low}-{high-1}" if high <= 100 else "100+"
            distribution.append({
                'range': label,
                'count': count,
            })

        # Stats
        from django.db.models import Avg, Max, Min
        stats = contacts.aggregate(
            avg_score=Avg('score'),
            max_score=Max('score'),
            min_score=Min('score'),
        )

        return {
            'distribution': distribution,
            'stats': {
                'average': round(stats['avg_score'] or 0, 1),
                'maximum': stats['max_score'] or 0,
                'minimum': stats['min_score'] or 0,
                'total_contacts': contacts.count(),
            }
        }

    # ==================== Export Functions ====================

    def export_campaign_report_csv(self, campaign_id: str) -> str:
        """Export campaign report to CSV.

        Args:
            campaign_id: Campaign ID

        Returns:
            CSV string
        """
        from apps.campaigns.models import CampaignRecipient

        recipients = CampaignRecipient.objects.filter(
            campaign_id=campaign_id,
            campaign__workspace_id=self.workspace_id
        ).select_related('contact')

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Email', 'First Name', 'Last Name', 'Company',
            'Status', 'Sent At', 'Opened At', 'Clicked At',
            'Open Count', 'Click Count'
        ])

        # Data
        for r in recipients:
            writer.writerow([
                r.contact.email,
                r.contact.first_name,
                r.contact.last_name,
                r.contact.company,
                r.status,
                r.sent_at.isoformat() if r.sent_at else '',
                r.opened_at.isoformat() if r.opened_at else '',
                r.clicked_at.isoformat() if r.clicked_at else '',
                r.open_count,
                r.click_count,
            ])

        return output.getvalue()

    def export_contacts_csv(
        self,
        filters: Optional[dict] = None,
        fields: Optional[List[str]] = None
    ) -> str:
        """Export contacts to CSV.

        Args:
            filters: Optional filters
            fields: Fields to include

        Returns:
            CSV string
        """
        from apps.contacts.models import Contact

        queryset = Contact.objects.filter(workspace_id=self.workspace_id)

        if filters:
            if filters.get('tags'):
                queryset = queryset.filter(tags__id__in=filters['tags'])
            if filters.get('score_min'):
                queryset = queryset.filter(score__gte=filters['score_min'])
            if filters.get('score_max'):
                queryset = queryset.filter(score__lte=filters['score_max'])
            if filters.get('is_unsubscribed') is not None:
                queryset = queryset.filter(is_unsubscribed=filters['is_unsubscribed'])

        default_fields = [
            'email', 'first_name', 'last_name', 'company', 'title',
            'phone', 'score', 'is_unsubscribed', 'created_at'
        ]
        fields = fields or default_fields

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([f.replace('_', ' ').title() for f in fields])

        # Data
        for contact in queryset:
            row = []
            for field in fields:
                value = getattr(contact, field, '')
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row.append(value)
            writer.writerow(row)

        return output.getvalue()

    def export_hot_leads_csv(self, min_score: int = 70) -> str:
        """Export hot leads to CSV.

        Args:
            min_score: Minimum score threshold

        Returns:
            CSV string
        """
        from apps.contacts.models import Contact

        contacts = Contact.objects.filter(
            workspace_id=self.workspace_id,
            score__gte=min_score,
            is_unsubscribed=False
        ).order_by('-score')

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Email', 'First Name', 'Last Name', 'Company', 'Title',
            'Score', 'Total Opens', 'Total Clicks', 'Total Replies',
            'Last Activity', 'Created At'
        ])

        for c in contacts:
            writer.writerow([
                c.email,
                c.first_name,
                c.last_name,
                c.company,
                c.title,
                c.score,
                c.total_opens,
                c.total_clicks,
                c.total_replies,
                c.last_activity_at.isoformat() if c.last_activity_at else '',
                c.created_at.isoformat(),
            ])

        return output.getvalue()

    # ==================== Performance Summary ====================

    def get_performance_summary(self, days: int = 7) -> dict:
        """Get performance summary comparing to previous period.

        Args:
            days: Number of days for current period

        Returns:
            Dict with current and previous period stats
        """
        from apps.campaigns.models import Campaign
        from apps.contacts.models import Contact

        now = timezone.now()
        current_start = now - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)

        def get_period_stats(start_date, end_date):
            campaigns = Campaign.objects.filter(
                workspace_id=self.workspace_id,
                started_at__gte=start_date,
                started_at__lt=end_date
            )

            stats = campaigns.aggregate(
                sent=Sum('sent_count'),
                opened=Sum('unique_opens'),
                clicked=Sum('unique_clicks'),
                replied=Sum('replied_count'),
            )

            new_contacts = Contact.objects.filter(
                workspace_id=self.workspace_id,
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count()

            sent = stats['sent'] or 0
            opened = stats['opened'] or 0
            clicked = stats['clicked'] or 0

            return {
                'emails_sent': sent,
                'emails_opened': opened,
                'emails_clicked': clicked,
                'replies': stats['replied'] or 0,
                'new_contacts': new_contacts,
                'open_rate': round((opened / sent * 100) if sent > 0 else 0, 1),
                'click_rate': round((clicked / opened * 100) if opened > 0 else 0, 1),
            }

        current = get_period_stats(current_start, now)
        previous = get_period_stats(previous_start, current_start)

        def calc_change(current_val, previous_val):
            if previous_val == 0:
                return 100 if current_val > 0 else 0
            return round((current_val - previous_val) / previous_val * 100, 1)

        return {
            'current': current,
            'previous': previous,
            'changes': {
                'emails_sent': calc_change(current['emails_sent'], previous['emails_sent']),
                'emails_opened': calc_change(current['emails_opened'], previous['emails_opened']),
                'replies': calc_change(current['replies'], previous['replies']),
                'new_contacts': calc_change(current['new_contacts'], previous['new_contacts']),
                'open_rate': round(current['open_rate'] - previous['open_rate'], 1),
                'click_rate': round(current['click_rate'] - previous['click_rate'], 1),
            },
            'period_days': days,
        }
