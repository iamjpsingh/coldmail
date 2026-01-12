import secrets
from django.db import models

from apps.core.models import BaseModel


def generate_token():
    """Generate a unique tracking token."""
    return secrets.token_urlsafe(32)


class TrackingDomain(BaseModel):
    """Custom tracking domain configuration."""

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='tracking_domains'
    )
    domain = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    ssl_enabled = models.BooleanField(default=True)
    verification_token = models.CharField(max_length=64, default=generate_token)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tracking_domains'
        unique_together = ['workspace', 'domain']

    def __str__(self):
        return self.domain


class TrackingLink(BaseModel):
    """Tracked link for click tracking."""

    campaign_recipient = models.ForeignKey(
        'campaigns.CampaignRecipient',
        on_delete=models.CASCADE,
        related_name='tracking_links'
    )
    token = models.CharField(max_length=64, unique=True, default=generate_token)
    original_url = models.URLField(max_length=2048)
    click_count = models.IntegerField(default=0)
    first_clicked_at = models.DateTimeField(null=True, blank=True)
    last_clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tracking_links'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['campaign_recipient']),
        ]

    def __str__(self):
        return f"{self.token[:8]}... -> {self.original_url[:50]}"


class TrackingPixel(BaseModel):
    """Tracking pixel for open tracking."""

    campaign_recipient = models.OneToOneField(
        'campaigns.CampaignRecipient',
        on_delete=models.CASCADE,
        related_name='tracking_pixel'
    )
    token = models.CharField(max_length=64, unique=True, default=generate_token)
    open_count = models.IntegerField(default=0)
    first_opened_at = models.DateTimeField(null=True, blank=True)
    last_opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tracking_pixels'
        indexes = [
            models.Index(fields=['token']),
        ]

    def __str__(self):
        return f"Pixel {self.token[:8]}..."


class UnsubscribeToken(BaseModel):
    """Unsubscribe token for one-click unsubscribe."""

    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.CASCADE,
        related_name='unsubscribe_tokens'
    )
    campaign = models.ForeignKey(
        'campaigns.Campaign',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='unsubscribe_tokens'
    )
    token = models.CharField(max_length=64, unique=True, default=generate_token)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = 'unsubscribe_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['contact']),
        ]

    def __str__(self):
        return f"Unsubscribe {self.token[:8]}..."


