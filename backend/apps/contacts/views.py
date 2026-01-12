from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Contact, Tag, ContactList, ContactActivity, CustomField, ImportJob
from .serializers import (
    ContactSerializer,
    ContactCreateSerializer,
    ContactUpdateSerializer,
    TagSerializer,
    TagCreateSerializer,
    ContactListSerializer,
    ContactListCreateSerializer,
    ContactActivitySerializer,
    CustomFieldSerializer,
    ImportJobSerializer,
    BulkContactSerializer,
    BulkTagSerializer,
    BulkListSerializer,
    ContactSearchSerializer,
)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tags."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # For now, return all tags for the user
        # Later this will be filtered by workspace
        return Tag.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return TagCreateSerializer
        return TagSerializer

    def perform_create(self, serializer):
        # For now, we'll need to handle workspace later
        # This is a placeholder - workspace will be required
        workspace = self.request.user.workspaces.first()
        if workspace:
            serializer.save(workspace=workspace)


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for managing contacts."""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'source']
    search_fields = ['email', 'first_name', 'last_name', 'company', 'job_title']
    ordering_fields = ['created_at', 'updated_at', 'email', 'score', 'last_emailed_at']
    ordering = ['-created_at']

    def get_queryset(self):
        # For now, return all contacts for the user's workspaces
        # Later this will be filtered by selected workspace
        user_workspaces = self.request.user.workspaces.all()
        return Contact.objects.filter(workspace__in=user_workspaces).prefetch_related('tags')

    def get_serializer_class(self):
        if self.action == 'create':
            return ContactCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ContactUpdateSerializer
        return ContactSerializer

    def perform_create(self, serializer):
        # Use the user's first workspace for now
        workspace = self.request.user.workspaces.first()
        if workspace:
            serializer.save(workspace=workspace)

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced search for contacts."""
        serializer = ContactSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        queryset = self.get_queryset()

        # Text search
        if data.get('query'):
            query = data['query']
            queryset = queryset.filter(
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(company__icontains=query) |
                Q(job_title__icontains=query)
            )

        # Status filter
        if data.get('status'):
            queryset = queryset.filter(status=data['status'])

        # Tags filter
        if data.get('tags'):
            queryset = queryset.filter(tags__id__in=data['tags'])

        # Score range
        if data.get('min_score') is not None:
            queryset = queryset.filter(score__gte=data['min_score'])
        if data.get('max_score') is not None:
            queryset = queryset.filter(score__lte=data['max_score'])

        # Company/job title filter
        if data.get('company'):
            queryset = queryset.filter(company__icontains=data['company'])
        if data.get('job_title'):
            queryset = queryset.filter(job_title__icontains=data['job_title'])

        # Location filter
        if data.get('country'):
            queryset = queryset.filter(country__iexact=data['country'])
        if data.get('city'):
            queryset = queryset.filter(city__icontains=data['city'])

        # Source filter
        if data.get('source'):
            queryset = queryset.filter(source__iexact=data['source'])

        # Engagement filters
        if data.get('has_opened') is not None:
            if data['has_opened']:
                queryset = queryset.filter(emails_opened__gt=0)
            else:
                queryset = queryset.filter(emails_opened=0)

        if data.get('has_clicked') is not None:
            if data['has_clicked']:
                queryset = queryset.filter(emails_clicked__gt=0)
            else:
                queryset = queryset.filter(emails_clicked=0)

        if data.get('has_replied') is not None:
            if data['has_replied']:
                queryset = queryset.filter(emails_replied__gt=0)
            else:
                queryset = queryset.filter(emails_replied=0)

        queryset = queryset.distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ContactSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ContactSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Get activity timeline for a contact."""
        contact = self.get_object()
        activities = contact.activities.all()[:100]
        serializer = ContactActivitySerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Delete multiple contacts."""
        serializer = BulkContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_ids = serializer.validated_data['contact_ids']
        queryset = self.get_queryset().filter(id__in=contact_ids)
        count = queryset.count()
        queryset.delete()

        return Response({'deleted_count': count})

    @action(detail=False, methods=['post'])
    def bulk_add_tags(self, request):
        """Add tags to multiple contacts."""
        serializer = BulkTagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_ids = serializer.validated_data['contact_ids']
        tag_ids = serializer.validated_data['tag_ids']

        contacts = self.get_queryset().filter(id__in=contact_ids)
        tags = Tag.objects.filter(id__in=tag_ids)

        for contact in contacts:
            contact.tags.add(*tags)

        return Response({'updated_count': contacts.count()})

    @action(detail=False, methods=['post'])
    def bulk_remove_tags(self, request):
        """Remove tags from multiple contacts."""
        serializer = BulkTagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_ids = serializer.validated_data['contact_ids']
        tag_ids = serializer.validated_data['tag_ids']

        contacts = self.get_queryset().filter(id__in=contact_ids)
        tags = Tag.objects.filter(id__in=tag_ids)

        for contact in contacts:
            contact.tags.remove(*tags)

        return Response({'updated_count': contacts.count()})

    @action(detail=False, methods=['post'])
    def bulk_add_to_list(self, request):
        """Add contacts to a list."""
        serializer = BulkListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_ids = serializer.validated_data['contact_ids']
        list_id = serializer.validated_data['list_id']

        try:
            contact_list = ContactList.objects.get(id=list_id)
        except ContactList.DoesNotExist:
            return Response(
                {'error': 'List not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if contact_list.list_type != ContactList.ListType.STATIC:
            return Response(
                {'error': 'Can only add contacts to static lists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        contacts = self.get_queryset().filter(id__in=contact_ids)
        contact_list.contacts.add(*contacts)
        contact_list.update_contact_count()

        return Response({'added_count': contacts.count()})

    @action(detail=False, methods=['post'])
    def bulk_remove_from_list(self, request):
        """Remove contacts from a list."""
        serializer = BulkListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_ids = serializer.validated_data['contact_ids']
        list_id = serializer.validated_data['list_id']

        try:
            contact_list = ContactList.objects.get(id=list_id)
        except ContactList.DoesNotExist:
            return Response(
                {'error': 'List not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if contact_list.list_type != ContactList.ListType.STATIC:
            return Response(
                {'error': 'Can only remove contacts from static lists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        contacts = self.get_queryset().filter(id__in=contact_ids)
        contact_list.contacts.remove(*contacts)
        contact_list.update_contact_count()

        return Response({'removed_count': contacts.count()})

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export contacts to CSV."""
        import csv
        from django.http import HttpResponse

        queryset = self.get_queryset()

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        tag_ids = request.query_params.getlist('tags')
        if tag_ids:
            queryset = queryset.filter(tags__id__in=tag_ids)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contacts.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Email', 'First Name', 'Last Name', 'Company', 'Job Title',
            'Phone', 'Website', 'LinkedIn', 'Twitter',
            'City', 'State', 'Country', 'Timezone',
            'Score', 'Status', 'Source', 'Notes',
            'Emails Sent', 'Emails Opened', 'Emails Clicked', 'Emails Replied',
            'Created At'
        ])

        for contact in queryset:
            writer.writerow([
                contact.email, contact.first_name, contact.last_name,
                contact.company, contact.job_title,
                contact.phone, contact.website, contact.linkedin_url, contact.twitter_handle,
                contact.city, contact.state, contact.country, contact.timezone,
                contact.score, contact.status, contact.source, contact.notes,
                contact.emails_sent, contact.emails_opened, contact.emails_clicked, contact.emails_replied,
                contact.created_at.isoformat()
            ])

        return response


class ContactListViewSet(viewsets.ModelViewSet):
    """ViewSet for managing contact lists."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_workspaces = self.request.user.workspaces.all()
        return ContactList.objects.filter(workspace__in=user_workspaces)

    def get_serializer_class(self):
        if self.action == 'create':
            return ContactListCreateSerializer
        return ContactListSerializer

    def perform_create(self, serializer):
        workspace = self.request.user.workspaces.first()
        if workspace:
            serializer.save(workspace=workspace)

    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Get contacts in a list."""
        contact_list = self.get_object()
        contacts = contact_list.get_contacts()

        page = self.paginate_queryset(contacts)
        if page is not None:
            serializer = ContactSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def refresh_count(self, request, pk=None):
        """Refresh the contact count for a list."""
        contact_list = self.get_object()
        contact_list.update_contact_count()
        return Response({'contact_count': contact_list.contact_count})


class CustomFieldViewSet(viewsets.ModelViewSet):
    """ViewSet for managing custom fields."""

    permission_classes = [IsAuthenticated]
    serializer_class = CustomFieldSerializer

    def get_queryset(self):
        user_workspaces = self.request.user.workspaces.all()
        return CustomField.objects.filter(workspace__in=user_workspaces)

    def perform_create(self, serializer):
        workspace = self.request.user.workspaces.first()
        if workspace:
            serializer.save(workspace=workspace)


class ImportJobViewSet(viewsets.ModelViewSet):
    """ViewSet for managing import jobs."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = ImportJobSerializer

    def get_queryset(self):
        user_workspaces = self.request.user.workspaces.all()
        return ImportJob.objects.filter(workspace__in=user_workspaces)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a file for import."""
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Determine file type
        file_name = file.name.lower()
        if file_name.endswith('.csv'):
            file_type = ImportJob.FileType.CSV
        elif file_name.endswith(('.xlsx', '.xls')):
            file_type = ImportJob.FileType.EXCEL
        elif file_name.endswith('.json'):
            file_type = ImportJob.FileType.JSON
        else:
            return Response(
                {'error': 'Unsupported file type. Use CSV, Excel, or JSON.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save file
        import os
        from django.conf import settings
        from django.utils import timezone

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(upload_dir, f"{timestamp}_{file.name}")

        with open(file_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        # Create import job
        workspace = request.user.workspaces.first()
        import_job = ImportJob.objects.create(
            workspace=workspace,
            user=request.user,
            file_name=file.name,
            file_type=file_type,
            file_path=file_path,
            status=ImportJob.Status.PENDING
        )

        # Get file preview (first few rows)
        preview = self._get_file_preview(file_path, file_type)

        return Response({
            'import_job_id': str(import_job.id),
            'file_name': file.name,
            'file_type': file_type,
            'preview': preview
        })

    def _get_file_preview(self, file_path, file_type):
        """Get preview of first few rows."""
        try:
            if file_type == ImportJob.FileType.CSV:
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    rows = []
                    for i, row in enumerate(reader):
                        if i >= 5:
                            break
                        rows.append(row)
                return {'headers': headers, 'rows': rows}

            elif file_type == ImportJob.FileType.EXCEL:
                import openpyxl
                wb = openpyxl.load_workbook(file_path, read_only=True)
                sheet = wb.active
                rows = list(sheet.iter_rows(max_row=6, values_only=True))
                headers = [str(h) if h else '' for h in rows[0]] if rows else []
                data_rows = [dict(zip(headers, row)) for row in rows[1:6]]
                return {'headers': headers, 'rows': data_rows}

            elif file_type == ImportJob.FileType.JSON:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    headers = list(data[0].keys()) if isinstance(data[0], dict) else []
                    return {'headers': headers, 'rows': data[:5]}
                return {'headers': [], 'rows': []}

        except Exception as e:
            return {'error': str(e)}

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start the import process."""
        import_job = self.get_object()

        if import_job.status != ImportJob.Status.PENDING:
            return Response(
                {'error': 'Import job is not pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get field mapping from request
        field_mapping = request.data.get('field_mapping', {})
        import_job.field_mapping = field_mapping
        import_job.save()

        # Queue the import task (Celery)
        from .tasks import process_import_job
        process_import_job.delay(str(import_job.id))

        return Response({
            'status': 'queued',
            'import_job_id': str(import_job.id)
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an import job."""
        import_job = self.get_object()

        if import_job.status not in [ImportJob.Status.PENDING, ImportJob.Status.PROCESSING]:
            return Response(
                {'error': 'Cannot cancel this import job'},
                status=status.HTTP_400_BAD_REQUEST
            )

        import_job.status = ImportJob.Status.CANCELLED
        import_job.save()

        return Response({'status': 'cancelled'})


# Scoring imports
from .models import ScoringRule, ScoreHistory, ScoreThreshold, ScoreDecayConfig
from .serializers import (
    ScoringRuleSerializer,
    ScoringRuleCreateSerializer,
    ScoreHistorySerializer,
    ScoreThresholdSerializer,
    ScoreDecayConfigSerializer,
    ScoreAdjustmentSerializer,
    ApplyEventSerializer,
)
from .services import ScoringEngine


class ScoringRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing scoring rules."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_workspaces = self.request.user.workspaces.all()
        return ScoringRule.objects.filter(workspace__in=user_workspaces)

    def get_serializer_class(self):
        if self.action == 'create':
            return ScoringRuleCreateSerializer
        return ScoringRuleSerializer

    def perform_create(self, serializer):
        workspace = self.request.user.workspaces.first()
        if workspace:
            serializer.save(workspace=workspace)

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle rule active status."""
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save(update_fields=['is_active'])
        return Response({'is_active': rule.is_active})


class ScoreThresholdViewSet(viewsets.ModelViewSet):
    """ViewSet for managing score thresholds."""

    permission_classes = [IsAuthenticated]
    serializer_class = ScoreThresholdSerializer

    def get_queryset(self):
        user_workspaces = self.request.user.workspaces.all()
        return ScoreThreshold.objects.filter(workspace__in=user_workspaces)

    def perform_create(self, serializer):
        workspace = self.request.user.workspaces.first()
        if workspace:
            serializer.save(workspace=workspace)


class ScoreDecayConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for managing score decay config."""

    permission_classes = [IsAuthenticated]
    serializer_class = ScoreDecayConfigSerializer

    def get_queryset(self):
        user_workspaces = self.request.user.workspaces.all()
        return ScoreDecayConfig.objects.filter(workspace__in=user_workspaces)

    def perform_create(self, serializer):
        workspace = self.request.user.workspaces.first()
        if workspace:
            serializer.save(workspace=workspace)

    @action(detail=True, methods=['post'])
    def run_decay(self, request, pk=None):
        """Manually run score decay."""
        config = self.get_object()
        engine = ScoringEngine(config.workspace)
        result = engine.run_score_decay()
        return Response(result)


class ScoringViewSet(viewsets.ViewSet):
    """ViewSet for scoring operations."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get scoring statistics."""
        workspace = request.user.workspaces.first()
        if not workspace:
            return Response({'error': 'No workspace found'}, status=status.HTTP_404_NOT_FOUND)

        engine = ScoringEngine(workspace)
        stats = engine.get_score_stats()
        return Response(stats)

    @action(detail=False, methods=['get'])
    def hot_leads(self, request):
        """Get hot leads."""
        workspace = request.user.workspaces.first()
        if not workspace:
            return Response({'error': 'No workspace found'}, status=status.HTTP_404_NOT_FOUND)

        limit = int(request.query_params.get('limit', 50))
        engine = ScoringEngine(workspace)
        leads = engine.get_hot_leads(limit=limit)

        serializer = ContactSerializer(leads, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='contact/(?P<contact_id>[^/.]+)/adjust')
    def adjust_score(self, request, contact_id=None):
        """Adjust a contact's score."""
        workspace = request.user.workspaces.first()
        if not workspace:
            return Response({'error': 'No workspace found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            contact = Contact.objects.get(id=contact_id, workspace=workspace)
        except Contact.DoesNotExist:
            return Response({'error': 'Contact not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ScoreAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        engine = ScoringEngine(workspace)

        if 'score' in data:
            result = engine.set_score(contact, data['score'], data.get('reason', 'Manual adjustment'))
        else:
            result = engine.adjust_score(contact, data['adjustment'], data.get('reason', 'Manual adjustment'))

        return Response({
            'success': result.success,
            'previous_score': result.previous_score,
            'new_score': result.new_score,
            'score_change': result.score_change,
            'message': result.message
        })

    @action(detail=False, methods=['post'], url_path='contact/(?P<contact_id>[^/.]+)/apply-event')
    def apply_event(self, request, contact_id=None):
        """Apply a scoring event to a contact."""
        workspace = request.user.workspaces.first()
        if not workspace:
            return Response({'error': 'No workspace found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            contact = Contact.objects.get(id=contact_id, workspace=workspace)
        except Contact.DoesNotExist:
            return Response({'error': 'Contact not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ApplyEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        engine = ScoringEngine(workspace)
        result = engine.apply_event(contact, data['event_type'], data.get('event_data', {}))

        return Response({
            'success': result.success,
            'previous_score': result.previous_score,
            'new_score': result.new_score,
            'score_change': result.score_change,
            'rules_applied': result.rules_applied,
            'message': result.message
        })

    @action(detail=False, methods=['get'], url_path='contact/(?P<contact_id>[^/.]+)/history')
    def score_history(self, request, contact_id=None):
        """Get score history for a contact."""
        workspace = request.user.workspaces.first()
        if not workspace:
            return Response({'error': 'No workspace found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            contact = Contact.objects.get(id=contact_id, workspace=workspace)
        except Contact.DoesNotExist:
            return Response({'error': 'Contact not found'}, status=status.HTTP_404_NOT_FOUND)

        history = ScoreHistory.objects.filter(contact=contact)[:100]
        serializer = ScoreHistorySerializer(history, many=True)
        return Response(serializer.data)
