from rest_framework import serializers

from .models import (
    EmailSignature,
    EmailTemplate,
    TemplateFolder,
    TemplateVersion,
    SnippetLibrary,
    Campaign,
    ABTestVariant,
    CampaignRecipient,
    CampaignEvent,
    CampaignLog,
)
from .services import TemplateEngine


class EmailSignatureSerializer(serializers.ModelSerializer):
    """Serializer for EmailSignature model."""

    class Meta:
        model = EmailSignature
        fields = [
            'id', 'name', 'content_html', 'content_text', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailSignatureCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating email signatures."""

    class Meta:
        model = EmailSignature
        fields = ['name', 'content_html', 'content_text', 'is_default']


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate model."""

    signature = EmailSignatureSerializer(read_only=True)
    signature_id = serializers.PrimaryKeyRelatedField(
        queryset=EmailSignature.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        source='signature'
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        default=''
    )
    folder_ids = serializers.SerializerMethodField()

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'subject', 'content_html', 'content_text',
            'category', 'description', 'signature', 'signature_id',
            'include_signature', 'variables', 'has_spintax',
            'times_used', 'last_used_at', 'is_shared',
            'created_by', 'created_by_name', 'folder_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'variables', 'has_spintax', 'times_used', 'last_used_at',
            'created_by', 'created_at', 'updated_at'
        ]

    def get_folder_ids(self, obj):
        return list(obj.folders.values_list('id', flat=True))


class EmailTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating email templates."""

    signature_id = serializers.PrimaryKeyRelatedField(
        queryset=EmailSignature.objects.all(),
        required=False,
        allow_null=True,
        source='signature'
    )
    folder_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'subject', 'content_html', 'content_text',
            'category', 'description', 'signature_id',
            'include_signature', 'is_shared', 'folder_ids'
        ]

    def validate(self, data):
        # Analyze template for variables and spintax
        engine = TemplateEngine()

        subject = data.get('subject', '')
        content_html = data.get('content_html', '')
        content_text = data.get('content_text', '')

        # Extract variables
        variables = set()
        variables.update(engine.extract_variables(subject))
        variables.update(engine.extract_variables(content_html))
        variables.update(engine.extract_variables(content_text))

        data['variables'] = list(variables)
        data['has_spintax'] = (
            engine.has_spintax(subject) or
            engine.has_spintax(content_html) or
            engine.has_spintax(content_text)
        )

        # Auto-generate plain text if not provided
        if not content_text and content_html:
            data['content_text'] = engine.html_to_text(content_html)

        return data

    def create(self, validated_data):
        folder_ids = validated_data.pop('folder_ids', [])
        template = EmailTemplate.objects.create(**validated_data)

        if folder_ids:
            folders = TemplateFolder.objects.filter(
                id__in=folder_ids,
                workspace=template.workspace
            )
            template.folders.set(folders)

        return template


class EmailTemplateUpdateSerializer(EmailTemplateCreateSerializer):
    """Serializer for updating email templates."""

    class Meta(EmailTemplateCreateSerializer.Meta):
        pass

    def update(self, instance, validated_data):
        folder_ids = validated_data.pop('folder_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if folder_ids is not None:
            folders = TemplateFolder.objects.filter(
                id__in=folder_ids,
                workspace=instance.workspace
            )
            instance.folders.set(folders)

        return instance


class TemplatePreviewSerializer(serializers.Serializer):
    """Serializer for template preview requests."""

    subject = serializers.CharField()
    content_html = serializers.CharField()
    content_text = serializers.CharField(required=False, allow_blank=True, default='')
    sample_contact = serializers.DictField(required=False, default=dict)


class TemplatePreviewResponseSerializer(serializers.Serializer):
    """Serializer for template preview responses."""

    subject = serializers.CharField()
    content_html = serializers.CharField()
    content_text = serializers.CharField()
    variables_used = serializers.ListField(child=serializers.CharField())
    missing_variables = serializers.ListField(child=serializers.CharField())
    spintax_variations = serializers.IntegerField()


class TemplateValidationSerializer(serializers.Serializer):
    """Serializer for template validation requests."""

    subject = serializers.CharField()
    content_html = serializers.CharField()
    content_text = serializers.CharField(required=False, allow_blank=True, default='')


class TemplateValidationResponseSerializer(serializers.Serializer):
    """Serializer for template validation responses."""

    is_valid = serializers.BooleanField()
    variables = serializers.ListField(child=serializers.CharField())
    known_variables = serializers.ListField(child=serializers.CharField())
    custom_variables = serializers.ListField(child=serializers.CharField())
    has_spintax = serializers.BooleanField()
    spintax_count = serializers.IntegerField()
    spintax_variations = serializers.IntegerField()
    warnings = serializers.ListField(child=serializers.CharField())


class TemplateFolderSerializer(serializers.ModelSerializer):
    """Serializer for TemplateFolder model."""

    template_count = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = TemplateFolder
        fields = [
            'id', 'name', 'parent', 'color', 'template_count',
            'children_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_template_count(self, obj):
        return obj.templates.count()

    def get_children_count(self, obj):
        return obj.children.count()


class TemplateFolderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating template folders."""

    class Meta:
        model = TemplateFolder
        fields = ['name', 'parent', 'color']