class TrackingEvent(BaseModel):
    """Individual tracking event with full details."""

    class EventType(models.TextChoices):
        OPEN = 'open', 'Email Opened'
        CLICK = 'click', 'Link Clicked'
        UNSUBSCRIBE = 'unsubscribe', 'Unsubscribed'
        BOUNCE = 'bounce', 'Bounced'
        COMPLAINT = 'complaint', 'Spam Complaint'
        DELIVERY = 'delivery', 'Delivered'

    class BounceType(models.TextChoices):
        HARD = 'hard', 'Hard Bounce'
        SOFT = 'soft', 'Soft Bounce'
        COMPLAINT = 'complaint', 'Complaint'

    # Core fields
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    campaign_recipient = models.ForeignKey(
        'campaigns.CampaignRecipient',
        on_delete=models.CASCADE,
        related_name='tracking_events'
    )

    # For click events
    tracking_link = models.ForeignKey(
        TrackingLink,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    clicked_url = models.URLField(max_length=2048, blank=True)

    # For bounce events
    bounce_type = models.CharField(
        max_length=20,
        choices=BounceType.choices,
        blank=True
    )
    bounce_code = models.CharField(max_length=10, blank=True)
    bounce_message = models.TextField(blank=True)

    # Request info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Parsed device info
    device_type = models.CharField(max_length=50, blank=True)  # desktop, mobile, tablet
    device_brand = models.CharField(max_length=100, blank=True)
    device_model = models.CharField(max_length=100, blank=True)
    browser_name = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    os_name = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=50, blank=True)

    # Geo info (from IP)
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timezone = models.CharField(max_length=50, blank=True)

    # Bot detection
    is_bot = models.BooleanField(default=False)
    bot_name = models.CharField(max_length=100, blank=True)

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tracking_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['campaign_recipient', '-created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.campaign_recipient}"


class BounceRecord(BaseModel):
    """Record of email bounces for deliverability tracking."""

    class BounceType(models.TextChoices):
        HARD = 'hard', 'Hard Bounce'
        SOFT = 'soft', 'Soft Bounce'

    class BounceCategory(models.TextChoices):
        INVALID = 'invalid', 'Invalid Address'
        MAILBOX_FULL = 'mailbox_full', 'Mailbox Full'
        BLOCKED = 'blocked', 'Blocked'
        CONTENT = 'content', 'Content Blocked'
        TIMEOUT = 'timeout', 'Connection Timeout'
        OTHER = 'other', 'Other'

    email = models.EmailField()
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='bounce_records'
    )
    email_account = models.ForeignKey(
        'email_accounts.EmailAccount',
        on_delete=models.SET_NULL,
        null=True,
        related_name='bounce_records'
    )
    campaign = models.ForeignKey(
        'campaigns.Campaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bounce_records'
    )
    campaign_recipient = models.ForeignKey(
        'campaigns.CampaignRecipient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bounce_records'
    )

    bounce_type = models.CharField(max_length=20, choices=BounceType.choices)
    bounce_category = models.CharField(
        max_length=20,
        choices=BounceCategory.choices,
        default=BounceCategory.OTHER
    )
    bounce_code = models.CharField(max_length=10, blank=True)
    bounce_message = models.TextField(blank=True)
    message_id = models.CharField(max_length=255, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'bounce_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['workspace', '-created_at']),
        ]

    def __str__(self):
        return f"Bounce: {self.email} ({self.bounce_type})"


class ComplaintRecord(BaseModel):
    """Record of spam complaints."""

    class ComplaintType(models.TextChoices):
        SPAM = 'spam', 'Marked as Spam'
        ABUSE = 'abuse', 'Abuse Report'
        OTHER = 'other', 'Other'

    email = models.EmailField()
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='complaint_records'
    )
    email_account = models.ForeignKey(
        'email_accounts.EmailAccount',
        on_delete=models.SET_NULL,
        null=True,
        related_name='complaint_records'
    )
    campaign = models.ForeignKey(
        'campaigns.Campaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaint_records'
    )
    campaign_recipient = models.ForeignKey(
        'campaigns.CampaignRecipient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaint_records'
    )

    complaint_type = models.CharField(
        max_length=20,
        choices=ComplaintType.choices,
        default=ComplaintType.SPAM
    )
    feedback_id = models.CharField(max_length=255, blank=True)
    message_id = models.CharField(max_length=255, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'complaint_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['workspace', '-created_at']),
        ]

    def __str__(self):
        return f"Complaint: {self.email}"


class SuppressionList(BaseModel):
    """Global suppression list for emails that should never be contacted."""

    class Reason(models.TextChoices):
        HARD_BOUNCE = 'hard_bounce', 'Hard Bounce'
        COMPLAINT = 'complaint', 'Spam Complaint'
        UNSUBSCRIBE = 'unsubscribe', 'Unsubscribed'
        MANUAL = 'manual', 'Manually Added'

    email = models.EmailField()
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='suppression_list'
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    source = models.CharField(max_length=100, blank=True)  # campaign name, import, etc.
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'suppression_list'
        unique_together = ['workspace', 'email']
        ordering = ['-created_at']

    def __str__(self):
        return f"Suppressed: {self.email}"


# Website Tracking Models

