"""Serializers for API keys and webhooks."""
from rest_framework import serializers
from .models import APIKey, Webhook, WebhookDelivery, WebhookEventLog


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for APIKey model (for listing/viewing)."""

    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    is_expired = serializers.SerializerMethodField()
    allowed_ips_list = serializers.ReadOnlyField()

    class Meta:
        model = APIKey
        fields = [
            'id',
            'name',
            'description',
            'key_prefix',
            'permission',
            'allowed_ips',
            'allowed_ips_list',
            'rate_limit_per_minute',
            'rate_limit_per_day',
            'is_active',
            'expires_at',
            'is_expired',
            'last_used_at',
            'last_used_ip',
            'total_requests',
            'created_by_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'key_prefix',
            'last_used_at',
            'last_used_ip',
            'total_requests',
            'created_by_email',
            'created_at',
            'updated_at',
        ]

    def get_is_expired(self, obj):
        return not obj.is_valid() if obj.is_active else True


class APIKeyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new API key."""

    class Meta:
        model = APIKey
        fields = [
            'name',
            'description',
            'permission',
            'allowed_ips',
            'rate_limit_per_minute',
            'rate_limit_per_day',
            'expires_at',
        ]

    def create(self, validated_data):
        """Create a new API key and return both the key and raw key."""
        workspace = self.context['request'].user.current_workspace
        user = self.context['request'].user

        api_key, raw_key = APIKey.create_key(
            workspace=workspace,
            created_by=user,
            **validated_data
        )

        # Attach raw key for one-time display
        api_key._raw_key = raw_key
        return api_key


class APIKeyCreateResponseSerializer(serializers.ModelSerializer):
    """Serializer for the response when creating an API key (includes raw key)."""

    raw_key = serializers.SerializerMethodField()

    class Meta:
        model = APIKey
        fields = [
            'id',
            'name',
            'description',
            'key_prefix',
            'permission',
            'raw_key',
            'created_at',
        ]

    def get_raw_key(self, obj):
        return getattr(obj, '_raw_key', None)


class APIKeyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an API key."""

    class Meta:
        model = APIKey
        fields = [
            'name',
            'description',
            'permission',
            'allowed_ips',
            'rate_limit_per_minute',
            'rate_limit_per_day',
            'is_active',
            'expires_at',
        ]


class WebhookSerializer(serializers.ModelSerializer):
    """Serializer for Webhook model."""

    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = Webhook
        fields = [
            'id',
            'name',
            'description',
            'url',
            'events',
            'verify_ssl',
            'headers',
            'is_active',
            'timeout_seconds',
            'max_retries',
            'retry_delay_seconds',
            'total_deliveries',
            'successful_deliveries',
            'failed_deliveries',
            'success_rate',
            'last_delivery_at',
            'last_success_at',
            'last_failure_at',
            'last_error',
            'consecutive_failures',
            'disabled_at',
            'disabled_reason',
            'created_by_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'secret',
            'total_deliveries',
            'successful_deliveries',
            'failed_deliveries',
            'last_delivery_at',
            'last_success_at',
            'last_failure_at',
            'last_error',
            'consecutive_failures',
            'disabled_at',
            'disabled_reason',
            'created_by_email',
            'created_at',
            'updated_at',
        ]

    def get_success_rate(self, obj):
        if obj.total_deliveries == 0:
            return 100.0
        return round((obj.successful_deliveries / obj.total_deliveries) * 100, 2)


class WebhookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new webhook."""

    class Meta:
        model = Webhook
        fields = [
            'name',
            'description',
            'url',
            'events',
            'verify_ssl',
            'headers',
            'timeout_seconds',
            'max_retries',
            'retry_delay_seconds',
        ]

    def validate_events(self, value):
        """Validate that events is a list of valid event types."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Events must be a list")

        valid_events = [choice[0] for choice in Webhook.EventType.choices]
        valid_events.append('*')  # Allow wildcard

        for event in value:
            if event not in valid_events:
                raise serializers.ValidationError(f"Invalid event type: {event}")

        return value

    def create(self, validated_data):
        workspace = self.context['request'].user.current_workspace
        user = self.context['request'].user

        return Webhook.objects.create(
            workspace=workspace,
            created_by=user,
            **validated_data
        )


class WebhookUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a webhook."""

    class Meta:
        model = Webhook
        fields = [
            'name',
            'description',
            'url',
            'events',
            'verify_ssl',
            'headers',
            'is_active',
            'timeout_seconds',
            'max_retries',
            'retry_delay_seconds',
        ]

    def validate_events(self, value):
        """Validate that events is a list of valid event types."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Events must be a list")

        valid_events = [choice[0] for choice in Webhook.EventType.choices]
        valid_events.append('*')

        for event in value:
            if event not in valid_events:
                raise serializers.ValidationError(f"Invalid event type: {event}")

        return value


class WebhookSecretSerializer(serializers.Serializer):
    """Serializer for webhook secret response."""

    secret = serializers.CharField(read_only=True)


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """Serializer for WebhookDelivery model."""

    webhook_name = serializers.CharField(source='webhook.name', read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id',
            'webhook',
            'webhook_name',
            'event_type',
            'event_id',
            'payload',
            'request_headers',
            'status',
            'response_status_code',
            'response_headers',
            'response_body',
            'error_message',
            'duration_ms',
            'delivered_at',
            'attempt_number',
            'next_retry_at',
            'created_at',
        ]


class WebhookDeliveryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing webhook deliveries."""

    webhook_name = serializers.CharField(source='webhook.name', read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id',
            'webhook',
            'webhook_name',
            'event_type',
            'event_id',
            'status',
            'response_status_code',
            'duration_ms',
            'attempt_number',
            'created_at',
            'delivered_at',
        ]


class WebhookEventLogSerializer(serializers.ModelSerializer):
    """Serializer for WebhookEventLog model."""

    class Meta:
        model = WebhookEventLog
        fields = [
            'id',
            'event_id',
            'event_type',
            'payload',
            'contact_id',
            'campaign_id',
            'sequence_id',
            'webhooks_triggered',
            'processed_at',
            'created_at',
        ]


class WebhookEventLogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing webhook events."""

    class Meta:
        model = WebhookEventLog
        fields = [
            'id',
            'event_id',
            'event_type',
            'webhooks_triggered',
            'processed_at',
            'created_at',
        ]


class WebhookTestSerializer(serializers.Serializer):
    """Serializer for webhook test response."""

    success = serializers.BooleanField()
    delivery_id = serializers.CharField()
    status_code = serializers.IntegerField(allow_null=True)
    error = serializers.CharField(allow_null=True)


class EventTypeSerializer(serializers.Serializer):
    """Serializer for listing available event types."""

    value = serializers.CharField()
    label = serializers.CharField()
    category = serializers.CharField()

    @staticmethod
    def get_event_types():
        """Get all event types grouped by category."""
        events = []
        for choice in Webhook.EventType.choices:
            value, label = choice
            category = value.split('.')[0].title()
            events.append({
                'value': value,
                'label': label,
                'category': category,
            })
        return events
