from rest_framework import serializers

from .models import Contact, Tag, ContactList, ContactActivity, CustomField, ImportJob


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    contact_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'contact_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'contact_count', 'created_at', 'updated_at']

    def get_contact_count(self, obj):
        return obj.contacts.count()


class TagCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tags."""

    class Meta:
        model = Tag
        fields = ['name', 'color']


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model."""

    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='tags'
    )
    full_name = serializers.CharField(read_only=True)
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    reply_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'company', 'job_title', 'phone', 'website', 'linkedin_url', 'twitter_handle',
            'city', 'state', 'country', 'timezone',
            'custom_fields', 'status', 'score', 'score_updated_at',
            'source', 'source_details',
            'tags', 'tag_ids',
            'emails_sent', 'emails_opened', 'emails_clicked', 'emails_replied', 'emails_bounced',
            'open_rate', 'click_rate', 'reply_rate',
            'last_emailed_at', 'last_opened_at', 'last_clicked_at', 'last_replied_at',
            'unsubscribed_at', 'unsubscribe_reason',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'full_name', 'open_rate', 'click_rate', 'reply_rate',
            'emails_sent', 'emails_opened', 'emails_clicked', 'emails_replied', 'emails_bounced',
            'last_emailed_at', 'last_opened_at', 'last_clicked_at', 'last_replied_at',
            'score_updated_at', 'created_at', 'updated_at'
        ]


class ContactCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contacts."""

    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Contact
        fields = [
            'email', 'first_name', 'last_name',
            'company', 'job_title', 'phone', 'website', 'linkedin_url', 'twitter_handle',
            'city', 'state', 'country', 'timezone',
            'custom_fields', 'source', 'source_details',
            'tag_ids', 'notes'
        ]

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        contact = Contact.objects.create(**validated_data)
        if tag_ids:
            contact.tags.set(tag_ids)
        return contact


class ContactUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating contacts."""

    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Contact
        fields = [
            'email', 'first_name', 'last_name',
            'company', 'job_title', 'phone', 'website', 'linkedin_url', 'twitter_handle',
            'city', 'state', 'country', 'timezone',
            'custom_fields', 'status', 'score',
            'source', 'source_details',
            'tag_ids', 'notes'
        ]

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        return instance