class WebsiteTrackingScript(BaseModel):
    """JavaScript tracking script configuration for a workspace."""

    workspace = models.OneToOneField(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='tracking_script'
    )
    script_id = models.CharField(max_length=32, unique=True, default=generate_token)
    is_enabled = models.BooleanField(default=True)

    # Script configuration
    track_page_views = models.BooleanField(default=True)
    track_clicks = models.BooleanField(default=True)
    track_forms = models.BooleanField(default=False)
    track_scroll_depth = models.BooleanField(default=False)
    track_time_on_page = models.BooleanField(default=True)

    # Allowed domains (comma-separated, or * for all)
    allowed_domains = models.TextField(default='*')

    # Score awarding
    award_score_on_visit = models.BooleanField(default=True)
    visit_score_points = models.IntegerField(default=5)
    page_view_score_points = models.IntegerField(default=1)

    # Session configuration
    session_timeout_minutes = models.IntegerField(default=30)

    class Meta:
        db_table = 'website_tracking_scripts'

    def __str__(self):
        return f"Tracking Script: {self.script_id[:8]}..."

    @property
    def allowed_domains_list(self):
        if self.allowed_domains == '*':
            return ['*']
        return [d.strip() for d in self.allowed_domains.split(',') if d.strip()]


class WebsiteVisitor(BaseModel):
    """A visitor to the website, identified by a unique visitor ID."""

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='website_visitors'
    )
    visitor_id = models.CharField(max_length=64, db_index=True)  # Client-side cookie ID

    # Matched contact (if identified)
    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='website_visitors'
    )
    is_identified = models.BooleanField(default=False)
    identified_at = models.DateTimeField(null=True, blank=True)
    identification_method = models.CharField(max_length=50, blank=True)  # email_link, form, api

    # First seen info
    first_seen_at = models.DateTimeField(auto_now_add=True)
    first_page_url = models.URLField(max_length=2048, blank=True)
    first_referrer = models.URLField(max_length=2048, blank=True)

    # Last seen info
    last_seen_at = models.DateTimeField(auto_now=True)
    last_page_url = models.URLField(max_length=2048, blank=True)

    # UTM parameters (from first visit)
    utm_source = models.CharField(max_length=255, blank=True)
    utm_medium = models.CharField(max_length=255, blank=True)
    utm_campaign = models.CharField(max_length=255, blank=True)
    utm_term = models.CharField(max_length=255, blank=True)
    utm_content = models.CharField(max_length=255, blank=True)

    # Device info
    device_type = models.CharField(max_length=50, blank=True)
    browser_name = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    os_name = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    screen_resolution = models.CharField(max_length=20, blank=True)

    # Geo info (from IP)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, blank=True)

    # Company enrichment (if identified by IP)
    company_name = models.CharField(max_length=255, blank=True)
    company_domain = models.CharField(max_length=255, blank=True)
    company_industry = models.CharField(max_length=255, blank=True)
    company_size = models.CharField(max_length=50, blank=True)

    # Engagement stats
    total_sessions = models.IntegerField(default=0)
    total_page_views = models.IntegerField(default=0)
    total_time_on_site = models.IntegerField(default=0)  # seconds

    class Meta:
        db_table = 'website_visitors'
        unique_together = ['workspace', 'visitor_id']
        ordering = ['-last_seen_at']
        indexes = [
            models.Index(fields=['workspace', 'is_identified']),
            models.Index(fields=['workspace', '-last_seen_at']),
            models.Index(fields=['contact']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        if self.contact:
            return f"Visitor: {self.contact.email}"
        return f"Visitor: {self.visitor_id[:8]}..."


class VisitorSession(BaseModel):
    """A browsing session for a visitor."""

    visitor = models.ForeignKey(
        WebsiteVisitor,
        on_delete=models.CASCADE,
        related_name='sessions'
    )

    # Session info
    session_id = models.CharField(max_length=64, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Entry info
    entry_page = models.URLField(max_length=2048)
    referrer = models.URLField(max_length=2048, blank=True)

    # Exit info
    exit_page = models.URLField(max_length=2048, blank=True)

    # UTM for this session
    utm_source = models.CharField(max_length=255, blank=True)
    utm_medium = models.CharField(max_length=255, blank=True)
    utm_campaign = models.CharField(max_length=255, blank=True)

    # Session stats
    page_views = models.IntegerField(default=0)
    duration_seconds = models.IntegerField(default=0)
    max_scroll_depth = models.IntegerField(default=0)  # 0-100%

    # Request info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'visitor_sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['visitor', '-started_at']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"Session {self.session_id[:8]}..."


class PageView(BaseModel):
    """A single page view event."""

    visitor = models.ForeignKey(
        WebsiteVisitor,
        on_delete=models.CASCADE,
        related_name='page_views'
    )
    session = models.ForeignKey(
        VisitorSession,
        on_delete=models.CASCADE,
        related_name='page_view_events'
    )

    # Page info
    page_url = models.URLField(max_length=2048)
    page_path = models.CharField(max_length=2048)
    page_title = models.CharField(max_length=512, blank=True)

    # Referrer
    referrer = models.URLField(max_length=2048, blank=True)

    # Timing
    time_on_page = models.IntegerField(default=0)  # seconds
    scroll_depth = models.IntegerField(default=0)  # 0-100%

    # Request info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'page_views'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['visitor', '-created_at']),
            models.Index(fields=['session']),
            models.Index(fields=['page_path']),
        ]

    def __str__(self):
        return f"PageView: {self.page_path}"


class WebsiteEvent(BaseModel):
    """Custom events tracked on the website."""

    class EventType(models.TextChoices):
        PAGE_VIEW = 'page_view', 'Page View'
        CLICK = 'click', 'Click'
        FORM_SUBMIT = 'form_submit', 'Form Submit'
        FORM_START = 'form_start', 'Form Start'
        SCROLL = 'scroll', 'Scroll'
        VIDEO_PLAY = 'video_play', 'Video Play'
        VIDEO_COMPLETE = 'video_complete', 'Video Complete'
        DOWNLOAD = 'download', 'Download'
        OUTBOUND_LINK = 'outbound_link', 'Outbound Link'
        CUSTOM = 'custom', 'Custom Event'

    visitor = models.ForeignKey(
        WebsiteVisitor,
        on_delete=models.CASCADE,
        related_name='events'
    )
    session = models.ForeignKey(
        VisitorSession,
        on_delete=models.CASCADE,
        related_name='events'
    )

    event_type = models.CharField(max_length=30, choices=EventType.choices)
    event_name = models.CharField(max_length=100, blank=True)  # For custom events

    # Page where event occurred
    page_url = models.URLField(max_length=2048)
    page_path = models.CharField(max_length=2048)

    # Event data
    element_id = models.CharField(max_length=255, blank=True)
    element_class = models.CharField(max_length=255, blank=True)
    element_text = models.CharField(max_length=512, blank=True)
    target_url = models.URLField(max_length=2048, blank=True)  # For link clicks

    # Custom properties
    properties = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'website_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['visitor', '-created_at']),
            models.Index(fields=['session']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.event_name or self.page_path}"


class VisitorIdentification(BaseModel):
    """Records of how visitors were identified."""

    class Method(models.TextChoices):
        EMAIL_LINK = 'email_link', 'Email Link Click'
        FORM_SUBMIT = 'form_submit', 'Form Submission'
        API = 'api', 'API Call'
        MANUAL = 'manual', 'Manual Identification'
        IP_MATCH = 'ip_match', 'IP Address Match'

    visitor = models.ForeignKey(
        WebsiteVisitor,
        on_delete=models.CASCADE,
        related_name='identifications'
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.CASCADE,
        related_name='visitor_identifications'
    )

    method = models.CharField(max_length=20, choices=Method.choices)
    email = models.EmailField()
    source = models.CharField(max_length=255, blank=True)  # campaign, form name, etc.
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'visitor_identifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.visitor} -> {self.contact.email}"
