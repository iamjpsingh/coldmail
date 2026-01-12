from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.core.models import BaseModel


class EmailAccount(BaseModel):
    """Email account for sending campaigns."""

    class Provider(models.TextChoices):
        SMTP = 'smtp', 'SMTP'
        GMAIL = 'gmail', 'Gmail (OAuth)'
        OUTLOOK = 'outlook', 'Outlook/Microsoft 365 (OAuth)'
        SENDGRID = 'sendgrid', 'SendGrid'
        MAILGUN = 'mailgun', 'Mailgun'
        AWS_SES = 'aws_ses', 'Amazon SES'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        ERROR = 'error', 'Error'
        DISCONNECTED = 'disconnected', 'Disconnected'

    # Ownership
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_accounts'
    )
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='email_accounts',
        null=True,
        blank=True
    )

    # Account info
    name = models.CharField(max_length=255, help_text="Display name for this account")
    email = models.EmailField(help_text="Email address")
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.SMTP)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # SMTP Configuration
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.IntegerField(default=587)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password = models.CharField(max_length=500, blank=True)  # Encrypted
    smtp_use_tls = models.BooleanField(default=True)
    smtp_use_ssl = models.BooleanField(default=False)

    # IMAP Configuration (for receiving/tracking replies)
    imap_host = models.CharField(max_length=255, blank=True)
    imap_port = models.IntegerField(default=993)
    imap_username = models.CharField(max_length=255, blank=True)
    imap_password = models.CharField(max_length=500, blank=True)  # Encrypted
    imap_use_ssl = models.BooleanField(default=True)

    # OAuth tokens (for Gmail/Outlook)
    oauth_access_token = models.TextField(blank=True)
    oauth_refresh_token = models.TextField(blank=True)
    oauth_token_expires_at = models.DateTimeField(null=True, blank=True)

    # Sender identity
    from_name = models.CharField(max_length=255, blank=True, help_text="Display name in From field")
    reply_to = models.EmailField(blank=True, help_text="Reply-to address")
    signature = models.TextField(blank=True, help_text="Email signature HTML")

    # Sending limits
    daily_limit = models.IntegerField(default=100, help_text="Maximum emails per day")
    hourly_limit = models.IntegerField(default=20, help_text="Maximum emails per hour")
    emails_sent_today = models.IntegerField(default=0)
    emails_sent_this_hour = models.IntegerField(default=0)
    last_hour_reset = models.DateTimeField(default=timezone.now)
    last_day_reset = models.DateTimeField(default=timezone.now)

    # Warmup settings
    is_warming_up = models.BooleanField(default=False)
    warmup_daily_increase = models.IntegerField(default=5)
    warmup_current_limit = models.IntegerField(default=10)
    warmup_started_at = models.DateTimeField(null=True, blank=True)

    # Health tracking
    last_connection_test = models.DateTimeField(null=True, blank=True)
    last_connection_success = models.BooleanField(default=False)
    last_connection_error = models.TextField(blank=True)
    last_email_sent_at = models.DateTimeField(null=True, blank=True)
    total_emails_sent = models.IntegerField(default=0)
    bounce_rate = models.FloatField(default=0.0)
    reputation_score = models.FloatField(default=100.0)

    class Meta:
        db_table = 'email_accounts'
        ordering = ['-created_at']
        unique_together = ['user', 'email']

    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def is_oauth(self):
        return self.provider in [self.Provider.GMAIL, self.Provider.OUTLOOK]

    @property
    def can_send(self):
        """Check if this account can send emails right now."""
        if self.status != self.Status.ACTIVE:
            return False

        # Check daily limit
        effective_daily_limit = self.warmup_current_limit if self.is_warming_up else self.daily_limit
        if self.emails_sent_today >= effective_daily_limit:
            return False

        # Check hourly limit
        if self.emails_sent_this_hour >= self.hourly_limit:
            return False

        return True

    @property
    def remaining_today(self):
        """Get remaining emails that can be sent today."""
        effective_limit = self.warmup_current_limit if self.is_warming_up else self.daily_limit
        return max(0, effective_limit - self.emails_sent_today)

    @property
    def remaining_this_hour(self):
        """Get remaining emails that can be sent this hour."""
        return max(0, self.hourly_limit - self.emails_sent_this_hour)

    def reset_hourly_counter(self):
        """Reset hourly email counter."""
        self.emails_sent_this_hour = 0
        self.last_hour_reset = timezone.now()
        self.save(update_fields=['emails_sent_this_hour', 'last_hour_reset'])

    def reset_daily_counter(self):
        """Reset daily email counter and update warmup limit."""
        self.emails_sent_today = 0
        self.last_day_reset = timezone.now()

        # Increase warmup limit if warming up
        if self.is_warming_up:
            self.warmup_current_limit = min(
                self.warmup_current_limit + self.warmup_daily_increase,
                self.daily_limit
            )
            # Stop warmup if we've reached the daily limit
            if self.warmup_current_limit >= self.daily_limit:
                self.is_warming_up = False

        self.save(update_fields=[
            'emails_sent_today', 'last_day_reset',
            'warmup_current_limit', 'is_warming_up'
        ])

    def increment_sent_count(self):
        """Increment sent counters after sending an email."""
        self.emails_sent_today += 1
        self.emails_sent_this_hour += 1
        self.total_emails_sent += 1
        self.last_email_sent_at = timezone.now()
        self.save(update_fields=[
            'emails_sent_today', 'emails_sent_this_hour',
            'total_emails_sent', 'last_email_sent_at'
        ])


class EmailAccountLog(BaseModel):
    """Log of email account activities and errors."""

    class LogType(models.TextChoices):
        CONNECTION_TEST = 'connection_test', 'Connection Test'
        EMAIL_SENT = 'email_sent', 'Email Sent'
        EMAIL_FAILED = 'email_failed', 'Email Failed'
        OAUTH_REFRESH = 'oauth_refresh', 'OAuth Token Refresh'
        LIMIT_REACHED = 'limit_reached', 'Limit Reached'
        ERROR = 'error', 'Error'

    email_account = models.ForeignKey(
        EmailAccount,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    log_type = models.CharField(max_length=20, choices=LogType.choices)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    is_success = models.BooleanField(default=True)

    class Meta:
        db_table = 'email_account_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email_account.email} - {self.log_type} - {self.created_at}"
