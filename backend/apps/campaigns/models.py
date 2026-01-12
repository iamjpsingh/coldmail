from django.db import models

from apps.core.models import BaseModel


class EmailSignature(BaseModel):
    """Email signature for outgoing emails."""

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='signatures'
    )
    name = models.CharField(max_length=100)
    content_html = models.TextField(blank=True)
    content_text = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'email_signatures'
        ordering = ['-is_default', 'name']
        unique_together = ['workspace', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # If this is set as default, unset other defaults
        if self.is_default:
            EmailSignature.objects.filter(
                workspace=self.workspace,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class EmailTemplate(BaseModel):
    """Email template for campaigns and sequences."""

    class Category(models.TextChoices):
        OUTREACH = 'outreach', 'Cold Outreach'
        FOLLOWUP = 'followup', 'Follow-up'
        NURTURE = 'nurture', 'Nurture'
        PROMOTIONAL = 'promotional', 'Promotional'
        TRANSACTIONAL = 'transactional', 'Transactional'
        OTHER = 'other', 'Other'

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='email_templates'
    )
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=500)
    content_html = models.TextField()
    content_text = models.TextField(blank=True)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OUTREACH
    )
    description = models.TextField(blank=True)

    # Signature
    signature = models.ForeignKey(
        EmailSignature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates'
    )
    include_signature = models.BooleanField(default=True)

    # Template metadata
    variables = models.JSONField(default=list, blank=True)  # Detected variables
    has_spintax = models.BooleanField(default=False)

    # Usage tracking
    times_used = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Sharing
    is_shared = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )

    class Meta:
        db_table = 'email_templates'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def increment_usage(self):
        """Increment usage counter."""
        from django.utils import timezone
        self.times_used += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['times_used', 'last_used_at'])


class TemplateFolder(BaseModel):
    """Folder for organizing templates."""

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='template_folders'
    )
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    color = models.CharField(max_length=7, default='#6366f1')  # Hex color
    templates = models.ManyToManyField(
        EmailTemplate,
        blank=True,
        related_name='folders'
    )

    class Meta:
        db_table = 'template_folders'
        ordering = ['name']
        unique_together = ['workspace', 'name', 'parent']

    def __str__(self):
        return self.name


class TemplateVersion(BaseModel):
    """Version history for templates."""

    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.PositiveIntegerField()
    subject = models.CharField(max_length=500)
    content_html = models.TextField()
    content_text = models.TextField(blank=True)
    change_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='template_versions'
    )

    class Meta:
        db_table = 'template_versions'
        ordering = ['-version_number']
        unique_together = ['template', 'version_number']

    def __str__(self):
        return f"{self.template.name} v{self.version_number}"


