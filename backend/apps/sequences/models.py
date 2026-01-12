from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class Sequence(BaseModel):
    """Email sequence for automated follow-ups."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        ARCHIVED = 'archived', 'Archived'

    # Basic info
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='sequences'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    # Sender settings
    email_account = models.ForeignKey(
        'email_accounts.EmailAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sequences'
    )
    from_name = models.CharField(max_length=255, blank=True)
    reply_to = models.EmailField(blank=True)

    # Tracking settings
    track_opens = models.BooleanField(default=True)
    track_clicks = models.BooleanField(default=True)
    include_unsubscribe_link = models.BooleanField(default=True)

    # Sending window (optional)
    send_window_enabled = models.BooleanField(default=False)
    send_window_start = models.TimeField(null=True, blank=True)  # e.g., 09:00
    send_window_end = models.TimeField(null=True, blank=True)  # e.g., 17:00
    send_window_days = models.JSONField(default=list, blank=True)  # [0,1,2,3,4] Mon-Fri
    send_window_timezone = models.CharField(max_length=50, default='UTC')

    # Throttling
    max_emails_per_day = models.IntegerField(default=100)
    min_delay_between_emails = models.IntegerField(default=60)  # seconds

    # Stop conditions (global for all enrollees)
    stop_on_reply = models.BooleanField(default=True)
    stop_on_click = models.BooleanField(default=False)
    stop_on_open = models.BooleanField(default=False)
    stop_on_unsubscribe = models.BooleanField(default=True)
    stop_on_bounce = models.BooleanField(default=True)
    stop_on_score_above = models.IntegerField(null=True, blank=True)  # Stop if contact score exceeds this
    stop_on_score_below = models.IntegerField(null=True, blank=True)  # Stop if contact score drops below

    # Statistics
    total_enrolled = models.IntegerField(default=0)
    active_enrolled = models.IntegerField(default=0)
    completed_count = models.IntegerField(default=0)
    stopped_count = models.IntegerField(default=0)
    total_sent = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_replied = models.IntegerField(default=0)

    # Metadata
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sequences'
    )

    class Meta:
        db_table = 'sequences'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def step_count(self):
        return self.steps.count()

    @property
    def open_rate(self):
        if self.total_sent == 0:
            return 0
        return round((self.total_opened / self.total_sent) * 100, 1)

    @property
    def click_rate(self):
        if self.total_sent == 0:
            return 0
        return round((self.total_clicked / self.total_sent) * 100, 1)

    @property
    def reply_rate(self):
        if self.total_sent == 0:
            return 0
        return round((self.total_replied / self.total_sent) * 100, 1)


class SequenceStep(BaseModel):
    """A step in an email sequence."""

    class StepType(models.TextChoices):
        EMAIL = 'email', 'Send Email'
        DELAY = 'delay', 'Wait/Delay'
        CONDITION = 'condition', 'Condition Branch'
        TASK = 'task', 'Create Task'
        WEBHOOK = 'webhook', 'Trigger Webhook'
        TAG = 'tag', 'Add/Remove Tag'

    class DelayUnit(models.TextChoices):
        MINUTES = 'minutes', 'Minutes'
        HOURS = 'hours', 'Hours'
        DAYS = 'days', 'Days'
        WEEKS = 'weeks', 'Weeks'

    sequence = models.ForeignKey(
        Sequence,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    order = models.IntegerField(default=0)
    step_type = models.CharField(
        max_length=20,
        choices=StepType.choices,
        default=StepType.EMAIL
    )
    name = models.CharField(max_length=200, blank=True)

    # Email step fields
    subject = models.CharField(max_length=500, blank=True)
    content_html = models.TextField(blank=True)
    content_text = models.TextField(blank=True)
    template = models.ForeignKey(
        'campaigns.EmailTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sequence_steps'
    )

    # Delay configuration
    delay_value = models.IntegerField(default=1)
    delay_unit = models.CharField(
        max_length=10,
        choices=DelayUnit.choices,
        default=DelayUnit.DAYS
    )

    # Condition fields (for branching)
    condition_type = models.CharField(max_length=50, blank=True)  # opened, clicked, replied, etc.
    condition_value = models.JSONField(default=dict, blank=True)  # Additional condition params
    true_branch_step = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='condition_true_sources'
    )
    false_branch_step = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='condition_false_sources'
    )

    # Tag step fields
    tag_action = models.CharField(max_length=10, blank=True)  # add, remove
    tag = models.ForeignKey(
        'contacts.Tag',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sequence_tag_steps'
    )

    # Webhook step fields
    webhook_url = models.URLField(blank=True)
    webhook_method = models.CharField(max_length=10, default='POST')
    webhook_headers = models.JSONField(default=dict, blank=True)
    webhook_payload = models.JSONField(default=dict, blank=True)

    # Task step fields
    task_title = models.CharField(max_length=200, blank=True)
    task_description = models.TextField(blank=True)
    task_assignee = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_sequence_tasks'
    )

    # Statistics for this step
    sent_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    replied_count = models.IntegerField(default=0)
    bounced_count = models.IntegerField(default=0)

    # Active state
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'sequence_steps'
        ordering = ['sequence', 'order']
        unique_together = ['sequence', 'order']

    def __str__(self):
        return f"{self.sequence.name} - Step {self.order + 1}: {self.get_step_type_display()}"

    @property
    def delay_seconds(self):
        """Convert delay to seconds for scheduling."""
        multipliers = {
            'minutes': 60,
            'hours': 3600,
            'days': 86400,
            'weeks': 604800,
        }
        return self.delay_value * multipliers.get(self.delay_unit, 86400)

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


class SequenceEnrollment(BaseModel):
    """A contact enrolled in a sequence."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        COMPLETED = 'completed', 'Completed'
        STOPPED = 'stopped', 'Stopped'
        FAILED = 'failed', 'Failed'

    class StopReason(models.TextChoices):
        COMPLETED = 'completed', 'Completed All Steps'
        MANUAL = 'manual', 'Manually Stopped'
        REPLY = 'reply', 'Contact Replied'
        CLICK = 'click', 'Contact Clicked'
        OPEN = 'open', 'Contact Opened'
        UNSUBSCRIBE = 'unsubscribe', 'Contact Unsubscribed'
        BOUNCE = 'bounce', 'Email Bounced'
        SCORE_HIGH = 'score_high', 'Score Exceeded Threshold'
        SCORE_LOW = 'score_low', 'Score Below Threshold'
        CONTACT_DELETED = 'contact_deleted', 'Contact Deleted'
        SEQUENCE_PAUSED = 'sequence_paused', 'Sequence Paused'
        SEQUENCE_DELETED = 'sequence_deleted', 'Sequence Deleted'
        ERROR = 'error', 'Error Occurred'

    sequence = models.ForeignKey(
        Sequence,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.CASCADE,
        related_name='sequence_enrollments'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    stop_reason = models.CharField(
        max_length=30,
        choices=StopReason.choices,
        blank=True
    )
    stop_details = models.TextField(blank=True)

    # Current position in sequence
    current_step = models.ForeignKey(
        SequenceStep,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_enrollments'
    )
    current_step_index = models.IntegerField(default=0)

    # Scheduling
    next_step_at = models.DateTimeField(null=True, blank=True)
    last_step_at = models.DateTimeField(null=True, blank=True)

    # Timing
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)

    # Engagement
    emails_sent = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    emails_clicked = models.IntegerField(default=0)
    has_replied = models.BooleanField(default=False)

    # Enrollment source
    enrolled_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrolled_contacts'
    )
    enrollment_source = models.CharField(max_length=50, blank=True)  # manual, import, automation, api

    # Retry handling
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        db_table = 'sequence_enrollments'
        unique_together = ['sequence', 'contact']
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['sequence', 'status']),
            models.Index(fields=['status', 'next_step_at']),
            models.Index(fields=['contact', 'status']),
        ]

    def __str__(self):
        return f"{self.contact.email} in {self.sequence.name}"

    def pause(self):
        """Pause the enrollment."""
        self.status = self.Status.PAUSED
        self.paused_at = timezone.now()
        self.save(update_fields=['status', 'paused_at', 'updated_at'])

    def resume(self):
        """Resume a paused enrollment."""
        if self.status == self.Status.PAUSED:
            self.status = self.Status.ACTIVE
            self.paused_at = None
            self.save(update_fields=['status', 'paused_at', 'updated_at'])

    def stop(self, reason, details=''):
        """Stop the enrollment."""
        self.status = self.Status.STOPPED
        self.stop_reason = reason
        self.stop_details = details
        self.stopped_at = timezone.now()
        self.save(update_fields=['status', 'stop_reason', 'stop_details', 'stopped_at', 'updated_at'])

    def complete(self):
        """Mark enrollment as completed."""
        self.status = self.Status.COMPLETED
        self.stop_reason = self.StopReason.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'stop_reason', 'completed_at', 'updated_at'])


