"""Serializers for integrations."""
from rest_framework import serializers
from .models import (
    Integration, SlackIntegration, DiscordIntegration,
    HubSpotIntegration, SalesforceIntegration, GoogleSheetsIntegration,
    IntegrationLog, IntegrationFieldMapping
)


class IntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Integration model."""

    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    success_rate = serializers.ReadOnlyField()
    integration_type_display = serializers.CharField(
        source='get_integration_type_display', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Integration
        fields = [
            'id',
            'name',
            'integration_type',
            'integration_type_display',
            'description',
            'status',
            'status_display',
            'is_active',
            'config',
            'last_sync_at',
            'last_error',
            'last_error_at',
            'total_syncs',
            'successful_syncs',
            'failed_syncs',
            'success_rate',
            'created_by_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'last_sync_at', 'last_error', 'last_error_at',
            'total_syncs', 'successful_syncs', 'failed_syncs',
            'created_by_email', 'created_at', 'updated_at',
        ]


class IntegrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an integration."""

    class Meta:
        model = Integration
        fields = ['name', 'integration_type', 'description', 'config']

    def create(self, validated_data):
        workspace = self.context['request'].user.current_workspace
        user = self.context['request'].user

        return Integration.objects.create(
            workspace=workspace,
            created_by=user,
            **validated_data
        )


class SlackIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Slack integration settings."""

    class Meta:
        model = SlackIntegration
        fields = [
            'id',
            'team_id',
            'team_name',
            'default_channel_id',
            'default_channel_name',
            'notify_on_new_contact',
            'notify_on_hot_lead',
            'notify_on_email_reply',
            'notify_on_campaign_complete',
            'notify_on_sequence_complete',
            'notify_on_form_submit',
            'notify_on_website_visit',
            'hot_lead_threshold',
        ]
        read_only_fields = ['id', 'team_id', 'team_name']


class DiscordIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Discord integration settings."""

    class Meta:
        model = DiscordIntegration
        fields = [
            'id',
            'webhook_url',
            'notify_on_new_contact',
            'notify_on_hot_lead',
            'notify_on_email_reply',
            'notify_on_campaign_complete',
            'notify_on_sequence_complete',
            'notify_on_form_submit',
            'hot_lead_threshold',
            'bot_username',
            'bot_avatar_url',
        ]
        read_only_fields = ['id']


class DiscordIntegrationCreateSerializer(serializers.Serializer):
    """Serializer for creating a Discord integration."""

    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    webhook_url = serializers.URLField()
    bot_username = serializers.CharField(max_length=80, default='ColdMail')
    bot_avatar_url = serializers.URLField(required=False, allow_blank=True)


class HubSpotIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for HubSpot integration settings."""

    class Meta:
        model = HubSpotIntegration
        fields = [
            'id',
            'portal_id',
            'portal_name',
            'sync_direction',
            'sync_contacts',
            'sync_companies',
            'sync_deals',
            'sync_activities',
            'auto_sync_interval',
            'last_auto_sync',
            'field_mapping',
            'sync_only_hot_leads',
            'min_score_to_sync',
        ]
        read_only_fields = ['id', 'portal_id', 'portal_name', 'last_auto_sync']


class SalesforceIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Salesforce integration settings."""

    class Meta:
        model = SalesforceIntegration
        fields = [
            'id',
            'instance_url',
            'org_id',
            'org_name',
            'sync_direction',
            'sync_leads',
            'sync_contacts',
            'sync_accounts',
            'sync_opportunities',
            'sync_activities',
            'auto_sync_interval',
            'last_auto_sync',
            'field_mapping',
            'sync_only_hot_leads',
            'min_score_to_sync',
            'create_as_lead',
        ]
        read_only_fields = ['id', 'instance_url', 'org_id', 'org_name', 'last_auto_sync']


class GoogleSheetsIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Google Sheets integration settings."""

    class Meta:
        model = GoogleSheetsIntegration
        fields = [
            'id',
            'spreadsheet_id',
            'spreadsheet_name',
            'spreadsheet_url',
            'contacts_sheet_name',
            'hot_leads_sheet_name',
            'campaign_stats_sheet_name',
            'export_contacts',
            'export_hot_leads',
            'export_campaign_stats',
            'auto_export_interval',
            'last_auto_export',
            'contact_columns',
            'hot_lead_columns',
        ]
        read_only_fields = ['id', 'spreadsheet_id', 'spreadsheet_name', 'spreadsheet_url', 'last_auto_export']


class IntegrationLogSerializer(serializers.ModelSerializer):
    """Serializer for integration logs."""

    level_display = serializers.CharField(source='get_level_display', read_only=True)
    operation_display = serializers.CharField(source='get_operation_display', read_only=True)

    class Meta:
        model = IntegrationLog
        fields = [
            'id',
            'level',
            'level_display',
            'operation',
            'operation_display',
            'message',
            'records_processed',
            'records_created',
            'records_updated',
            'records_failed',
            'duration_ms',
            'error_details',
            'created_at',
        ]


class IntegrationFieldMappingSerializer(serializers.ModelSerializer):
    """Serializer for field mappings."""

    class Meta:
        model = IntegrationFieldMapping
        fields = [
            'id',
            'source_field',
            'source_field_label',
            'target_field',
            'target_field_label',
            'sync_to_external',
            'sync_from_external',
            'transform_function',
            'order',
        ]


class IntegrationTypeSerializer(serializers.Serializer):
    """Serializer for listing available integration types."""

    value = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    requires_oauth = serializers.BooleanField()
    icon = serializers.CharField()

    @staticmethod
    def get_integration_types():
        """Get all available integration types."""
        return [
            {
                'value': 'slack',
                'label': 'Slack',
                'description': 'Send notifications to Slack channels',
                'requires_oauth': True,
                'icon': 'slack',
            },
            {
                'value': 'discord',
                'label': 'Discord',
                'description': 'Send notifications via Discord webhooks',
                'requires_oauth': False,
                'icon': 'discord',
            },
            {
                'value': 'hubspot',
                'label': 'HubSpot',
                'description': 'Sync contacts with HubSpot CRM',
                'requires_oauth': True,
                'icon': 'hubspot',
            },
            {
                'value': 'salesforce',
                'label': 'Salesforce',
                'description': 'Sync contacts with Salesforce CRM',
                'requires_oauth': True,
                'icon': 'salesforce',
            },
            {
                'value': 'google_sheets',
                'label': 'Google Sheets',
                'description': 'Export data to Google Sheets',
                'requires_oauth': True,
                'icon': 'google-sheets',
            },
            {
                'value': 'zapier',
                'label': 'Zapier',
                'description': 'Connect with 5000+ apps via Zapier',
                'requires_oauth': False,
                'icon': 'zapier',
            },
            {
                'value': 'n8n',
                'label': 'n8n',
                'description': 'Connect with n8n automation workflows',
                'requires_oauth': False,
                'icon': 'n8n',
            },
        ]


class OAuthURLSerializer(serializers.Serializer):
    """Serializer for OAuth URL response."""

    url = serializers.URLField()


class TestConnectionSerializer(serializers.Serializer):
    """Serializer for test connection response."""

    success = serializers.BooleanField()
    message = serializers.CharField()


class SyncResultSerializer(serializers.Serializer):
    """Serializer for sync result."""

    processed = serializers.IntegerField()
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    failed = serializers.IntegerField()
    skipped = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.DictField())
