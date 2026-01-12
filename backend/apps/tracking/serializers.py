from rest_framework import serializers

from apps.tracking.models import (
    TrackingDomain,
    TrackingLink,
    TrackingPixel,
    TrackingEvent,
    UnsubscribeToken,
    BounceRecord,
    ComplaintRecord,
    SuppressionList,
    WebsiteTrackingScript,
    WebsiteVisitor,
    VisitorSession,
    PageView,
    WebsiteEvent,
    VisitorIdentification,
)


class TrackingDomainSerializer(serializers.ModelSerializer):
    """Serializer for TrackingDomain model."""

    class Meta:
        model = TrackingDomain
        fields = [
            'id',
            'workspace',
            'domain',
            'is_verified',
            'is_default',
            'ssl_enabled',
            'verification_token',
            'verified_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'workspace',
            'is_verified',
            'verification_token',
            'verified_at',
            'created_at',
            'updated_at',
        ]


class TrackingDomainCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TrackingDomain."""

    class Meta:
        model = TrackingDomain
        fields = ['domain', 'ssl_enabled', 'is_default']


class TrackingLinkSerializer(serializers.ModelSerializer):
    """Serializer for TrackingLink model."""

    class Meta:
        model = TrackingLink
        fields = [
            'id',
            'campaign_recipient',
            'token',
            'original_url',
            'click_count',
            'first_clicked_at',
            'last_clicked_at',
            'created_at',
        ]
        read_only_fields = fields


class TrackingPixelSerializer(serializers.ModelSerializer):
    """Serializer for TrackingPixel model."""

    class Meta:
        model = TrackingPixel
        fields = [
            'id',
            'campaign_recipient',
            'token',
            'open_count',
            'first_opened_at',
            'last_opened_at',
            'created_at',
        ]
        read_only_fields = fields


class TrackingEventSerializer(serializers.ModelSerializer):
    """Serializer for TrackingEvent model."""

    class Meta:
        model = TrackingEvent
        fields = [
            'id',
            'event_type',
            'campaign_recipient',
            'tracking_link',
            'clicked_url',
            'bounce_type',
            'bounce_code',
            'bounce_message',
            'ip_address',
            'user_agent',
            'device_type',
            'device_brand',
            'device_model',
            'browser_name',
            'browser_version',
            'os_name',
            'os_version',
            'country',
            'country_code',
            'region',
            'city',
            'is_bot',
            'bot_name',
            'created_at',
        ]
        read_only_fields = fields


class TrackingEventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing TrackingEvents."""

    contact_email = serializers.CharField(
        source='campaign_recipient.contact.email',
        read_only=True
    )
    campaign_name = serializers.CharField(
        source='campaign_recipient.campaign.name',
        read_only=True
    )

    class Meta:
        model = TrackingEvent
        fields = [
            'id',
            'event_type',
            'contact_email',
            'campaign_name',
            'clicked_url',
            'device_type',
            'browser_name',
            'os_name',
            'country',
            'city',
            'is_bot',
            'created_at',
        ]


class UnsubscribeTokenSerializer(serializers.ModelSerializer):
    """Serializer for UnsubscribeToken model."""

    contact_email = serializers.CharField(source='contact.email', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)

    class Meta:
        model = UnsubscribeToken
        fields = [
            'id',
            'contact',
            'contact_email',
            'campaign',
            'campaign_name',
            'token',
            'is_used',
            'used_at',
            'reason',
            'created_at',
        ]
        read_only_fields = fields