class SnippetLibrary(BaseModel):
    """Reusable text snippets for templates."""

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='snippets'
    )
    name = models.CharField(max_length=100)
    shortcode = models.CharField(max_length=50)  # e.g., "intro", "cta"
    content_html = models.TextField()
    content_text = models.TextField(blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    times_used = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'snippet_library'
        ordering = ['category', 'name']
        unique_together = ['workspace', 'shortcode']

    def __str__(self):
        return f"{self.shortcode}: {self.name}"


class Campaign(BaseModel):
    """Email campaign for sending to contacts."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        SENDING = 'sending', 'Sending'
        PAUSED = 'paused', 'Paused'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    class SendingMode(models.TextChoices):
        IMMEDIATE = 'immediate', 'Send Immediately'
        SCHEDULED = 'scheduled', 'Schedule for Later'
        SPREAD = 'spread', 'Spread Across Time Window'

    # Basic info
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='campaigns'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    # Email content
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns'
    )
    subject = models.CharField(max_length=500)
    content_html = models.TextField()
    content_text = models.TextField(blank=True)

    # Sender
    email_account = models.ForeignKey(
        'email_accounts.EmailAccount',
        on_delete=models.SET_NULL,
        null=True,
        related_name='campaigns'
    )
    from_name = models.CharField(max_length=255, blank=True)
    reply_to = models.EmailField(blank=True)

    # Recipients selection
    contact_lists = models.ManyToManyField(
        'contacts.ContactList',
        blank=True,
        related_name='campaigns'
    )
    contact_tags = models.ManyToManyField(
        'contacts.Tag',
        blank=True,
        related_name='campaigns'
    )
    exclude_lists = models.ManyToManyField(
        'contacts.ContactList',
        blank=True,
        related_name='excluded_campaigns'
    )
    exclude_tags = models.ManyToManyField(
        'contacts.Tag',
        blank=True,
        related_name='excluded_campaigns'
    )

    # Sending settings
    sending_mode = models.CharField(
        max_length=20,
        choices=SendingMode.choices,
        default=SendingMode.IMMEDIATE
    )

    # Delays
    min_delay_seconds = models.IntegerField(default=30)  # Min delay between emails
    max_delay_seconds = models.IntegerField(default=120)  # Max delay between emails
    batch_size = models.IntegerField(default=50)  # Emails per batch
    batch_delay_minutes = models.IntegerField(default=15)  # Delay between batches

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')

    # Spread sending (time window)
    spread_start_time = models.TimeField(null=True, blank=True)  # e.g., 09:00
    spread_end_time = models.TimeField(null=True, blank=True)  # e.g., 17:00
    spread_days = models.JSONField(default=list, blank=True)  # e.g., [0,1,2,3,4] for Mon-Fri

    # A/B Testing
    is_ab_test = models.BooleanField(default=False)
    ab_test_winner_criteria = models.CharField(max_length=20, blank=True)  # open_rate, click_rate
    ab_test_sample_size = models.IntegerField(default=20)  # % of recipients for testing
    ab_test_duration_hours = models.IntegerField(default=4)  # Hours before selecting winner

    # Tracking
    track_opens = models.BooleanField(default=True)
    track_clicks = models.BooleanField(default=True)
    use_custom_tracking_domain = models.BooleanField(default=False)
    tracking_domain = models.CharField(max_length=255, blank=True)

    # Unsubscribe
    include_unsubscribe_link = models.BooleanField(default=True)

    # Statistics
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    replied_count = models.IntegerField(default=0)
    bounced_count = models.IntegerField(default=0)
    unsubscribed_count = models.IntegerField(default=0)
    complained_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)

    # Unique metrics (unique recipients who performed action)
    unique_opens = models.IntegerField(default=0)
    unique_clicks = models.IntegerField(default=0)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)

    # Created by
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_campaigns'
    )

    class Meta:
        db_table = 'campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def open_rate(self):
        if self.sent_count == 0:
            return 0
        return round((self.unique_opens / self.sent_count) * 100, 1)

    @property
    def click_rate(self):
        if self.sent_count == 0:
            return 0
        return round((self.unique_clicks / self.sent_count) * 100, 1)

    @property
    def reply_rate(self):
        if self.sent_count == 0:
            return 0
        return round((self.replied_count / self.sent_count) * 100, 1)

    @property
    def bounce_rate(self):
        if self.sent_count == 0:
            return 0
        return round((self.bounced_count / self.sent_count) * 100, 1)

    @property
    def progress_percentage(self):
        if self.total_recipients == 0:
            return 0
        return round((self.sent_count / self.total_recipients) * 100, 1)


class ABTestVariant(BaseModel):
    """A/B test variant for a campaign."""

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='ab_variants'
    )
    name = models.CharField(max_length=100)  # e.g., "Variant A", "Variant B"
    subject = models.CharField(max_length=500)
    content_html = models.TextField()
    content_text = models.TextField(blank=True)

    # Statistics
    sent_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    replied_count = models.IntegerField(default=0)

    # Winner status
    is_winner = models.BooleanField(default=False)
    is_control = models.BooleanField(default=False)

    class Meta:
        db_table = 'campaign_ab_variants'
        ordering = ['name']

    def __str__(self):
        return f"{self.campaign.name} - {self.name}"

    @property
    def open_rate(self):
        if self.sent_count == 0:
            return 0
        return round((self.opened_count / self.sent_count) * 100, 1)

    @property
    def click_rate(self):
        if self.sent_count == 0:
            return 0
        return round((self.clicked_count / self.sent_count) * 100, 1)


class CampaignRecipient(BaseModel):
    """Recipient in a campaign."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        QUEUED = 'queued', 'Queued'
        SENDING = 'sending', 'Sending'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        OPENED = 'opened', 'Opened'
        CLICKED = 'clicked', 'Clicked'
        REPLIED = 'replied', 'Replied'
        BOUNCED = 'bounced', 'Bounced'
        FAILED = 'failed', 'Failed'
        UNSUBSCRIBED = 'unsubscribed', 'Unsubscribed'
        COMPLAINED = 'complained', 'Complained'
        SKIPPED = 'skipped', 'Skipped'

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='recipients'
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.CASCADE,
        related_name='campaign_recipients'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    status_reason = models.TextField(blank=True)

    # A/B Test assignment
    ab_variant = models.ForeignKey(
        ABTestVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipients'
    )

    # Personalized content (rendered from template)
    rendered_subject = models.CharField(max_length=500, blank=True)
    rendered_html = models.TextField(blank=True)
    rendered_text = models.TextField(blank=True)

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    send_after = models.DateTimeField(null=True, blank=True)

    # Timing
    queued_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    # Engagement metrics
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)

    # Email details
    message_id = models.CharField(max_length=255, blank=True)
    email_account = models.ForeignKey(
        'email_accounts.EmailAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_emails'
    )

    # Error tracking
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        db_table = 'campaign_recipients'
        unique_together = ['campaign', 'contact']
        ordering = ['scheduled_at', 'created_at']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['campaign', 'scheduled_at']),
            models.Index(fields=['status', 'scheduled_at']),
        ]

    def __str__(self):
        return f"{self.campaign.name} -> {self.contact.email}"


