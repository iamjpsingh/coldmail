from rest_framework import serializers

from .models import EmailAccount, EmailAccountLog


class EmailAccountSerializer(serializers.ModelSerializer):
    """Serializer for EmailAccount model."""

    can_send = serializers.ReadOnlyField()
    remaining_today = serializers.ReadOnlyField()
    remaining_this_hour = serializers.ReadOnlyField()
    is_oauth = serializers.ReadOnlyField()

    class Meta:
        model = EmailAccount
        fields = [
            'id', 'name', 'email', 'provider', 'status',
            'from_name', 'reply_to', 'signature',
            'daily_limit', 'hourly_limit',
            'emails_sent_today', 'emails_sent_this_hour',
            'is_warming_up', 'warmup_current_limit',
            'can_send', 'remaining_today', 'remaining_this_hour', 'is_oauth',
            'last_connection_test', 'last_connection_success',
            'last_email_sent_at', 'total_emails_sent',
            'bounce_rate', 'reputation_score',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'emails_sent_today', 'emails_sent_this_hour',
            'last_connection_test', 'last_connection_success',
            'last_email_sent_at', 'total_emails_sent',
            'bounce_rate', 'reputation_score',
            'created_at', 'updated_at',
        ]


class EmailAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SMTP email account."""

    class Meta:
        model = EmailAccount
        fields = [
            'name', 'email', 'provider',
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'smtp_use_tls', 'smtp_use_ssl',
            'imap_host', 'imap_port', 'imap_username', 'imap_password',
            'imap_use_ssl',
            'from_name', 'reply_to', 'signature',
            'daily_limit', 'hourly_limit',
        ]
        extra_kwargs = {
            'smtp_password': {'write_only': True},
            'imap_password': {'write_only': True},
        }

    def validate(self, data):
        provider = data.get('provider', EmailAccount.Provider.SMTP)

        # For SMTP provider, require SMTP configuration
        if provider == EmailAccount.Provider.SMTP:
            if not data.get('smtp_host'):
                raise serializers.ValidationError({
                    'smtp_host': 'SMTP host is required for SMTP provider.'
                })
            if not data.get('smtp_username'):
                raise serializers.ValidationError({
                    'smtp_username': 'SMTP username is required for SMTP provider.'
                })
            if not data.get('smtp_password'):
                raise serializers.ValidationError({
                    'smtp_password': 'SMTP password is required for SMTP provider.'
                })

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class EmailAccountUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating email account."""

    class Meta:
        model = EmailAccount
        fields = [
            'name', 'status',
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'smtp_use_tls', 'smtp_use_ssl',
            'imap_host', 'imap_port', 'imap_username', 'imap_password',
            'imap_use_ssl',
            'from_name', 'reply_to', 'signature',
            'daily_limit', 'hourly_limit',
            'is_warming_up', 'warmup_daily_increase', 'warmup_current_limit',
        ]
        extra_kwargs = {
            'smtp_password': {'write_only': True, 'required': False},
            'imap_password': {'write_only': True, 'required': False},
        }

    def update(self, instance, validated_data):
        # Only update password if provided
        if 'smtp_password' in validated_data and not validated_data['smtp_password']:
            validated_data.pop('smtp_password')
        if 'imap_password' in validated_data and not validated_data['imap_password']:
            validated_data.pop('imap_password')

        return super().update(instance, validated_data)


class EmailAccountLogSerializer(serializers.ModelSerializer):
    """Serializer for EmailAccountLog model."""

    class Meta:
        model = EmailAccountLog
        fields = [
            'id', 'log_type', 'message', 'details',
            'is_success', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ConnectionTestSerializer(serializers.Serializer):
    """Serializer for connection test request."""

    test_smtp = serializers.BooleanField(default=True)
    test_imap = serializers.BooleanField(default=False)


class SendTestEmailSerializer(serializers.Serializer):
    """Serializer for sending test email."""

    to_email = serializers.EmailField()
    subject = serializers.CharField(max_length=255, default="Test Email from ColdMail")
    body = serializers.CharField(default="This is a test email to verify your email account configuration.")