class ContactListSerializer(serializers.ModelSerializer):
    """Serializer for ContactList model."""

    class Meta:
        model = ContactList
        fields = [
            'id', 'name', 'description', 'list_type',
            'filter_criteria', 'contact_count', 'last_count_updated_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'contact_count', 'last_count_updated_at', 'created_at', 'updated_at']


class ContactListCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contact lists."""

    contact_ids = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = ContactList
        fields = ['name', 'description', 'list_type', 'filter_criteria', 'contact_ids']

    def create(self, validated_data):
        contact_ids = validated_data.pop('contact_ids', [])
        contact_list = ContactList.objects.create(**validated_data)
        if contact_ids and contact_list.list_type == ContactList.ListType.STATIC:
            contact_list.contacts.set(contact_ids)
        contact_list.update_contact_count()
        return contact_list


class ContactActivitySerializer(serializers.ModelSerializer):
    """Serializer for ContactActivity model."""

    class Meta:
        model = ContactActivity
        fields = [
            'id', 'activity_type', 'description', 'metadata',
            'campaign_id', 'sequence_id', 'email_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CustomFieldSerializer(serializers.ModelSerializer):
    """Serializer for CustomField model."""

    class Meta:
        model = CustomField
        fields = [
            'id', 'name', 'field_key', 'field_type', 'description',
            'is_required', 'default_value', 'options', 'display_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ImportJobSerializer(serializers.ModelSerializer):
    """Serializer for ImportJob model."""

    progress_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = ImportJob
        fields = [
            'id', 'file_name', 'file_type', 'field_mapping',
            'status', 'total_rows', 'processed_rows',
            'created_count', 'updated_count', 'skipped_count', 'error_count',
            'errors', 'progress_percentage',
            'started_at', 'completed_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'total_rows', 'processed_rows',
            'created_count', 'updated_count', 'skipped_count', 'error_count',
            'errors', 'progress_percentage', 'started_at', 'completed_at', 'created_at'
        ]


class BulkContactSerializer(serializers.Serializer):
    """Serializer for bulk contact operations."""

    contact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=1000
    )


class BulkTagSerializer(serializers.Serializer):
    """Serializer for bulk tag operations."""

    contact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=1000
    )
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )


class BulkListSerializer(serializers.Serializer):
    """Serializer for bulk list operations."""

    contact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=1000
    )
    list_id = serializers.UUIDField()


class ContactSearchSerializer(serializers.Serializer):
    """Serializer for contact search."""

    query = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Contact.Status.choices, required=False)
    tags = serializers.ListField(child=serializers.UUIDField(), required=False)
    min_score = serializers.IntegerField(required=False)
    max_score = serializers.IntegerField(required=False)
    company = serializers.CharField(required=False, allow_blank=True)
    job_title = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    source = serializers.CharField(required=False, allow_blank=True)
    has_opened = serializers.BooleanField(required=False)
    has_clicked = serializers.BooleanField(required=False)
    has_replied = serializers.BooleanField(required=False)


# Scoring serializers
from .models import ScoringRule, ScoreHistory, ScoreThreshold, ScoreDecayConfig


class ScoringRuleSerializer(serializers.ModelSerializer):
    """Serializer for ScoringRule model."""

    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = ScoringRule
        fields = [
            'id', 'name', 'description', 'is_active',
            'event_type', 'conditions', 'score_change',
            'max_applications', 'cooldown_hours', 'priority',
            'applications_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'applications_count', 'created_at', 'updated_at']

    def get_applications_count(self, obj):
        return obj.applications.count()


class ScoringRuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating scoring rules."""

    class Meta:
        model = ScoringRule
        fields = [
            'name', 'description', 'is_active',
            'event_type', 'conditions', 'score_change',
            'max_applications', 'cooldown_hours', 'priority'
        ]


class ScoreHistorySerializer(serializers.ModelSerializer):
    """Serializer for ScoreHistory model."""

    rule_name = serializers.CharField(source='rule.name', read_only=True, default=None)

    class Meta:
        model = ScoreHistory
        fields = [
            'id', 'previous_score', 'new_score', 'score_change',
            'reason', 'rule', 'rule_name', 'event_type', 'event_data',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ScoreThresholdSerializer(serializers.ModelSerializer):
    """Serializer for ScoreThreshold model."""

    contacts_count = serializers.SerializerMethodField()

    class Meta:
        model = ScoreThreshold
        fields = [
            'id', 'classification', 'min_score', 'max_score', 'color',
            'contacts_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'contacts_count', 'created_at', 'updated_at']

    def get_contacts_count(self, obj):
        from .models import Contact
        queryset = Contact.objects.filter(
            workspace=obj.workspace,
            status=Contact.Status.ACTIVE,
            score__gte=obj.min_score
        )
        if obj.max_score:
            queryset = queryset.filter(score__lte=obj.max_score)
        return queryset.count()


class ScoreDecayConfigSerializer(serializers.ModelSerializer):
    """Serializer for ScoreDecayConfig model."""

    class Meta:
        model = ScoreDecayConfig
        fields = [
            'id', 'is_enabled', 'decay_points', 'decay_interval_days',
            'min_score', 'inactivity_days', 'last_run_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run_at', 'created_at', 'updated_at']


class ScoreAdjustmentSerializer(serializers.Serializer):
    """Serializer for manual score adjustments."""

    score = serializers.IntegerField(required=False)
    adjustment = serializers.IntegerField(required=False)
    reason = serializers.CharField(max_length=200, required=False, default='Manual adjustment')

    def validate(self, data):
        if 'score' not in data and 'adjustment' not in data:
            raise serializers.ValidationError("Either 'score' or 'adjustment' is required")
        if 'score' in data and 'adjustment' in data:
            raise serializers.ValidationError("Provide either 'score' or 'adjustment', not both")
        return data


class ApplyEventSerializer(serializers.Serializer):
    """Serializer for applying scoring events."""

    event_type = serializers.ChoiceField(choices=ScoringRule.EventType.choices)
    event_data = serializers.DictField(required=False, default=dict)
