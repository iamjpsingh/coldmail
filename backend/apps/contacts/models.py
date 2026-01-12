from django.db import models

from apps.core.models import BaseModel


class Tag(BaseModel):
    """Tag for categorizing contacts."""

    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6366f1')  # Hex color
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='tags'
    )

    class Meta:
        unique_together = ['name', 'workspace']
        ordering = ['name']

    def __str__(self):
        return self.name


class Contact(BaseModel):
    """Contact model with custom fields support."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        UNSUBSCRIBED = 'unsubscribed', 'Unsubscribed'
        BOUNCED = 'bounced', 'Bounced'
        COMPLAINED = 'complained', 'Complained'

    # Core fields
    email = models.EmailField()
    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')

    # Additional info
    company = models.CharField(max_length=200, blank=True, default='')
    job_title = models.CharField(max_length=200, blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    website = models.URLField(blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    twitter_handle = models.CharField(max_length=50, blank=True, default='')

    # Location
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')
    timezone = models.CharField(max_length=50, blank=True, default='')

    # Custom fields (JSON)
    custom_fields = models.JSONField(default=dict, blank=True)

    # Status and scoring
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    score = models.IntegerField(default=0)
    score_updated_at = models.DateTimeField(null=True, blank=True)

    # Source tracking
    source = models.CharField(max_length=100, blank=True, default='')
    source_details = models.JSONField(default=dict, blank=True)

    # Relationships
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='contacts')

    # Email engagement metrics
    emails_sent = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    emails_clicked = models.IntegerField(default=0)
    emails_replied = models.IntegerField(default=0)
    emails_bounced = models.IntegerField(default=0)
    last_emailed_at = models.DateTimeField(null=True, blank=True)
    last_opened_at = models.DateTimeField(null=True, blank=True)
    last_clicked_at = models.DateTimeField(null=True, blank=True)
    last_replied_at = models.DateTimeField(null=True, blank=True)

    # Subscription
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    unsubscribe_reason = models.TextField(blank=True, default='')

    # Notes
    notes = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ['email', 'workspace']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['workspace', 'score']),
            models.Index(fields=['workspace', '-created_at']),
        ]

    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def open_rate(self):
        if self.emails_sent == 0:
            return 0
        return round((self.emails_opened / self.emails_sent) * 100, 1)

    @property
    def click_rate(self):
        if self.emails_sent == 0:
            return 0
        return round((self.emails_clicked / self.emails_sent) * 100, 1)

    @property
    def reply_rate(self):
        if self.emails_sent == 0:
            return 0
        return round((self.emails_replied / self.emails_sent) * 100, 1)


class ContactList(BaseModel):
    """Static or dynamic list of contacts."""

    class ListType(models.TextChoices):
        STATIC = 'static', 'Static List'
        SMART = 'smart', 'Smart List'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    list_type = models.CharField(
        max_length=20,
        choices=ListType.choices,
        default=ListType.STATIC
    )

    # Workspace
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='contact_lists'
    )

    # For static lists - direct contact relationship
    contacts = models.ManyToManyField(
        Contact,
        blank=True,
        related_name='lists'
    )

    # For smart lists - filter criteria
    filter_criteria = models.JSONField(default=dict, blank=True)

    # Cached count (updated periodically for smart lists)
    contact_count = models.IntegerField(default=0)
    last_count_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_contacts(self):
        """Get contacts for this list."""
        if self.list_type == self.ListType.STATIC:
            return self.contacts.all()
        else:
            # Smart list - apply filter criteria
            return self._apply_smart_filters()

    def _apply_smart_filters(self):
        """Apply smart list filter criteria to get contacts."""
        queryset = Contact.objects.filter(
            workspace=self.workspace,
            status=Contact.Status.ACTIVE
        )

        criteria = self.filter_criteria

        # Filter by tags
        if 'tags' in criteria and criteria['tags']:
            queryset = queryset.filter(tags__id__in=criteria['tags'])

        # Filter by score range
        if 'min_score' in criteria:
            queryset = queryset.filter(score__gte=criteria['min_score'])
        if 'max_score' in criteria:
            queryset = queryset.filter(score__lte=criteria['max_score'])

        # Filter by company
        if 'company' in criteria and criteria['company']:
            queryset = queryset.filter(company__icontains=criteria['company'])

        # Filter by job title
        if 'job_title' in criteria and criteria['job_title']:
            queryset = queryset.filter(job_title__icontains=criteria['job_title'])

        # Filter by location
        if 'country' in criteria and criteria['country']:
            queryset = queryset.filter(country__iexact=criteria['country'])
        if 'city' in criteria and criteria['city']:
            queryset = queryset.filter(city__icontains=criteria['city'])

        # Filter by engagement
        if 'has_opened' in criteria:
            if criteria['has_opened']:
                queryset = queryset.filter(emails_opened__gt=0)
            else:
                queryset = queryset.filter(emails_opened=0)

        if 'has_clicked' in criteria:
            if criteria['has_clicked']:
                queryset = queryset.filter(emails_clicked__gt=0)
            else:
                queryset = queryset.filter(emails_clicked=0)

        if 'has_replied' in criteria:
            if criteria['has_replied']:
                queryset = queryset.filter(emails_replied__gt=0)
            else:
                queryset = queryset.filter(emails_replied=0)

        # Filter by source
        if 'source' in criteria and criteria['source']:
            queryset = queryset.filter(source__iexact=criteria['source'])

        # Filter by custom fields
        if 'custom_fields' in criteria:
            for key, value in criteria['custom_fields'].items():
                queryset = queryset.filter(**{f'custom_fields__{key}': value})

        return queryset.distinct()

    def update_contact_count(self):
        """Update the cached contact count."""
        from django.utils import timezone
        if self.list_type == self.ListType.STATIC:
            self.contact_count = self.contacts.count()
        else:
            self.contact_count = self.get_contacts().count()
        self.last_count_updated_at = timezone.now()
        self.save(update_fields=['contact_count', 'last_count_updated_at'])


class ContactActivity(BaseModel):
    """Activity log for contacts."""

    class ActivityType(models.TextChoices):
        EMAIL_SENT = 'email_sent', 'Email Sent'
        EMAIL_OPENED = 'email_opened', 'Email Opened'
        EMAIL_CLICKED = 'email_clicked', 'Email Clicked'
        EMAIL_REPLIED = 'email_replied', 'Email Replied'
        EMAIL_BOUNCED = 'email_bounced', 'Email Bounced'
        UNSUBSCRIBED = 'unsubscribed', 'Unsubscribed'
        COMPLAINED = 'complained', 'Complained'
        SCORE_CHANGED = 'score_changed', 'Score Changed'
        TAG_ADDED = 'tag_added', 'Tag Added'
        TAG_REMOVED = 'tag_removed', 'Tag Removed'
        LIST_ADDED = 'list_added', 'Added to List'
        LIST_REMOVED = 'list_removed', 'Removed from List'
        FIELD_UPDATED = 'field_updated', 'Field Updated'
        PAGE_VIEWED = 'page_viewed', 'Page Viewed'

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices
    )
    description = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)

    # Related objects (optional)
    campaign_id = models.UUIDField(null=True, blank=True)
    sequence_id = models.UUIDField(null=True, blank=True)
    email_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contact', '-created_at']),
            models.Index(fields=['contact', 'activity_type']),
        ]

    def __str__(self):
        return f"{self.contact} - {self.activity_type}"


class CustomField(BaseModel):
    """Custom field definition for contacts."""

    class FieldType(models.TextChoices):
        TEXT = 'text', 'Text'
        NUMBER = 'number', 'Number'
        DATE = 'date', 'Date'
        BOOLEAN = 'boolean', 'Boolean'
        SELECT = 'select', 'Select'
        MULTISELECT = 'multiselect', 'Multi-Select'
        URL = 'url', 'URL'
        EMAIL = 'email', 'Email'

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='custom_fields'
    )
    name = models.CharField(max_length=100)
    field_key = models.SlugField(max_length=100)
    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT
    )
    description = models.TextField(blank=True, default='')
    is_required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=500, blank=True, default='')

    # For select/multiselect fields
    options = models.JSONField(default=list, blank=True)

    # Order for display
    display_order = models.IntegerField(default=0)

    class Meta:
        unique_together = ['workspace', 'field_key']
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.field_type})"


class ImportJob(BaseModel):
    """Track contact import jobs."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    class FileType(models.TextChoices):
        CSV = 'csv', 'CSV'
        EXCEL = 'excel', 'Excel'
        JSON = 'json', 'JSON'

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='import_jobs'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='import_jobs'
    )

    # File info
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices
    )
    file_path = models.CharField(max_length=500)

    # Mapping configuration
    field_mapping = models.JSONField(default=dict)
    default_tags = models.ManyToManyField(Tag, blank=True)
    default_list = models.ForeignKey(
        ContactList,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Progress
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    created_count = models.IntegerField(default=0)
    updated_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    # Errors
    errors = models.JSONField(default=list, blank=True)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Import {self.file_name} ({self.status})"

    @property
    def progress_percentage(self):
        if self.total_rows == 0:
            return 0
        return round((self.processed_rows / self.total_rows) * 100, 1)


class ScoringRule(BaseModel):
    """Scoring rule for automatically scoring contacts."""

    class EventType(models.TextChoices):
        EMAIL_OPENED = 'email_opened', 'Email Opened'
        EMAIL_CLICKED = 'email_clicked', 'Email Clicked'
        EMAIL_REPLIED = 'email_replied', 'Email Replied'
        LINK_CLICKED = 'link_clicked', 'Link Clicked'
        PAGE_VIEWED = 'page_viewed', 'Page Viewed'
        FORM_SUBMITTED = 'form_submitted', 'Form Submitted'
        TAG_ADDED = 'tag_added', 'Tag Added'
        LIST_ADDED = 'list_added', 'Added to List'
        CUSTOM = 'custom', 'Custom Event'

    class Operator(models.TextChoices):
        EQUALS = 'equals', 'Equals'
        NOT_EQUALS = 'not_equals', 'Not Equals'
        CONTAINS = 'contains', 'Contains'
        NOT_CONTAINS = 'not_contains', 'Does Not Contain'
        GREATER_THAN = 'greater_than', 'Greater Than'
        LESS_THAN = 'less_than', 'Less Than'
        IS_SET = 'is_set', 'Is Set'
        IS_NOT_SET = 'is_not_set', 'Is Not Set'

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='scoring_rules'
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    # Event trigger
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices
    )

    # Conditions (JSON array of conditions)
    # Format: [{"field": "page_url", "operator": "contains", "value": "/pricing"}]
    conditions = models.JSONField(default=list, blank=True)

    # Score adjustment
    score_change = models.IntegerField(default=0)  # Can be positive or negative

    # Optional: max times this rule can apply per contact
    max_applications = models.IntegerField(null=True, blank=True)

    # Optional: cooldown period in hours before rule can apply again
    cooldown_hours = models.IntegerField(null=True, blank=True)

    # Priority for rule ordering
    priority = models.IntegerField(default=0)

    class Meta:
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.name} ({self.score_change:+d})"