class CampaignEvent(BaseModel):
    """Events/activities for campaign recipients."""

    class EventType(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        OPENED = 'opened', 'Opened'
        CLICKED = 'clicked', 'Clicked'
        REPLIED = 'replied', 'Replied'
        BOUNCED = 'bounced', 'Bounced'
        UNSUBSCRIBED = 'unsubscribed', 'Unsubscribed'
        COMPLAINED = 'complained', 'Complained'
        FAILED = 'failed', 'Failed'

    recipient = models.ForeignKey(
        CampaignRecipient,
        on_delete=models.CASCADE,
        related_name='events'
    )
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices
    )

    # Event details
    metadata = models.JSONField(default=dict, blank=True)

    # For click events
    clicked_url = models.URLField(blank=True)

    # Device/location info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    # Bot detection
    is_bot = models.BooleanField(default=False)

    class Meta:
        db_table = 'campaign_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.recipient} - {self.event_type}"


class CampaignLog(BaseModel):
    """Audit log for campaign operations."""

    class LogType(models.TextChoices):
        CREATED = 'created', 'Campaign Created'
        UPDATED = 'updated', 'Campaign Updated'
        STARTED = 'started', 'Sending Started'
        PAUSED = 'paused', 'Sending Paused'
        RESUMED = 'resumed', 'Sending Resumed'
        COMPLETED = 'completed', 'Sending Completed'
        CANCELLED = 'cancelled', 'Campaign Cancelled'
        ERROR = 'error', 'Error Occurred'
        RECIPIENTS_ADDED = 'recipients_added', 'Recipients Added'
        AB_WINNER = 'ab_winner', 'A/B Test Winner Selected'

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    log_type = models.CharField(
        max_length=30,
        choices=LogType.choices
    )
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'campaign_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.campaign.name} - {self.log_type}"