class SequenceStepExecution(BaseModel):
    """Record of a step being executed for an enrollment."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SCHEDULED = 'scheduled', 'Scheduled'
        SENDING = 'sending', 'Sending'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        OPENED = 'opened', 'Opened'
        CLICKED = 'clicked', 'Clicked'
        REPLIED = 'replied', 'Replied'
        BOUNCED = 'bounced', 'Bounced'
        FAILED = 'failed', 'Failed'
        SKIPPED = 'skipped', 'Skipped'

    enrollment = models.ForeignKey(
        SequenceEnrollment,
        on_delete=models.CASCADE,
        related_name='step_executions'
    )
    step = models.ForeignKey(
        SequenceStep,
        on_delete=models.CASCADE,
        related_name='executions'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    status_reason = models.TextField(blank=True)

    # Personalized content (for email steps)
    rendered_subject = models.CharField(max_length=500, blank=True)
    rendered_html = models.TextField(blank=True)
    rendered_text = models.TextField(blank=True)

    # Timing
    scheduled_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    # Email details
    message_id = models.CharField(max_length=255, blank=True)
    email_account = models.ForeignKey(
        'email_accounts.EmailAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sequence_emails'
    )

    # Engagement
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    clicked_urls = models.JSONField(default=list, blank=True)

    # Error handling
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        db_table = 'sequence_step_executions'
        ordering = ['enrollment', 'step__order']
        unique_together = ['enrollment', 'step']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['enrollment', 'status']),
        ]

    def __str__(self):
        return f"{self.enrollment} - Step {self.step.order + 1}"


class SequenceEvent(BaseModel):
    """Events/activities for sequence enrollments."""

    class EventType(models.TextChoices):
        ENROLLED = 'enrolled', 'Enrolled'
        STARTED = 'started', 'Started'
        STEP_EXECUTED = 'step_executed', 'Step Executed'
        EMAIL_SENT = 'email_sent', 'Email Sent'
        EMAIL_OPENED = 'email_opened', 'Email Opened'
        EMAIL_CLICKED = 'email_clicked', 'Email Clicked'
        EMAIL_REPLIED = 'email_replied', 'Email Replied'
        EMAIL_BOUNCED = 'email_bounced', 'Email Bounced'
        PAUSED = 'paused', 'Paused'
        RESUMED = 'resumed', 'Resumed'
        STOPPED = 'stopped', 'Stopped'
        COMPLETED = 'completed', 'Completed'
        ERROR = 'error', 'Error'
        TAG_ADDED = 'tag_added', 'Tag Added'
        TAG_REMOVED = 'tag_removed', 'Tag Removed'
        WEBHOOK_TRIGGERED = 'webhook_triggered', 'Webhook Triggered'
        TASK_CREATED = 'task_created', 'Task Created'

    enrollment = models.ForeignKey(
        SequenceEnrollment,
        on_delete=models.CASCADE,
        related_name='events'
    )
    step = models.ForeignKey(
        SequenceStep,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices
    )

    # Event details
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # For click events
    clicked_url = models.URLField(blank=True)

    # Device/location info (for opens/clicks)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Bot detection
    is_bot = models.BooleanField(default=False)

    class Meta:
        db_table = 'sequence_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['enrollment', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.enrollment} - {self.event_type}"