class TemplateVersionSerializer(serializers.ModelSerializer):
    """Serializer for TemplateVersion model."""

    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        default=''
    )

    class Meta:
        model = TemplateVersion
        fields = [
            'id', 'version_number', 'subject', 'content_html', 'content_text',
            'change_notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'version_number', 'created_by', 'created_at']


class SnippetLibrarySerializer(serializers.ModelSerializer):
    """Serializer for SnippetLibrary model."""

    class Meta:
        model = SnippetLibrary
        fields = [
            'id', 'name', 'shortcode', 'content_html', 'content_text',
            'description', 'category', 'times_used', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'times_used', 'created_at', 'updated_at']


class SnippetLibraryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating snippets."""

    class Meta:
        model = SnippetLibrary
        fields = ['name', 'shortcode', 'content_html', 'content_text', 'description', 'category']

    def validate_shortcode(self, value):
        # Ensure shortcode is lowercase and alphanumeric with underscores
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError(
                "Shortcode must start with a letter and contain only lowercase letters, numbers, and underscores"
            )
        return value


class DuplicateTemplateSerializer(serializers.Serializer):
    """Serializer for duplicating templates."""

    name = serializers.CharField(max_length=200)


class TemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for template lists."""

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'subject', 'category', 'has_spintax',
            'times_used', 'is_shared', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


# ============ Campaign Serializers ============

class ABTestVariantSerializer(serializers.ModelSerializer):
    """Serializer for A/B test variants."""

    class Meta:
        model = ABTestVariant
        fields = [
            'id', 'name', 'subject', 'content_html', 'content_text',
            'sent_count', 'opened_count', 'clicked_count', 'replied_count',
            'is_winner', 'is_control', 'open_rate', 'click_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sent_count', 'opened_count', 'clicked_count', 'replied_count',
            'is_winner', 'open_rate', 'click_rate', 'created_at', 'updated_at'
        ]


class ABTestVariantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating A/B test variants."""

    class Meta:
        model = ABTestVariant
        fields = ['name', 'subject', 'content_html', 'content_text', 'is_control']


class CampaignRecipientSerializer(serializers.ModelSerializer):
    """Serializer for campaign recipients."""

    contact_email = serializers.CharField(source='contact.email', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    ab_variant_name = serializers.CharField(source='ab_variant.name', read_only=True, default='')

    class Meta:
        model = CampaignRecipient
        fields = [
            'id', 'contact', 'contact_email', 'contact_name',
            'status', 'status_reason', 'ab_variant', 'ab_variant_name',
            'rendered_subject', 'scheduled_at', 'send_after',
            'queued_at', 'sent_at', 'delivered_at', 'opened_at',
            'clicked_at', 'replied_at', 'bounced_at', 'unsubscribed_at',
            'open_count', 'click_count', 'message_id',
            'retry_count', 'last_error', 'created_at'
        ]
        read_only_fields = fields


class CampaignEventSerializer(serializers.ModelSerializer):
    """Serializer for campaign events."""

    class Meta:
        model = CampaignEvent
        fields = [
            'id', 'event_type', 'metadata', 'clicked_url',
            'ip_address', 'user_agent', 'device_type', 'browser',
            'os', 'country', 'city', 'is_bot', 'created_at'
        ]
        read_only_fields = fields


class CampaignLogSerializer(serializers.ModelSerializer):
    """Serializer for campaign logs."""

    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        default=''
    )

    class Meta:
        model = CampaignLog
        fields = [
            'id', 'log_type', 'message', 'details',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = fields


class CampaignSerializer(serializers.ModelSerializer):
    """Full serializer for Campaign model."""

    email_account_name = serializers.CharField(
        source='email_account.name',
        read_only=True,
        default=''
    )
    email_account_email = serializers.CharField(
        source='email_account.email',
        read_only=True,
        default=''
    )
    template_name = serializers.CharField(
        source='template.name',
        read_only=True,
        default=''
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        default=''
    )
    ab_variants = ABTestVariantSerializer(many=True, read_only=True)
    contact_list_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    contact_tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    exclude_list_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    exclude_tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'status',
            'template', 'template_name', 'subject', 'content_html', 'content_text',
            'email_account', 'email_account_name', 'email_account_email',
            'from_name', 'reply_to',
            'contact_lists', 'contact_list_ids', 'contact_tags', 'contact_tag_ids',
            'exclude_lists', 'exclude_list_ids', 'exclude_tags', 'exclude_tag_ids',
            'sending_mode', 'min_delay_seconds', 'max_delay_seconds',
            'batch_size', 'batch_delay_minutes',
            'scheduled_at', 'timezone',
            'spread_start_time', 'spread_end_time', 'spread_days',
            'is_ab_test', 'ab_test_winner_criteria', 'ab_test_sample_size',
            'ab_test_duration_hours', 'ab_variants',
            'track_opens', 'track_clicks', 'use_custom_tracking_domain',
            'tracking_domain', 'include_unsubscribe_link',
            'total_recipients', 'sent_count', 'delivered_count',
            'opened_count', 'clicked_count', 'replied_count',
            'bounced_count', 'unsubscribed_count', 'complained_count', 'failed_count',
            'unique_opens', 'unique_clicks',
            'open_rate', 'click_rate', 'reply_rate', 'bounce_rate', 'progress_percentage',
            'started_at', 'completed_at', 'paused_at',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'total_recipients', 'sent_count', 'delivered_count',
            'opened_count', 'clicked_count', 'replied_count',
            'bounced_count', 'unsubscribed_count', 'complained_count', 'failed_count',
            'unique_opens', 'unique_clicks',
            'open_rate', 'click_rate', 'reply_rate', 'bounce_rate', 'progress_percentage',
            'started_at', 'completed_at', 'paused_at',
            'created_by', 'created_at', 'updated_at'
        ]


class CampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating campaigns."""

    contact_list_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list
    )
    contact_tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list
    )
    exclude_list_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list
    )
    exclude_tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list
    )
    ab_variants = ABTestVariantCreateSerializer(many=True, required=False)

    class Meta:
        model = Campaign
        fields = [
            'name', 'description', 'template', 'subject', 'content_html', 'content_text',
            'email_account', 'from_name', 'reply_to',
            'contact_list_ids', 'contact_tag_ids', 'exclude_list_ids', 'exclude_tag_ids',
            'sending_mode', 'min_delay_seconds', 'max_delay_seconds',
            'batch_size', 'batch_delay_minutes',
            'scheduled_at', 'timezone',
            'spread_start_time', 'spread_end_time', 'spread_days',
            'is_ab_test', 'ab_test_winner_criteria', 'ab_test_sample_size',
            'ab_test_duration_hours', 'ab_variants',
            'track_opens', 'track_clicks', 'use_custom_tracking_domain',
            'tracking_domain', 'include_unsubscribe_link',
        ]

    def validate(self, data):
        # Analyze content for variables and spintax
        engine = TemplateEngine()

        subject = data.get('subject', '')
        content_html = data.get('content_html', '')
        content_text = data.get('content_text', '')

        # Auto-generate plain text if not provided
        if not content_text and content_html:
            data['content_text'] = engine.html_to_text(content_html)

        # Validate A/B testing setup
        if data.get('is_ab_test'):
            ab_variants = data.get('ab_variants', [])
            if len(ab_variants) < 2:
                raise serializers.ValidationError({
                    'ab_variants': 'A/B testing requires at least 2 variants'
                })

        return data

    def create(self, validated_data):
        from apps.contacts.models import ContactList, Tag

        contact_list_ids = validated_data.pop('contact_list_ids', [])
        contact_tag_ids = validated_data.pop('contact_tag_ids', [])
        exclude_list_ids = validated_data.pop('exclude_list_ids', [])
        exclude_tag_ids = validated_data.pop('exclude_tag_ids', [])
        ab_variants_data = validated_data.pop('ab_variants', [])

        campaign = Campaign.objects.create(**validated_data)

        # Set M2M relationships
        if contact_list_ids:
            lists = ContactList.objects.filter(
                id__in=contact_list_ids,
                workspace=campaign.workspace
            )
            campaign.contact_lists.set(lists)

        if contact_tag_ids:
            tags = Tag.objects.filter(
                id__in=contact_tag_ids,
                workspace=campaign.workspace
            )
            campaign.contact_tags.set(tags)

        if exclude_list_ids:
            lists = ContactList.objects.filter(
                id__in=exclude_list_ids,
                workspace=campaign.workspace
            )
            campaign.exclude_lists.set(lists)

        if exclude_tag_ids:
            tags = Tag.objects.filter(
                id__in=exclude_tag_ids,
                workspace=campaign.workspace
            )
            campaign.exclude_tags.set(tags)

        # Create A/B variants
        for variant_data in ab_variants_data:
            ABTestVariant.objects.create(campaign=campaign, **variant_data)

        return campaign


