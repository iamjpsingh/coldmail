from rest_framework import serializers

from apps.sequences.models import (
    Sequence, SequenceStep, SequenceEnrollment,
    SequenceStepExecution, SequenceEvent
)
from apps.contacts.serializers import ContactSerializer


class SequenceStepSerializer(serializers.ModelSerializer):
    """Serializer for SequenceStep model."""

    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    delay_seconds = serializers.IntegerField(read_only=True)

    class Meta:
        model = SequenceStep
        fields = [
            'id', 'sequence', 'order', 'step_type', 'name',
            # Email fields
            'subject', 'content_html', 'content_text', 'template',
            # Delay fields
            'delay_value', 'delay_unit', 'delay_seconds',
            # Condition fields
            'condition_type', 'condition_value',
            'true_branch_step', 'false_branch_step',
            # Tag fields
            'tag_action', 'tag',
            # Webhook fields
            'webhook_url', 'webhook_method', 'webhook_headers', 'webhook_payload',
            # Task fields
            'task_title', 'task_description', 'task_assignee',
            # Stats
            'sent_count', 'opened_count', 'clicked_count',
            'replied_count', 'bounced_count',
            'open_rate', 'click_rate',
            'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'sent_count', 'opened_count', 'clicked_count',
            'replied_count', 'bounced_count', 'created_at', 'updated_at'
        ]


class SequenceStepCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating SequenceStep."""

    class Meta:
        model = SequenceStep
        fields = [
            'sequence', 'order', 'step_type', 'name',
            'subject', 'content_html', 'content_text', 'template',
            'delay_value', 'delay_unit',
            'condition_type', 'condition_value',
            'true_branch_step', 'false_branch_step',
            'tag_action', 'tag',
            'webhook_url', 'webhook_method', 'webhook_headers', 'webhook_payload',
            'task_title', 'task_description', 'task_assignee',
            'is_active',
        ]
        extra_kwargs = {
            'sequence': {'required': False},  # Set in view
            'order': {'required': False},  # Auto-assigned if not provided
        }


class SequenceSerializer(serializers.ModelSerializer):
    """Serializer for Sequence model."""

    steps = SequenceStepSerializer(many=True, read_only=True)
    step_count = serializers.IntegerField(read_only=True)
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    reply_rate = serializers.FloatField(read_only=True)
    email_account_email = serializers.CharField(
        source='email_account.email', read_only=True
    )
    created_by_email = serializers.CharField(
        source='created_by.email', read_only=True
    )

    class Meta:
        model = Sequence
        fields = [
            'id', 'workspace', 'name', 'description', 'status',
            # Sender settings
            'email_account', 'email_account_email',
            'from_name', 'reply_to',
            # Tracking
            'track_opens', 'track_clicks', 'include_unsubscribe_link',
            # Sending window
            'send_window_enabled', 'send_window_start', 'send_window_end',
            'send_window_days', 'send_window_timezone',
            # Throttling
            'max_emails_per_day', 'min_delay_between_emails',
            # Stop conditions
            'stop_on_reply', 'stop_on_click', 'stop_on_open',
            'stop_on_unsubscribe', 'stop_on_bounce',
            'stop_on_score_above', 'stop_on_score_below',
            # Stats
            'total_enrolled', 'active_enrolled', 'completed_count', 'stopped_count',
            'total_sent', 'total_opened', 'total_clicked', 'total_replied',
            'open_rate', 'click_rate', 'reply_rate',
            # Steps
            'steps', 'step_count',
            # Metadata
            'created_by', 'created_by_email',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'workspace', 'steps', 'step_count',
            'total_enrolled', 'active_enrolled', 'completed_count', 'stopped_count',
            'total_sent', 'total_opened', 'total_clicked', 'total_replied',
            'created_by', 'created_at', 'updated_at',
        ]


class SequenceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Sequence."""

    steps = SequenceStepCreateSerializer(many=True, required=False)

    class Meta:
        model = Sequence
        fields = [
            'name', 'description', 'email_account', 'from_name', 'reply_to',
            'track_opens', 'track_clicks', 'include_unsubscribe_link',
            'send_window_enabled', 'send_window_start', 'send_window_end',
            'send_window_days', 'send_window_timezone',
            'max_emails_per_day', 'min_delay_between_emails',
            'stop_on_reply', 'stop_on_click', 'stop_on_open',
            'stop_on_unsubscribe', 'stop_on_bounce',
            'stop_on_score_above', 'stop_on_score_below',
            'steps',
        ]

    def create(self, validated_data):
        steps_data = validated_data.pop('steps', [])
        sequence = Sequence.objects.create(**validated_data)

        for i, step_data in enumerate(steps_data):
            step_data['order'] = i
            SequenceStep.objects.create(sequence=sequence, **step_data)

        return sequence


class SequenceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a Sequence."""

    class Meta:
        model = Sequence
        fields = [
            'name', 'description', 'email_account', 'from_name', 'reply_to',
            'track_opens', 'track_clicks', 'include_unsubscribe_link',
            'send_window_enabled', 'send_window_start', 'send_window_end',
            'send_window_days', 'send_window_timezone',
            'max_emails_per_day', 'min_delay_between_emails',
            'stop_on_reply', 'stop_on_click', 'stop_on_open',
            'stop_on_unsubscribe', 'stop_on_bounce',
            'stop_on_score_above', 'stop_on_score_below',
        ]


class SequenceListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing sequences."""

    step_count = serializers.IntegerField(read_only=True)
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    reply_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Sequence
        fields = [
            'id', 'name', 'description', 'status',
            'email_account',
            'total_enrolled', 'active_enrolled', 'completed_count',
            'total_sent', 'total_opened', 'total_clicked', 'total_replied',
            'open_rate', 'click_rate', 'reply_rate',
            'step_count',
            'created_at', 'updated_at',
        ]


class SequenceEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for SequenceEnrollment model."""

    contact = ContactSerializer(read_only=True)
    sequence_name = serializers.CharField(source='sequence.name', read_only=True)
    current_step_name = serializers.SerializerMethodField()
    stop_reason_display = serializers.CharField(
        source='get_stop_reason_display', read_only=True
    )

    class Meta:
        model = SequenceEnrollment
        fields = [
            'id', 'sequence', 'sequence_name', 'contact',
            'status', 'stop_reason', 'stop_reason_display', 'stop_details',
            'current_step', 'current_step_name', 'current_step_index',
            'next_step_at', 'last_step_at',
            'enrolled_at', 'started_at', 'completed_at', 'stopped_at', 'paused_at',
            'emails_sent', 'emails_opened', 'emails_clicked', 'has_replied',
            'enrolled_by', 'enrollment_source',
            'retry_count', 'last_error',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'sequence', 'contact',
            'current_step', 'current_step_index',
            'next_step_at', 'last_step_at',
            'enrolled_at', 'started_at', 'completed_at', 'stopped_at',
            'emails_sent', 'emails_opened', 'emails_clicked', 'has_replied',
            'retry_count', 'last_error',
            'created_at', 'updated_at',
        ]

    def get_current_step_name(self, obj):
        if obj.current_step:
            return obj.current_step.name or f"Step {obj.current_step.order + 1}"
        return None


class SequenceEnrollmentListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing enrollments."""

    contact_email = serializers.CharField(source='contact.email', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    current_step_name = serializers.SerializerMethodField()

    class Meta:
        model = SequenceEnrollment
        fields = [
            'id', 'sequence', 'contact_email', 'contact_name',
            'status', 'current_step_index', 'current_step_name',
            'next_step_at',
            'emails_sent', 'emails_opened', 'emails_clicked', 'has_replied',
            'enrolled_at',
        ]

    def get_current_step_name(self, obj):
        if obj.current_step:
            return obj.current_step.name or f"Step {obj.current_step.order + 1}"
        return None


class EnrollContactSerializer(serializers.Serializer):
    """Serializer for enrolling a contact in a sequence."""

    contact_id = serializers.UUIDField()
    source = serializers.CharField(max_length=50, default='manual')


class BulkEnrollSerializer(serializers.Serializer):
    """Serializer for bulk enrolling contacts."""

    contact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=1000
    )
    source = serializers.CharField(max_length=50, default='bulk')


class SequenceStepExecutionSerializer(serializers.ModelSerializer):
    """Serializer for SequenceStepExecution model."""

    step_name = serializers.SerializerMethodField()
    step_type = serializers.CharField(source='step.step_type', read_only=True)

    class Meta:
        model = SequenceStepExecution
        fields = [
            'id', 'enrollment', 'step', 'step_name', 'step_type',
            'status', 'status_reason',
            'rendered_subject', 'rendered_html', 'rendered_text',
            'scheduled_at', 'executed_at', 'sent_at',
            'delivered_at', 'opened_at', 'clicked_at', 'replied_at',
            'message_id', 'email_account',
            'open_count', 'click_count', 'clicked_urls',
            'retry_count', 'last_error',
            'created_at', 'updated_at',
        ]

    def get_step_name(self, obj):
        return obj.step.name or f"Step {obj.step.order + 1}"


class SequenceEventSerializer(serializers.ModelSerializer):
    """Serializer for SequenceEvent model."""

    event_type_display = serializers.CharField(
        source='get_event_type_display', read_only=True
    )
    step_name = serializers.SerializerMethodField()
    contact_email = serializers.CharField(
        source='enrollment.contact.email', read_only=True
    )

    class Meta:
        model = SequenceEvent
        fields = [
            'id', 'enrollment', 'contact_email',
            'step', 'step_name',
            'event_type', 'event_type_display',
            'message', 'metadata', 'clicked_url',
            'ip_address', 'user_agent', 'device_type',
            'browser', 'country', 'is_bot',
            'created_at',
        ]

    def get_step_name(self, obj):
        if obj.step:
            return obj.step.name or f"Step {obj.step.order + 1}"
        return None


class SequenceStatsSerializer(serializers.Serializer):
    """Serializer for sequence statistics."""

    total_enrolled = serializers.IntegerField()
    active_enrolled = serializers.IntegerField()
    completed = serializers.IntegerField()
    stopped = serializers.IntegerField()
    total_sent = serializers.IntegerField()
    total_opened = serializers.IntegerField()
    total_clicked = serializers.IntegerField()
    total_replied = serializers.IntegerField()
    open_rate = serializers.FloatField()
    click_rate = serializers.FloatField()
    reply_rate = serializers.FloatField()
    steps = serializers.IntegerField()


class StepStatsSerializer(serializers.Serializer):
    """Serializer for step-level statistics."""

    order = serializers.IntegerField()
    type = serializers.CharField()
    name = serializers.CharField()
    sent = serializers.IntegerField()
    opened = serializers.IntegerField()
    clicked = serializers.IntegerField()
    replied = serializers.IntegerField()
    bounced = serializers.IntegerField()
    open_rate = serializers.FloatField()
    click_rate = serializers.FloatField()