class BounceRecordSerializer(serializers.ModelSerializer):
    """Serializer for BounceRecord model."""

    campaign_name = serializers.CharField(
        source='campaign.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = BounceRecord
        fields = [
            'id',
            'email',
            'workspace',
            'email_account',
            'campaign',
            'campaign_name',
            'campaign_recipient',
            'bounce_type',
            'bounce_category',
            'bounce_code',
            'bounce_message',
            'message_id',
            'created_at',
        ]
        read_only_fields = fields


class ComplaintRecordSerializer(serializers.ModelSerializer):
    """Serializer for ComplaintRecord model."""

    campaign_name = serializers.CharField(
        source='campaign.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = ComplaintRecord
        fields = [
            'id',
            'email',
            'workspace',
            'email_account',
            'campaign',
            'campaign_name',
            'campaign_recipient',
            'complaint_type',
            'feedback_id',
            'message_id',
            'created_at',
        ]
        read_only_fields = fields


class SuppressionListSerializer(serializers.ModelSerializer):
    """Serializer for SuppressionList model."""

    class Meta:
        model = SuppressionList
        fields = [
            'id',
            'email',
            'workspace',
            'reason',
            'source',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'workspace', 'created_at']


class SuppressionListCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SuppressionList entries."""

    class Meta:
        model = SuppressionList
        fields = ['email', 'reason', 'source', 'notes']


class TrackingStatsSerializer(serializers.Serializer):
    """Serializer for tracking statistics."""

    total_opens = serializers.IntegerField()
    unique_opens = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    unique_clicks = serializers.IntegerField()
    total_unsubscribes = serializers.IntegerField()
    total_bounces = serializers.IntegerField()
    hard_bounces = serializers.IntegerField()
    soft_bounces = serializers.IntegerField()
    total_complaints = serializers.IntegerField()
    suppressed_count = serializers.IntegerField()
    bot_opens = serializers.IntegerField()
    bot_clicks = serializers.IntegerField()


class DeviceStatsSerializer(serializers.Serializer):
    """Serializer for device breakdown statistics."""

    device_type = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class LocationStatsSerializer(serializers.Serializer):
    """Serializer for location breakdown statistics."""

    country = serializers.CharField()
    country_code = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class BrowserStatsSerializer(serializers.Serializer):
    """Serializer for browser breakdown statistics."""

    browser_name = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


# ==================== Website Tracking Serializers ====================

class WebsiteTrackingScriptSerializer(serializers.ModelSerializer):
    """Serializer for WebsiteTrackingScript model."""

    snippet_url = serializers.SerializerMethodField()
    embed_code = serializers.SerializerMethodField()

    class Meta:
        model = WebsiteTrackingScript
        fields = [
            'id',
            'workspace',
            'script_id',
            'is_enabled',
            'track_page_views',
            'track_clicks',
            'track_forms',
            'track_scroll_depth',
            'track_time_on_page',
            'allowed_domains',
            'award_score_on_visit',
            'visit_score_points',
            'page_view_score_points',
            'session_timeout_minutes',
            'snippet_url',
            'embed_code',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'workspace',
            'script_id',
            'snippet_url',
            'embed_code',
            'created_at',
            'updated_at',
        ]

    def get_snippet_url(self, obj):
        from django.conf import settings
        base_url = getattr(settings, 'TRACKING_BASE_URL', getattr(settings, 'BASE_URL', 'http://localhost:8000'))
        return f"{base_url}/t/w/script/{obj.script_id}.js"

    def get_embed_code(self, obj):
        snippet_url = self.get_snippet_url(obj)
        return f'<script src="{snippet_url}" async></script>'


class WebsiteTrackingScriptUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating WebsiteTrackingScript."""

    class Meta:
        model = WebsiteTrackingScript
        fields = [
            'is_enabled',
            'track_page_views',
            'track_clicks',
            'track_forms',
            'track_scroll_depth',
            'track_time_on_page',
            'allowed_domains',
            'award_score_on_visit',
            'visit_score_points',
            'page_view_score_points',
            'session_timeout_minutes',
        ]


class VisitorSessionSerializer(serializers.ModelSerializer):
    """Serializer for VisitorSession model."""

    class Meta:
        model = VisitorSession
        fields = [
            'id',
            'session_id',
            'started_at',
            'ended_at',
            'is_active',
            'entry_page',
            'referrer',
            'exit_page',
            'utm_source',
            'utm_medium',
            'utm_campaign',
            'page_views',
            'duration_seconds',
            'max_scroll_depth',
            'ip_address',
            'created_at',
        ]
        read_only_fields = fields


class PageViewSerializer(serializers.ModelSerializer):
    """Serializer for PageView model."""

    class Meta:
        model = PageView
        fields = [
            'id',
            'page_url',
            'page_path',
            'page_title',
            'referrer',
            'time_on_page',
            'scroll_depth',
            'created_at',
        ]
        read_only_fields = fields


class WebsiteEventSerializer(serializers.ModelSerializer):
    """Serializer for WebsiteEvent model."""

    class Meta:
        model = WebsiteEvent
        fields = [
            'id',
            'event_type',
            'event_name',
            'page_url',
            'page_path',
            'element_id',
            'element_class',
            'element_text',
            'target_url',
            'properties',
            'created_at',
        ]
        read_only_fields = fields


class WebsiteVisitorSerializer(serializers.ModelSerializer):
    """Serializer for WebsiteVisitor model."""

    contact_email = serializers.CharField(source='contact.email', read_only=True, allow_null=True)
    contact_name = serializers.SerializerMethodField()
    recent_sessions = VisitorSessionSerializer(many=True, read_only=True, source='sessions')

    class Meta:
        model = WebsiteVisitor
        fields = [
            'id',
            'visitor_id',
            'contact',
            'contact_email',
            'contact_name',
            'is_identified',
            'identified_at',
            'identification_method',
            'first_seen_at',
            'first_page_url',
            'first_referrer',
            'last_seen_at',
            'last_page_url',
            'utm_source',
            'utm_medium',
            'utm_campaign',
            'utm_term',
            'utm_content',
            'device_type',
            'browser_name',
            'browser_version',
            'os_name',
            'os_version',
            'screen_resolution',
            'ip_address',
            'country',
            'country_code',
            'region',
            'city',
            'timezone',
            'company_name',
            'company_domain',
            'company_industry',
            'company_size',
            'total_sessions',
            'total_page_views',
            'total_time_on_site',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_contact_name(self, obj):
        if obj.contact:
            return obj.contact.full_name
        return None


class WebsiteVisitorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing visitors."""

    contact_email = serializers.CharField(source='contact.email', read_only=True, allow_null=True)
    contact_name = serializers.SerializerMethodField()

    class Meta:
        model = WebsiteVisitor
        fields = [
            'id',
            'visitor_id',
            'contact',
            'contact_email',
            'contact_name',
            'is_identified',
            'first_seen_at',
            'last_seen_at',
            'device_type',
            'country',
            'city',
            'company_name',
            'total_sessions',
            'total_page_views',
            'total_time_on_site',
        ]

    def get_contact_name(self, obj):
        if obj.contact:
            return obj.contact.full_name
        return None


class WebsiteVisitorDetailSerializer(WebsiteVisitorSerializer):
    """Detailed serializer for WebsiteVisitor with related data."""

    sessions = VisitorSessionSerializer(many=True, read_only=True)
    recent_page_views = serializers.SerializerMethodField()
    recent_events = serializers.SerializerMethodField()

    class Meta(WebsiteVisitorSerializer.Meta):
        fields = WebsiteVisitorSerializer.Meta.fields + [
            'sessions',
            'recent_page_views',
            'recent_events',
        ]

    def get_recent_page_views(self, obj):
        page_views = obj.page_views.order_by('-created_at')[:10]
        return PageViewSerializer(page_views, many=True).data

    def get_recent_events(self, obj):
        events = obj.events.order_by('-created_at')[:10]
        return WebsiteEventSerializer(events, many=True).data


class VisitorIdentificationSerializer(serializers.ModelSerializer):
    """Serializer for VisitorIdentification model."""

    class Meta:
        model = VisitorIdentification
        fields = [
            'id',
            'visitor',
            'contact',
            'method',
            'email',
            'source',
            'metadata',
            'created_at',
        ]
        read_only_fields = fields


class WebsiteTrackingStatsSerializer(serializers.Serializer):
    """Serializer for website tracking statistics."""

    total_visitors = serializers.IntegerField()
    identified_visitors = serializers.IntegerField()
    anonymous_visitors = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    total_page_views = serializers.IntegerField()
    average_session_duration = serializers.FloatField()
    average_pages_per_session = serializers.FloatField()
    bounce_rate = serializers.FloatField()
    new_visitors_today = serializers.IntegerField()
    returning_visitors_today = serializers.IntegerField()
