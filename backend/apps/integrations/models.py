"""Models for integrations system."""
import secrets
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class Integration(BaseModel):
    """Base model for all integrations."""

    class IntegrationType(models.TextChoices):
        SLACK = 'slack', 'Slack'
        DISCORD = 'discord', 'Discord'
        HUBSPOT = 'hubspot', 'HubSpot'
        SALESFORCE = 'salesforce', 'Salesforce'
        GOOGLE_SHEETS = 'google_sheets', 'Google Sheets'
        ZAPIER = 'zapier', 'Zapier'
        N8N = 'n8n', 'n8n'
        CUSTOM_WEBHOOK = 'custom_webhook', 'Custom Webhook'

    class Status(models.TextChoices):
        CONNECTED = 'connected', 'Connected'
        DISCONNECTED = 'disconnected', 'Disconnected'
        ERROR = 'error', 'Error'
        PENDING = 'pending', 'Pending Setup'

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='integrations'
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_integrations'
    )

    name = models.CharField(max_length=100)
    integration_type = models.CharField(
        max_length=20,
        choices=IntegrationType.choices
    )
    description = models.TextField(blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    is_active = models.BooleanField(default=True)

    # Configuration (stored as JSON)
    config = models.JSONField(default=dict)

    # OAuth tokens (encrypted in production)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # Usage tracking
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    last_error_at = models.DateTimeField(null=True, blank=True)
    total_syncs = models.IntegerField(default=0)
    successful_syncs = models.IntegerField(default=0)
    failed_syncs = models.IntegerField(default=0)

    class Meta:
        db_table = 'integrations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'integration_type']),
            models.Index(fields=['workspace', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"

    def record_sync(self, success, error_message=''):
        """Record a sync attempt."""
        now = timezone.now()
        self.last_sync_at = now
        self.total_syncs += 1

        if success:
            self.successful_syncs += 1
            self.last_error = ''
            self.status = self.Status.CONNECTED
        else:
            self.failed_syncs += 1
            self.last_error = error_message[:1000]
            self.last_error_at = now
            if self.failed_syncs >= 5:
                self.status = self.Status.ERROR

        self.save()

    @property
    def success_rate(self):
        if self.total_syncs == 0:
            return 100.0
        return round((self.successful_syncs / self.total_syncs) * 100, 2)


class SlackIntegration(BaseModel):
    """Slack-specific integration settings."""

    integration = models.OneToOneField(
        Integration,
        on_delete=models.CASCADE,
        related_name='slack_config'
    )

    # Slack workspace info
    team_id = models.CharField(max_length=50, blank=True)
    team_name = models.CharField(max_length=100, blank=True)

    # Default channel for notifications
    default_channel_id = models.CharField(max_length=50, blank=True)
    default_channel_name = models.CharField(max_length=100, blank=True)

    # Notification settings
    notify_on_new_contact = models.BooleanField(default=False)
    notify_on_hot_lead = models.BooleanField(default=True)
    notify_on_email_reply = models.BooleanField(default=True)
    notify_on_campaign_complete = models.BooleanField(default=True)
    notify_on_sequence_complete = models.BooleanField(default=False)
    notify_on_form_submit = models.BooleanField(default=True)
    notify_on_website_visit = models.BooleanField(default=False)

    # Minimum score for hot lead notifications
    hot_lead_threshold = models.IntegerField(default=80)

    class Meta:
        db_table = 'slack_integrations'

    def __str__(self):
        return f"Slack: {self.team_name or 'Not configured'}"


class DiscordIntegration(BaseModel):
    """Discord-specific integration settings."""

    integration = models.OneToOneField(
        Integration,
        on_delete=models.CASCADE,
        related_name='discord_config'
    )

    # Discord webhook URL
    webhook_url = models.URLField(max_length=500)

    # Notification settings
    notify_on_new_contact = models.BooleanField(default=False)
    notify_on_hot_lead = models.BooleanField(default=True)
    notify_on_email_reply = models.BooleanField(default=True)
    notify_on_campaign_complete = models.BooleanField(default=True)
    notify_on_sequence_complete = models.BooleanField(default=False)
    notify_on_form_submit = models.BooleanField(default=True)

    # Minimum score for hot lead notifications
    hot_lead_threshold = models.IntegerField(default=80)

    # Customization
    bot_username = models.CharField(max_length=80, default='ColdMail')
    bot_avatar_url = models.URLField(max_length=500, blank=True)

    class Meta:
        db_table = 'discord_integrations'

    def __str__(self):
        return f"Discord: {self.bot_username}"


class HubSpotIntegration(BaseModel):
    """HubSpot CRM integration settings."""

    class SyncDirection(models.TextChoices):
        TO_HUBSPOT = 'to_hubspot', 'ColdMail → HubSpot'
        FROM_HUBSPOT = 'from_hubspot', 'HubSpot → ColdMail'
        BIDIRECTIONAL = 'bidirectional', 'Bidirectional'

    integration = models.OneToOneField(
        Integration,
        on_delete=models.CASCADE,
        related_name='hubspot_config'
    )

    # HubSpot portal info
    portal_id = models.CharField(max_length=50, blank=True)
    portal_name = models.CharField(max_length=100, blank=True)

    # Sync settings
    sync_direction = models.CharField(
        max_length=20,
        choices=SyncDirection.choices,
        default=SyncDirection.TO_HUBSPOT
    )
    sync_contacts = models.BooleanField(default=True)
    sync_companies = models.BooleanField(default=False)
    sync_deals = models.BooleanField(default=False)
    sync_activities = models.BooleanField(default=True)

    # Auto sync interval (in minutes, 0 = manual only)
    auto_sync_interval = models.IntegerField(default=60)
    last_auto_sync = models.DateTimeField(null=True, blank=True)

    # Field mapping (ColdMail field -> HubSpot property)
    field_mapping = models.JSONField(default=dict)

    # Filters
    sync_only_hot_leads = models.BooleanField(default=False)
    min_score_to_sync = models.IntegerField(default=0)

    class Meta:
        db_table = 'hubspot_integrations'

    def __str__(self):
        return f"HubSpot: {self.portal_name or 'Not configured'}"


class SalesforceIntegration(BaseModel):
    """Salesforce CRM integration settings."""

    class SyncDirection(models.TextChoices):
        TO_SALESFORCE = 'to_salesforce', 'ColdMail → Salesforce'
        FROM_SALESFORCE = 'from_salesforce', 'Salesforce → ColdMail'
        BIDIRECTIONAL = 'bidirectional', 'Bidirectional'

    integration = models.OneToOneField(
        Integration,
        on_delete=models.CASCADE,
        related_name='salesforce_config'
    )

    # Salesforce org info
    instance_url = models.URLField(max_length=500, blank=True)
    org_id = models.CharField(max_length=50, blank=True)
    org_name = models.CharField(max_length=100, blank=True)

    # Sync settings
    sync_direction = models.CharField(
        max_length=20,
        choices=SyncDirection.choices,
        default=SyncDirection.TO_SALESFORCE
    )
    sync_leads = models.BooleanField(default=True)
    sync_contacts = models.BooleanField(default=True)
    sync_accounts = models.BooleanField(default=False)
    sync_opportunities = models.BooleanField(default=False)
    sync_activities = models.BooleanField(default=True)

    # Auto sync interval (in minutes, 0 = manual only)
    auto_sync_interval = models.IntegerField(default=60)
    last_auto_sync = models.DateTimeField(null=True, blank=True)

    # Field mapping (ColdMail field -> Salesforce field)
    field_mapping = models.JSONField(default=dict)

    # Filters
    sync_only_hot_leads = models.BooleanField(default=False)
    min_score_to_sync = models.IntegerField(default=0)

    # Create as Lead or Contact
    create_as_lead = models.BooleanField(default=True)

    class Meta:
        db_table = 'salesforce_integrations'

    def __str__(self):
        return f"Salesforce: {self.org_name or 'Not configured'}"


class GoogleSheetsIntegration(BaseModel):
    """Google Sheets export integration settings."""

    integration = models.OneToOneField(
        Integration,
        on_delete=models.CASCADE,
        related_name='google_sheets_config'
    )

    # Spreadsheet info
    spreadsheet_id = models.CharField(max_length=100, blank=True)
    spreadsheet_name = models.CharField(max_length=200, blank=True)
    spreadsheet_url = models.URLField(max_length=500, blank=True)

    # Sheet names for different data
    contacts_sheet_name = models.CharField(max_length=100, default='Contacts')
    hot_leads_sheet_name = models.CharField(max_length=100, default='Hot Leads')
    campaign_stats_sheet_name = models.CharField(max_length=100, default='Campaign Stats')

    # Export settings
    export_contacts = models.BooleanField(default=True)
    export_hot_leads = models.BooleanField(default=True)
    export_campaign_stats = models.BooleanField(default=True)

    # Auto export interval (in minutes, 0 = manual only)
    auto_export_interval = models.IntegerField(default=0)
    last_auto_export = models.DateTimeField(null=True, blank=True)

    # Column configuration
    contact_columns = models.JSONField(default=list)
    hot_lead_columns = models.JSONField(default=list)

    class Meta:
        db_table = 'google_sheets_integrations'

    def __str__(self):
        return f"Google Sheets: {self.spreadsheet_name or 'Not configured'}"


class IntegrationLog(BaseModel):
    """Log of integration sync operations."""

    class LogLevel(models.TextChoices):
        DEBUG = 'debug', 'Debug'
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'

    class Operation(models.TextChoices):
        SYNC = 'sync', 'Sync'
        EXPORT = 'export', 'Export'
        IMPORT = 'import', 'Import'
        NOTIFICATION = 'notification', 'Notification'
        AUTH = 'auth', 'Authentication'
        TEST = 'test', 'Test'

    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name='logs'
    )

    level = models.CharField(
        max_length=10,
        choices=LogLevel.choices,
        default=LogLevel.INFO
    )
    operation = models.CharField(
        max_length=20,
        choices=Operation.choices
    )
    message = models.TextField()

    # Details
    records_processed = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    duration_ms = models.IntegerField(null=True, blank=True)

    # Error details
    error_details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'integration_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['integration', '-created_at']),
            models.Index(fields=['level', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_level_display()}: {self.message[:50]}"


class IntegrationFieldMapping(BaseModel):
    """Field mapping configuration for CRM integrations."""

    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name='field_mappings'
    )

    # ColdMail field
    source_field = models.CharField(max_length=100)
    source_field_label = models.CharField(max_length=200)

    # External system field
    target_field = models.CharField(max_length=100)
    target_field_label = models.CharField(max_length=200)

    # Sync direction for this specific field
    sync_to_external = models.BooleanField(default=True)
    sync_from_external = models.BooleanField(default=False)

    # Transformation
    transform_function = models.CharField(max_length=50, blank=True)

    # Order
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'integration_field_mappings'
        ordering = ['integration', 'order']
        unique_together = ['integration', 'source_field']

    def __str__(self):
        return f"{self.source_field} → {self.target_field}"
