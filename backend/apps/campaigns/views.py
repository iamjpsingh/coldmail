from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import (
    EmailSignature,
    EmailTemplate,
    TemplateFolder,
    TemplateVersion,
    SnippetLibrary,
    Campaign,
    CampaignRecipient,
    CampaignEvent,
    CampaignLog,
    ABTestVariant,
)
from .serializers import (
    EmailSignatureSerializer,
    EmailSignatureCreateSerializer,
    EmailTemplateSerializer,
    EmailTemplateCreateSerializer,
    EmailTemplateUpdateSerializer,
    TemplateListSerializer,
    TemplatePreviewSerializer,
    TemplatePreviewResponseSerializer,
    TemplateValidationSerializer,
    TemplateValidationResponseSerializer,
    TemplateFolderSerializer,
    TemplateFolderCreateSerializer,
    TemplateVersionSerializer,
    SnippetLibrarySerializer,
    SnippetLibraryCreateSerializer,
    DuplicateTemplateSerializer,
    CampaignSerializer,
    CampaignCreateSerializer,
    CampaignUpdateSerializer,
    CampaignListSerializer,
    CampaignStatsSerializer,
    CampaignRecipientSerializer,
    CampaignEventSerializer,
    CampaignLogSerializer,
    ABTestVariantSerializer,
    ScheduleCampaignSerializer,
)
from .services import TemplateEngine, CampaignService


class EmailSignatureViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email signatures."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # TODO: Filter by workspace when auth is implemented
        return EmailSignature.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return EmailSignatureCreateSerializer
        return EmailSignatureSerializer

    def perform_create(self, serializer):
        # TODO: Set workspace from authenticated user
        serializer.save()

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set this signature as the default."""
        signature = self.get_object()
        signature.is_default = True
        signature.save()
        return Response(EmailSignatureSerializer(signature).data)


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email templates."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # TODO: Filter by workspace when auth is implemented
        queryset = EmailTemplate.objects.all()

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by folder
        folder_id = self.request.query_params.get('folder')
        if folder_id:
            queryset = queryset.filter(folders__id=folder_id)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(subject__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.select_related('signature', 'created_by')

    def get_serializer_class(self):
        if self.action == 'create':
            return EmailTemplateCreateSerializer
        if self.action in ['update', 'partial_update']:
            return EmailTemplateUpdateSerializer
        if self.action == 'list':
            return TemplateListSerializer
        return EmailTemplateSerializer

    def perform_create(self, serializer):
        # TODO: Set workspace from authenticated user
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def preview(self, request):
        """Preview a template with sample data."""
        serializer = TemplatePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        engine = TemplateEngine()
        result = engine.preview(
            subject=serializer.validated_data['subject'],
            content_html=serializer.validated_data['content_html'],
            content_text=serializer.validated_data.get('content_text', ''),
            sample_contact=serializer.validated_data.get('sample_contact'),
        )

        response_serializer = TemplatePreviewResponseSerializer({
            'subject': result.subject,
            'content_html': result.content_html,
            'content_text': result.content_text,
            'variables_used': result.variables_used,
            'missing_variables': result.missing_variables,
            'spintax_variations': result.spintax_variations,
        })

        return Response(response_serializer.data)

    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Validate a template."""
        serializer = TemplateValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        engine = TemplateEngine()
        result = engine.validate_template(
            subject=serializer.validated_data['subject'],
            content_html=serializer.validated_data['content_html'],
            content_text=serializer.validated_data.get('content_text', ''),
        )

        response_serializer = TemplateValidationResponseSerializer(result)
        return Response(response_serializer.data)

    @action(detail=False, methods=['get'])
    def variables(self, request):
        """Get list of available template variables."""
        engine = TemplateEngine()
        return Response(engine.get_available_variables())

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a template."""
        template = self.get_object()
        serializer = DuplicateTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create duplicate
        new_template = EmailTemplate.objects.create(
            workspace=template.workspace,
            name=serializer.validated_data['name'],
            subject=template.subject,
            content_html=template.content_html,
            content_text=template.content_text,
            category=template.category,
            description=template.description,
            signature=template.signature,
            include_signature=template.include_signature,
            variables=template.variables,
            has_spintax=template.has_spintax,
            is_shared=False,
            created_by=request.user,
        )

        # Copy folder associations
        new_template.folders.set(template.folders.all())

        return Response(
            EmailTemplateSerializer(new_template).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get version history for a template."""
        template = self.get_object()
        versions = template.versions.all()
        serializer = TemplateVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def save_version(self, request, pk=None):
        """Save current template state as a version."""
        template = self.get_object()

        # Get next version number
        last_version = template.versions.first()
        next_version = (last_version.version_number + 1) if last_version else 1

        change_notes = request.data.get('change_notes', '')

        version = TemplateVersion.objects.create(
            template=template,
            version_number=next_version,
            subject=template.subject,
            content_html=template.content_html,
            content_text=template.content_text,
            change_notes=change_notes,
            created_by=request.user,
        )

        return Response(
            TemplateVersionSerializer(version).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def restore_version(self, request, pk=None):
        """Restore a template to a specific version."""
        template = self.get_object()
        version_id = request.data.get('version_id')

        if not version_id:
            return Response(
                {'error': 'version_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            version = template.versions.get(id=version_id)
        except TemplateVersion.DoesNotExist:
            return Response(
                {'error': 'Version not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Restore template content
        template.subject = version.subject
        template.content_html = version.content_html
        template.content_text = version.content_text
        template.save()

        return Response(EmailTemplateSerializer(template).data)


class TemplateFolderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing template folders."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # TODO: Filter by workspace when auth is implemented
        queryset = TemplateFolder.objects.all()

        # Filter by parent (null for root folders)
        parent = self.request.query_params.get('parent')
        if parent == 'root':
            queryset = queryset.filter(parent__isnull=True)
        elif parent:
            queryset = queryset.filter(parent_id=parent)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return TemplateFolderCreateSerializer
        return TemplateFolderSerializer

    def perform_create(self, serializer):
        # TODO: Set workspace from authenticated user
        serializer.save()

    @action(detail=True, methods=['get'])
    def templates(self, request, pk=None):
        """Get templates in this folder."""
        folder = self.get_object()
        templates = folder.templates.all()
        serializer = TemplateListSerializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_templates(self, request, pk=None):
        """Add templates to this folder."""
        folder = self.get_object()
        template_ids = request.data.get('template_ids', [])

        templates = EmailTemplate.objects.filter(
            id__in=template_ids,
            workspace=folder.workspace
        )
        folder.templates.add(*templates)

        return Response({'added_count': templates.count()})

    @action(detail=True, methods=['post'])
    def remove_templates(self, request, pk=None):
        """Remove templates from this folder."""
        folder = self.get_object()
        template_ids = request.data.get('template_ids', [])

        templates = folder.templates.filter(id__in=template_ids)
        count = templates.count()
        folder.templates.remove(*templates)

        return Response({'removed_count': count})


class SnippetLibraryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reusable snippets."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # TODO: Filter by workspace when auth is implemented
        queryset = SnippetLibrary.objects.all()

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(shortcode__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SnippetLibraryCreateSerializer
        return SnippetLibrarySerializer

    def perform_create(self, serializer):
        # TODO: Set workspace from authenticated user
        serializer.save()

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of snippet categories."""
        categories = SnippetLibrary.objects.values_list(
            'category', flat=True
        ).distinct().order_by('category')
        return Response(list(filter(None, categories)))

    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Record snippet usage."""
        snippet = self.get_object()
        snippet.times_used += 1
        snippet.save(update_fields=['times_used'])
        return Response({'times_used': snippet.times_used})


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing campaigns."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # TODO: Filter by workspace when auth is implemented
        queryset = Campaign.objects.all()

        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.select_related('email_account', 'template', 'created_by')

    def get_serializer_class(self):
        if self.action == 'create':
            return CampaignCreateSerializer
        if self.action in ['update', 'partial_update']:
            return CampaignUpdateSerializer
        if self.action == 'list':
            return CampaignListSerializer
        return CampaignSerializer

    def perform_create(self, serializer):
        # TODO: Set workspace from authenticated user
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def prepare(self, request, pk=None):
        """Prepare campaign recipients."""
        campaign = self.get_object()

        if campaign.status != Campaign.Status.DRAFT:
            return Response(
                {'error': 'Can only prepare draft campaigns'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use Celery task for async processing
        from .tasks import prepare_campaign_recipients, schedule_campaign_recipients
        prepare_campaign_recipients.delay(str(campaign.id))

        return Response({
            'message': 'Recipient preparation started',
            'campaign_id': str(campaign.id)
        })

    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """Schedule campaign for sending."""
        campaign = self.get_object()
        serializer = ScheduleCampaignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if campaign.status not in [Campaign.Status.DRAFT]:
            return Response(
                {'error': 'Can only schedule draft campaigns'},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign.scheduled_at = serializer.validated_data['scheduled_at']
        campaign.timezone = serializer.validated_data.get('timezone', 'UTC')
        campaign.status = Campaign.Status.SCHEDULED
        campaign.sending_mode = Campaign.SendingMode.SCHEDULED
        campaign.save()

        # Schedule recipients
        from .tasks import schedule_campaign_recipients
        schedule_campaign_recipients.delay(str(campaign.id))

        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start sending the campaign immediately."""
        campaign = self.get_object()

        if campaign.status not in [Campaign.Status.DRAFT, Campaign.Status.SCHEDULED]:
            return Response(
                {'error': f'Cannot start campaign in {campaign.status} status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare recipients if not already done
        if campaign.total_recipients == 0:
            service = CampaignService(campaign)
            result = service.prepare_recipients()
            if not result.success:
                return Response(
                    {'error': result.message},
                    status=status.HTTP_400_BAD_REQUEST
                )
            service.schedule_recipients()

        # Start sending via Celery
        from .tasks import start_campaign_sending
        start_campaign_sending.delay(str(campaign.id))

        campaign.refresh_from_db()
        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause campaign sending."""
        campaign = self.get_object()
        service = CampaignService(campaign)
        success, message = service.pause_sending()

        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign.refresh_from_db()
        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume paused campaign."""
        campaign = self.get_object()
        service = CampaignService(campaign)
        success, message = service.resume_sending()

        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Continue processing
        from .tasks import process_campaign_queue
        process_campaign_queue.delay(str(campaign.id))

        campaign.refresh_from_db()
        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel campaign."""
        campaign = self.get_object()
        service = CampaignService(campaign)
        success, message = service.cancel_campaign()

        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign.refresh_from_db()
        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a campaign."""
        campaign = self.get_object()
        name = request.data.get('name', f"{campaign.name} (Copy)")

        new_campaign = Campaign.objects.create(
            workspace=campaign.workspace,
            name=name,
            description=campaign.description,
            template=campaign.template,
            subject=campaign.subject,
            content_html=campaign.content_html,
            content_text=campaign.content_text,
            email_account=campaign.email_account,
            from_name=campaign.from_name,
            reply_to=campaign.reply_to,
            sending_mode=campaign.sending_mode,
            min_delay_seconds=campaign.min_delay_seconds,
            max_delay_seconds=campaign.max_delay_seconds,
            batch_size=campaign.batch_size,
            batch_delay_minutes=campaign.batch_delay_minutes,
            timezone=campaign.timezone,
            spread_start_time=campaign.spread_start_time,
            spread_end_time=campaign.spread_end_time,
            spread_days=campaign.spread_days,
            is_ab_test=campaign.is_ab_test,
            ab_test_winner_criteria=campaign.ab_test_winner_criteria,
            ab_test_sample_size=campaign.ab_test_sample_size,
            ab_test_duration_hours=campaign.ab_test_duration_hours,
            track_opens=campaign.track_opens,
            track_clicks=campaign.track_clicks,
            use_custom_tracking_domain=campaign.use_custom_tracking_domain,
            tracking_domain=campaign.tracking_domain,
            include_unsubscribe_link=campaign.include_unsubscribe_link,
            created_by=request.user,
        )

        # Copy M2M relationships
        new_campaign.contact_lists.set(campaign.contact_lists.all())
        new_campaign.contact_tags.set(campaign.contact_tags.all())
        new_campaign.exclude_lists.set(campaign.exclude_lists.all())
        new_campaign.exclude_tags.set(campaign.exclude_tags.all())

        # Copy A/B variants
        for variant in campaign.ab_variants.all():
            ABTestVariant.objects.create(
                campaign=new_campaign,
                name=variant.name,
                subject=variant.subject,
                content_html=variant.content_html,
                content_text=variant.content_text,
                is_control=variant.is_control,
            )

        return Response(
            CampaignSerializer(new_campaign).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get campaign statistics."""
        campaign = self.get_object()
        service = CampaignService(campaign)
        stats = service.get_stats()
        return Response(CampaignStatsSerializer(stats).data)

    @action(detail=True, methods=['get'])
    def recipients(self, request, pk=None):
        """Get campaign recipients."""
        campaign = self.get_object()
        recipients = campaign.recipients.all()

        # Filter by status
        recipient_status = request.query_params.get('status')
        if recipient_status:
            recipients = recipients.filter(status=recipient_status)

        # Search
        search = request.query_params.get('search')
        if search:
            recipients = recipients.filter(
                Q(contact__email__icontains=search) |
                Q(contact__first_name__icontains=search) |
                Q(contact__last_name__icontains=search)
            )

        recipients = recipients.select_related('contact', 'ab_variant')[:100]
        serializer = CampaignRecipientSerializer(recipients, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get campaign logs."""
        campaign = self.get_object()
        logs = campaign.logs.all().select_related('created_by')[:50]
        serializer = CampaignLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get campaign events."""
        campaign = self.get_object()
        events = CampaignEvent.objects.filter(
            recipient__campaign=campaign
        ).select_related('recipient', 'recipient__contact')

        # Filter by event type
        event_type = request.query_params.get('type')
        if event_type:
            events = events.filter(event_type=event_type)

        events = events[:100]
        serializer = CampaignEventSerializer(events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def retry_failed(self, request, pk=None):
        """Retry failed recipients."""
        campaign = self.get_object()

        from .tasks import retry_failed_recipients
        retry_failed_recipients.delay(str(campaign.id))

        return Response({
            'message': 'Retry process started',
            'campaign_id': str(campaign.id)
        })

    @action(detail=True, methods=['post'])
    def select_ab_winner(self, request, pk=None):
        """Manually select A/B test winner."""
        campaign = self.get_object()

        if not campaign.is_ab_test:
            return Response(
                {'error': 'Campaign is not an A/B test'},
                status=status.HTTP_400_BAD_REQUEST
            )

        variant_id = request.data.get('variant_id')
        if variant_id:
            try:
                winner = campaign.ab_variants.get(id=variant_id)
                campaign.ab_variants.update(is_winner=False)
                winner.is_winner = True
                winner.save()
            except ABTestVariant.DoesNotExist:
                return Response(
                    {'error': 'Variant not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            service = CampaignService(campaign)
            winner = service.select_ab_winner()

        if winner:
            return Response(ABTestVariantSerializer(winner).data)

        return Response(
            {'error': 'Could not determine winner'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get campaign summary stats."""
        from django.db.models import Count, Sum

        # TODO: Filter by workspace
        queryset = Campaign.objects.all()

        summary = {
            'total': queryset.count(),
            'draft': queryset.filter(status=Campaign.Status.DRAFT).count(),
            'scheduled': queryset.filter(status=Campaign.Status.SCHEDULED).count(),
            'sending': queryset.filter(status=Campaign.Status.SENDING).count(),
            'paused': queryset.filter(status=Campaign.Status.PAUSED).count(),
            'completed': queryset.filter(status=Campaign.Status.COMPLETED).count(),
            'cancelled': queryset.filter(status=Campaign.Status.CANCELLED).count(),
        }

        # Aggregate stats from completed campaigns
        completed_stats = queryset.filter(
            status=Campaign.Status.COMPLETED
        ).aggregate(
            total_sent=Sum('sent_count'),
            total_opened=Sum('unique_opens'),
            total_clicked=Sum('unique_clicks'),
            total_replied=Sum('replied_count'),
        )

        summary.update({
            'total_emails_sent': completed_stats['total_sent'] or 0,
            'total_opens': completed_stats['total_opened'] or 0,
            'total_clicks': completed_stats['total_clicked'] or 0,
            'total_replies': completed_stats['total_replied'] or 0,
        })

        return Response(summary)
