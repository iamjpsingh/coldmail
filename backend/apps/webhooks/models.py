import secrets
import hashlib
import hmac
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


def generate_api_key():
    """Generate a secure API key."""
    return f"cm_{secrets.token_urlsafe(32)}"


def generate_api_key_prefix():
    """Generate a short prefix for API key identification."""
    return secrets.token_hex(4)


def generate_webhook_secret():
    """Generate a webhook signing secret."""
    return f"whsec_{secrets.token_urlsafe(32)}"


class APIKey(BaseModel):
    """API key for external access to the API."""

    class Permission(models.TextChoices):
        READ = 'read', 'Read Only'
        WRITE = 'write', 'Read & Write'
        ADMIN = 'admin', 'Full Access'

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='api_keys'
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_api_keys'
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # The actual key is hashed for security - we only store hash
    key_prefix = models.CharField(max_length=8, default=generate_api_key_prefix)
    key_hash = models.CharField(max_length=64, unique=True)

    # Permissions
    permission = models.CharField(
        max_length=10,
        choices=Permission.choices,
        default=Permission.READ
    )

    # Restrictions
    allowed_ips = models.TextField(blank=True, help_text='Comma-separated list of allowed IPs')
    rate_limit_per_minute = models.IntegerField(default=60)
    rate_limit_per_day = models.IntegerField(default=10000)

    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True)
    total_requests = models.IntegerField(default=0)

    class Meta:
        db_table = 'api_keys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['key_prefix']),
            models.Index(fields=['workspace', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"

    @classmethod
    def create_key(cls, workspace, name, created_by=None, **kwargs):
        """Create a new API key and return the raw key (only available once).

        Args:
            workspace: Workspace instance
            name: Name for the API key
            created_by: User who created the key
            **kwargs: Additional fields

        Returns:
            Tuple of (APIKey instance, raw key string)
        """
        raw_key = generate_api_key()
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = cls.objects.create(
            workspace=workspace,
            name=name,
            created_by=created_by,
            key_hash=key_hash,
            **kwargs
        )

        return api_key, raw_key

    @classmethod
    def get_by_key(cls, raw_key):
        """Get an API key by its raw value.

        Args:
            raw_key: The raw API key string

        Returns:
            APIKey instance or None
        """
        if not raw_key or not raw_key.startswith('cm_'):
            return None

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        try:
            return cls.objects.select_related('workspace').get(
                key_hash=key_hash,
                is_active=True
            )
        except cls.DoesNotExist:
            return None

    def is_valid(self):
        """Check if the API key is valid for use."""
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def is_ip_allowed(self, ip_address):
        """Check if an IP address is allowed to use this key."""
        if not self.allowed_ips:
            return True
        allowed = [ip.strip() for ip in self.allowed_ips.split(',')]
        return ip_address in allowed

    def record_usage(self, ip_address=None):
        """Record usage of this API key."""
        self.last_used_at = timezone.now()
        self.last_used_ip = ip_address
        self.total_requests += 1
        self.save(update_fields=['last_used_at', 'last_used_ip', 'total_requests', 'updated_at'])

    @property
    def allowed_ips_list(self):
        if not self.allowed_ips:
            return []
        return [ip.strip() for ip in self.allowed_ips.split(',') if ip.strip()]


class Webhook(BaseModel):
    """Webhook endpoint configuration."""

    class EventType(models.TextChoices):
        # Contact events
        CONTACT_CREATED = 'contact.created', 'Contact Created'
        CONTACT_UPDATED = 'contact.updated', 'Contact Updated'
        CONTACT_DELETED = 'contact.deleted', 'Contact Deleted'
        CONTACT_SCORED = 'contact.scored', 'Contact Score Changed'
        CONTACT_TAG_ADDED = 'contact.tag_added', 'Tag Added to Contact'
        CONTACT_TAG_REMOVED = 'contact.tag_removed', 'Tag Removed from Contact'

        # Campaign events
        CAMPAIGN_CREATED = 'campaign.created', 'Campaign Created'
        CAMPAIGN_STARTED = 'campaign.started', 'Campaign Started'
        CAMPAIGN_PAUSED = 'campaign.paused', 'Campaign Paused'
        CAMPAIGN_COMPLETED = 'campaign.completed', 'Campaign Completed'
        CAMPAIGN_CANCELLED = 'campaign.cancelled', 'Campaign Cancelled'

        # Email events
        EMAIL_SENT = 'email.sent', 'Email Sent'
        EMAIL_DELIVERED = 'email.delivered', 'Email Delivered'
        EMAIL_OPENED = 'email.opened', 'Email Opened'
        EMAIL_CLICKED = 'email.clicked', 'Link Clicked'
        EMAIL_BOUNCED = 'email.bounced', 'Email Bounced'
        EMAIL_COMPLAINED = 'email.complained', 'Spam Complaint'
        EMAIL_UNSUBSCRIBED = 'email.unsubscribed', 'Unsubscribed'
        EMAIL_REPLIED = 'email.replied', 'Email Reply Received'

        # Sequence events
        SEQUENCE_ENROLLED = 'sequence.enrolled', 'Contact Enrolled in Sequence'
        SEQUENCE_COMPLETED = 'sequence.completed', 'Contact Completed Sequence'
        SEQUENCE_STOPPED = 'sequence.stopped', 'Contact Stopped in Sequence'
        SEQUENCE_STEP_EXECUTED = 'sequence.step_executed', 'Sequence Step Executed'

        # Website tracking events
        VISITOR_IDENTIFIED = 'visitor.identified', 'Website Visitor Identified'
        VISITOR_PAGE_VIEW = 'visitor.page_view', 'Website Page View'
        VISITOR_FORM_SUBMIT = 'visitor.form_submit', 'Website Form Submitted'

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_webhooks'
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    url = models.URLField(max_length=2048)

    # Events this webhook subscribes to
    events = models.JSONField(
        default=list,
        help_text='List of event types this webhook subscribes to'
    )

    # Security
    secret = models.CharField(max_length=64, default=generate_webhook_secret)
    verify_ssl = models.BooleanField(default=True)

    # Headers to include with requests
    headers = models.JSONField(
        default=dict,
        blank=True,
        help_text='Custom headers to include with webhook requests'
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Delivery settings
    timeout_seconds = models.IntegerField(default=30)
    max_retries = models.IntegerField(default=5)
    retry_delay_seconds = models.IntegerField(default=60)

    # Stats
    total_deliveries = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    last_delivery_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    # Consecutive failures tracking for auto-disable
    consecutive_failures = models.IntegerField(default=0)
    disabled_at = models.DateTimeField(null=True, blank=True)
    disabled_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'webhooks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} -> {self.url[:50]}"

    def subscribes_to(self, event_type):
        """Check if this webhook subscribes to an event type."""
        if '*' in self.events:
            return True
        return event_type in self.events

    def sign_payload(self, payload):
        """Generate HMAC signature for a payload.

        Args:
            payload: The payload string to sign

        Returns:
            Signature string in format 'sha256=<signature>'
        """
        signature = hmac.new(
            self.secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    def record_delivery(self, success, error_message=''):
        """Record a delivery attempt."""
        now = timezone.now()
        self.total_deliveries += 1
        self.last_delivery_at = now

        if success:
            self.successful_deliveries += 1
            self.last_success_at = now
            self.consecutive_failures = 0
            self.last_error = ''
        else:
            self.failed_deliveries += 1
            self.last_failure_at = now
            self.consecutive_failures += 1
            self.last_error = error_message[:1000]

            # Auto-disable after 10 consecutive failures
            if self.consecutive_failures >= 10 and self.is_active:
                self.is_active = False
                self.disabled_at = now
                self.disabled_reason = f'Auto-disabled after {self.consecutive_failures} consecutive failures'

        self.save()

    def regenerate_secret(self):
        """Regenerate the webhook signing secret."""
        self.secret = generate_webhook_secret()
        self.save(update_fields=['secret', 'updated_at'])
        return self.secret


class WebhookDelivery(BaseModel):
    """Log of webhook delivery attempts."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        RETRYING = 'retrying', 'Retrying'

    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )

    # Event info
    event_type = models.CharField(max_length=50)
    event_id = models.CharField(max_length=64, db_index=True)

    # Request details
    payload = models.JSONField()
    request_headers = models.JSONField(default=dict)

    # Response details
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    response_status_code = models.IntegerField(null=True, blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    # Timing
    duration_ms = models.IntegerField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Retry info
    attempt_number = models.IntegerField(default=1)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'webhook_deliveries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook', '-created_at']),
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['event_id']),
        ]

    def __str__(self):
        return f"{self.event_type} -> {self.webhook.url[:30]} ({self.status})"

    def schedule_retry(self):
        """Schedule a retry for this delivery."""
        if self.attempt_number >= self.webhook.max_retries:
            self.status = self.Status.FAILED
            self.save(update_fields=['status', 'updated_at'])
            return False

        # Exponential backoff: delay * 2^(attempt-1)
        delay = self.webhook.retry_delay_seconds * (2 ** (self.attempt_number - 1))
        self.next_retry_at = timezone.now() + timezone.timedelta(seconds=delay)
        self.status = self.Status.RETRYING
        self.save(update_fields=['next_retry_at', 'status', 'updated_at'])
        return True


class WebhookEventLog(BaseModel):
    """Log of events that triggered webhooks."""

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='webhook_events'
    )

    event_id = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()

    # Related objects (optional, for reference)
    contact_id = models.UUIDField(null=True, blank=True)
    campaign_id = models.UUIDField(null=True, blank=True)
    sequence_id = models.UUIDField(null=True, blank=True)

    # Processing info
    webhooks_triggered = models.IntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'webhook_event_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} ({self.event_id[:8]})"
