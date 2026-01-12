from django.contrib import admin

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


@admin.register(TrackingDomain)
class TrackingDomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'workspace', 'is_verified', 'is_default', 'created_at']
    list_filter = ['is_verified', 'is_default']
    search_fields = ['domain', 'workspace__name']
    readonly_fields = ['verification_token', 'verified_at', 'created_at', 'updated_at']


@admin.register(TrackingLink)
class TrackingLinkAdmin(admin.ModelAdmin):
    list_display = ['token', 'original_url', 'click_count', 'first_clicked_at', 'created_at']
    list_filter = ['created_at']
    search_fields = ['token', 'original_url']
    readonly_fields = ['token', 'click_count', 'first_clicked_at', 'last_clicked_at', 'created_at']


@admin.register(TrackingPixel)
class TrackingPixelAdmin(admin.ModelAdmin):
    list_display = ['token', 'campaign_recipient', 'open_count', 'first_opened_at', 'created_at']
    list_filter = ['created_at']
    search_fields = ['token']
    readonly_fields = ['token', 'open_count', 'first_opened_at', 'last_opened_at', 'created_at']


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'campaign_recipient', 'device_type', 'country', 'is_bot', 'created_at']
    list_filter = ['event_type', 'is_bot', 'device_type', 'created_at']
    search_fields = ['campaign_recipient__contact__email', 'ip_address']
    readonly_fields = ['created_at']


@admin.register(UnsubscribeToken)
class UnsubscribeTokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'contact', 'campaign', 'is_used', 'used_at', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['token', 'contact__email']
    readonly_fields = ['token', 'used_at', 'created_at']


@admin.register(BounceRecord)
class BounceRecordAdmin(admin.ModelAdmin):
    list_display = ['email', 'bounce_type', 'bounce_category', 'workspace', 'created_at']
    list_filter = ['bounce_type', 'bounce_category', 'created_at']
    search_fields = ['email', 'bounce_message']
    readonly_fields = ['created_at']


@admin.register(ComplaintRecord)
class ComplaintRecordAdmin(admin.ModelAdmin):
    list_display = ['email', 'complaint_type', 'workspace', 'created_at']
    list_filter = ['complaint_type', 'created_at']
    search_fields = ['email']
    readonly_fields = ['created_at']


@admin.register(SuppressionList)
class SuppressionListAdmin(admin.ModelAdmin):
    list_display = ['email', 'reason', 'source', 'workspace', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['email', 'source']
    readonly_fields = ['created_at']


@admin.register(WebsiteTrackingScript)
class WebsiteTrackingScriptAdmin(admin.ModelAdmin):
    list_display = ['script_id', 'workspace', 'is_enabled', 'track_page_views', 'created_at']
    list_filter = ['is_enabled', 'track_page_views', 'track_clicks']
    search_fields = ['script_id', 'workspace__name']
    readonly_fields = ['script_id', 'created_at', 'updated_at']


@admin.register(WebsiteVisitor)
class WebsiteVisitorAdmin(admin.ModelAdmin):
    list_display = [
        'visitor_id', 'workspace', 'contact', 'is_identified',
        'total_sessions', 'total_page_views', 'last_seen_at'
    ]
    list_filter = ['is_identified', 'device_type', 'country', 'created_at']
    search_fields = ['visitor_id', 'contact__email', 'company_name', 'ip_address']
    readonly_fields = [
        'visitor_id', 'first_seen_at', 'identified_at',
        'total_sessions', 'total_page_views', 'created_at', 'updated_at'
    ]


@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_id', 'visitor', 'is_active', 'page_views',
        'duration_seconds', 'started_at', 'ended_at'
    ]
    list_filter = ['is_active', 'started_at']
    search_fields = ['session_id', 'visitor__visitor_id']
    readonly_fields = ['session_id', 'started_at', 'created_at']


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['page_path', 'visitor', 'session', 'time_on_page', 'created_at']
    list_filter = ['created_at']
    search_fields = ['page_url', 'page_path', 'page_title']
    readonly_fields = ['created_at']


@admin.register(WebsiteEvent)
class WebsiteEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'event_name', 'visitor', 'page_path', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['event_name', 'page_url', 'element_id']
    readonly_fields = ['created_at']


@admin.register(VisitorIdentification)
class VisitorIdentificationAdmin(admin.ModelAdmin):
    list_display = ['visitor', 'contact', 'method', 'email', 'source', 'created_at']
    list_filter = ['method', 'created_at']
    search_fields = ['email', 'source']
    readonly_fields = ['created_at']