class CampaignUpdateSerializer(CampaignCreateSerializer):
    """Serializer for updating campaigns."""

    class Meta(CampaignCreateSerializer.Meta):
        pass

    def update(self, instance, validated_data):
        from apps.contacts.models import ContactList, Tag

        # Only allow updating draft campaigns
        if instance.status != Campaign.Status.DRAFT:
            raise serializers.ValidationError(
                "Can only update campaigns in draft status"
            )

        contact_list_ids = validated_data.pop('contact_list_ids', None)
        contact_tag_ids = validated_data.pop('contact_tag_ids', None)
        exclude_list_ids = validated_data.pop('exclude_list_ids', None)
        exclude_tag_ids = validated_data.pop('exclude_tag_ids', None)
        ab_variants_data = validated_data.pop('ab_variants', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update M2M relationships
        if contact_list_ids is not None:
            lists = ContactList.objects.filter(
                id__in=contact_list_ids,
                workspace=instance.workspace
            )
            instance.contact_lists.set(lists)

        if contact_tag_ids is not None:
            tags = Tag.objects.filter(
                id__in=contact_tag_ids,
                workspace=instance.workspace
            )
            instance.contact_tags.set(tags)

        if exclude_list_ids is not None:
            lists = ContactList.objects.filter(
                id__in=exclude_list_ids,
                workspace=instance.workspace
            )
            instance.exclude_lists.set(lists)

        if exclude_tag_ids is not None:
            tags = Tag.objects.filter(
                id__in=exclude_tag_ids,
                workspace=instance.workspace
            )
            instance.exclude_tags.set(tags)

        # Update A/B variants
        if ab_variants_data is not None:
            instance.ab_variants.all().delete()
            for variant_data in ab_variants_data:
                ABTestVariant.objects.create(campaign=instance, **variant_data)

        return instance


class CampaignListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for campaign lists."""

    email_account_email = serializers.CharField(
        source='email_account.email',
        read_only=True,
        default=''
    )

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'status', 'email_account_email',
            'total_recipients', 'sent_count', 'open_rate', 'click_rate',
            'progress_percentage', 'scheduled_at', 'started_at', 'completed_at',
            'is_ab_test', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class CampaignStatsSerializer(serializers.Serializer):
    """Serializer for campaign statistics."""

    total_recipients = serializers.IntegerField()
    sent = serializers.IntegerField()
    delivered = serializers.IntegerField()
    opened = serializers.IntegerField()
    unique_opens = serializers.IntegerField()
    clicked = serializers.IntegerField()
    unique_clicks = serializers.IntegerField()
    replied = serializers.IntegerField()
    bounced = serializers.IntegerField()
    unsubscribed = serializers.IntegerField()
    complained = serializers.IntegerField()
    failed = serializers.IntegerField()
    open_rate = serializers.FloatField()
    click_rate = serializers.FloatField()
    reply_rate = serializers.FloatField()
    bounce_rate = serializers.FloatField()
    progress = serializers.FloatField()


class ScheduleCampaignSerializer(serializers.Serializer):
    """Serializer for scheduling a campaign."""

    scheduled_at = serializers.DateTimeField()
    timezone = serializers.CharField(required=False, default='UTC')