class ScoreHistory(BaseModel):
    """Track score changes over time for contacts."""

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='score_history'
    )

    # Score change details
    previous_score = models.IntegerField()
    new_score = models.IntegerField()
    score_change = models.IntegerField()

    # What triggered the change
    reason = models.CharField(max_length=200)
    rule = models.ForeignKey(
        ScoringRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications'
    )

    # Related event data
    event_type = models.CharField(max_length=30, blank=True, default='')
    event_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contact', '-created_at']),
        ]

    def __str__(self):
        return f"{self.contact} score {self.previous_score} -> {self.new_score}"


class ScoreThreshold(BaseModel):
    """Define thresholds for contact classification (Hot/Warm/Cold)."""

    class Classification(models.TextChoices):
        HOT = 'hot', 'Hot Lead'
        WARM = 'warm', 'Warm Lead'
        COLD = 'cold', 'Cold Lead'
        FROZEN = 'frozen', 'Frozen'

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='score_thresholds'
    )

    classification = models.CharField(
        max_length=20,
        choices=Classification.choices
    )

    min_score = models.IntegerField()
    max_score = models.IntegerField(null=True, blank=True)  # null = no upper limit
    color = models.CharField(max_length=7, default='#6366f1')

    class Meta:
        ordering = ['-min_score']
        unique_together = ['workspace', 'classification']

    def __str__(self):
        return f"{self.classification}: {self.min_score}+"


class ScoreDecayConfig(BaseModel):
    """Configuration for automatic score decay over time."""

    workspace = models.OneToOneField(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='score_decay_config'
    )

    is_enabled = models.BooleanField(default=False)

    # Decay settings
    decay_points = models.IntegerField(default=5)  # Points to decay
    decay_interval_days = models.IntegerField(default=30)  # How often to decay

    # Minimum score (don't decay below this)
    min_score = models.IntegerField(default=0)

    # Only decay inactive contacts (no activity in X days)
    inactivity_days = models.IntegerField(default=30)

    # Last run
    last_run_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Decay config for {self.workspace}"
