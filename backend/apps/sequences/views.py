from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models, transaction
from django.shortcuts import get_object_or_404

from apps.sequences.models import (
    Sequence, SequenceStep, SequenceEnrollment,
    SequenceStepExecution, SequenceEvent
)
from apps.sequences.serializers import (
    SequenceSerializer, SequenceCreateSerializer, SequenceUpdateSerializer,
    SequenceListSerializer, SequenceStepSerializer, SequenceStepCreateSerializer,
    SequenceEnrollmentSerializer, SequenceEnrollmentListSerializer,
    SequenceStepExecutionSerializer, SequenceEventSerializer,
    EnrollContactSerializer, BulkEnrollSerializer,
    SequenceStatsSerializer, StepStatsSerializer
)
from apps.sequences.services.sequence_engine import SequenceEngine
from apps.contacts.models import Contact
from apps.workspaces.models import Workspace


class SequenceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Sequences."""

    permission_classes = [IsAuthenticated]
    serializer_class = SequenceSerializer

    def get_queryset(self):
        # Get the workspace (for now, use the first one or from query param)
        workspace_id = self.request.query_params.get('workspace')
        if workspace_id:
            return Sequence.objects.filter(workspace_id=workspace_id)

        # Get user's workspaces
        workspaces = Workspace.objects.filter(
            members__user=self.request.user
        )
        return Sequence.objects.filter(workspace__in=workspaces)

    def get_serializer_class(self):
        if self.action == 'create':
            return SequenceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SequenceUpdateSerializer
        elif self.action == 'list':
            return SequenceListSerializer
        return SequenceSerializer

    def perform_create(self, serializer):
        # Get workspace
        workspace_id = self.request.data.get('workspace')
        if workspace_id:
            workspace = get_object_or_404(Workspace, id=workspace_id)
        else:
            # Use first workspace
            workspace = Workspace.objects.filter(
                members__user=self.request.user
            ).first()

        serializer.save(workspace=workspace, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a sequence (make it ready to process enrollments)."""
        sequence = self.get_object()

        if sequence.status == Sequence.Status.ACTIVE:
            return Response(
                {'error': 'Sequence is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not sequence.email_account:
            return Response(
                {'error': 'No email account configured'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if sequence.steps.count() == 0:
            return Response(
                {'error': 'Sequence has no steps'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sequence.status = Sequence.Status.ACTIVE
        sequence.save(update_fields=['status'])

        return Response(SequenceSerializer(sequence).data)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a sequence and all its active enrollments."""
        sequence = self.get_object()
        engine = SequenceEngine(sequence)

        success, message = engine.pause_sequence()

        if success:
            return Response(SequenceSerializer(sequence).data)
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused sequence."""
        sequence = self.get_object()
        engine = SequenceEngine(sequence)

        success, message = engine.resume_sequence()

        if success:
            return Response(SequenceSerializer(sequence).data)
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a sequence."""
        sequence = self.get_object()

        # Stop all active enrollments first
        if sequence.status == Sequence.Status.ACTIVE:
            engine = SequenceEngine(sequence)
            engine.pause_sequence()

        sequence.status = Sequence.Status.ARCHIVED
        sequence.save(update_fields=['status'])

        return Response(SequenceSerializer(sequence).data)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a sequence."""
        sequence = self.get_object()

        with transaction.atomic():
            # Create new sequence
            new_sequence = Sequence.objects.create(
                workspace=sequence.workspace,
                name=f"{sequence.name} (Copy)",
                description=sequence.description,
                email_account=sequence.email_account,
                from_name=sequence.from_name,
                reply_to=sequence.reply_to,
                track_opens=sequence.track_opens,
                track_clicks=sequence.track_clicks,
                include_unsubscribe_link=sequence.include_unsubscribe_link,
                send_window_enabled=sequence.send_window_enabled,
                send_window_start=sequence.send_window_start,
                send_window_end=sequence.send_window_end,
                send_window_days=sequence.send_window_days,
                send_window_timezone=sequence.send_window_timezone,
                max_emails_per_day=sequence.max_emails_per_day,
                min_delay_between_emails=sequence.min_delay_between_emails,
                stop_on_reply=sequence.stop_on_reply,
                stop_on_click=sequence.stop_on_click,
                stop_on_open=sequence.stop_on_open,
                stop_on_unsubscribe=sequence.stop_on_unsubscribe,
                stop_on_bounce=sequence.stop_on_bounce,
                stop_on_score_above=sequence.stop_on_score_above,
                stop_on_score_below=sequence.stop_on_score_below,
                status=Sequence.Status.DRAFT,
                created_by=request.user,
            )

            # Duplicate steps
            for step in sequence.steps.all():
                SequenceStep.objects.create(
                    sequence=new_sequence,
                    order=step.order,
                    step_type=step.step_type,
                    name=step.name,
                    subject=step.subject,
                    content_html=step.content_html,
                    content_text=step.content_text,
                    template=step.template,
                    delay_value=step.delay_value,
                    delay_unit=step.delay_unit,
                    condition_type=step.condition_type,
                    condition_value=step.condition_value,
                    tag_action=step.tag_action,
                    tag=step.tag,
                    webhook_url=step.webhook_url,
                    webhook_method=step.webhook_method,
                    webhook_headers=step.webhook_headers,
                    webhook_payload=step.webhook_payload,
                    task_title=step.task_title,
                    task_description=step.task_description,
                    task_assignee=step.task_assignee,
                    is_active=step.is_active,
                )

        return Response(
            SequenceSerializer(new_sequence).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """Enroll a single contact in the sequence."""
        sequence = self.get_object()
        serializer = EnrollContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_id = serializer.validated_data['contact_id']
        source = serializer.validated_data.get('source', 'manual')

        contact = get_object_or_404(Contact, id=contact_id)
        engine = SequenceEngine(sequence)

        result = engine.enroll_contact(
            contact,
            enrolled_by=request.user,
            source=source
        )

        if result.success:
            return Response({
                'success': True,
                'message': result.message,
                'enrollment_id': result.enrollment_id
            })
        else:
            return Response(
                {'error': result.message},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def bulk_enroll(self, request, pk=None):
        """Enroll multiple contacts in the sequence."""
        sequence = self.get_object()
        serializer = BulkEnrollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_ids = serializer.validated_data['contact_ids']
        source = serializer.validated_data.get('source', 'bulk')

        contacts = Contact.objects.filter(id__in=contact_ids)
        engine = SequenceEngine(sequence)

        success_count, failed_count, errors = engine.bulk_enroll(
            list(contacts),
            enrolled_by=request.user,
            source=source
        )

        return Response({
            'success': True,
            'enrolled': success_count,
            'failed': failed_count,
            'errors': errors[:20]  # Limit errors in response
        })

    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        """Get enrollments for a sequence."""
        sequence = self.get_object()
        status_filter = request.query_params.get('status')

        queryset = sequence.enrollments.all()
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        queryset = queryset.select_related('contact', 'current_step')

        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        offset = (page - 1) * page_size

        total = queryset.count()
        enrollments = queryset[offset:offset + page_size]

        return Response({
            'results': SequenceEnrollmentListSerializer(enrollments, many=True).data,
            'total': total,
            'page': page,
            'page_size': page_size,
        })

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get detailed statistics for a sequence."""
        sequence = self.get_object()
        engine = SequenceEngine(sequence)

        stats = engine.get_stats()

        # Get step-level stats
        step_stats = []
        for step in sequence.steps.all():
            step_stats.append({
                'order': step.order,
                'type': step.step_type,
                'name': step.name or f"Step {step.order + 1}",
                'sent': step.sent_count,
                'opened': step.opened_count,
                'clicked': step.clicked_count,
                'replied': step.replied_count,
                'bounced': step.bounced_count,
                'open_rate': step.open_rate,
                'click_rate': step.click_rate,
            })

        return Response({
            'stats': stats,
            'step_stats': step_stats
        })

    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get recent events for a sequence."""
        sequence = self.get_object()

        queryset = SequenceEvent.objects.filter(
            enrollment__sequence=sequence
        ).select_related(
            'enrollment__contact', 'step'
        ).order_by('-created_at')

        # Filter by event type
        event_type = request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Pagination
        limit = int(request.query_params.get('limit', 50))
        events = queryset[:limit]

        return Response(SequenceEventSerializer(events, many=True).data)


class SequenceStepViewSet(viewsets.ModelViewSet):
    """ViewSet for managing SequenceSteps."""

    permission_classes = [IsAuthenticated]
    serializer_class = SequenceStepSerializer

    def get_queryset(self):
        sequence_id = self.request.query_params.get('sequence')
        if sequence_id:
            return SequenceStep.objects.filter(
                sequence_id=sequence_id
            ).order_by('order')
        return SequenceStep.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SequenceStepCreateSerializer
        return SequenceStepSerializer

    def perform_create(self, serializer):
        sequence_id = self.request.data.get('sequence')
        sequence = get_object_or_404(Sequence, id=sequence_id)

        # Get next order number if not specified
        order = self.request.data.get('order')
        if order is None:
            max_order = sequence.steps.aggregate(
                max_order=models.Max('order')
            )['max_order']
            order = (max_order or -1) + 1

        serializer.save(sequence=sequence, order=order)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle step active state."""
        step = self.get_object()
        step.is_active = not step.is_active
        step.save(update_fields=['is_active'])

        return Response(SequenceStepSerializer(step).data)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Reorder steps within a sequence."""
        step_ids = request.data.get('step_ids', [])
        sequence_id = request.data.get('sequence')

        if not step_ids:
            return Response(
                {'error': 'step_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not sequence_id:
            return Response(
                {'error': 'sequence is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sequence = get_object_or_404(Sequence, id=sequence_id)

        with transaction.atomic():
            for i, step_id in enumerate(step_ids):
                SequenceStep.objects.filter(
                    id=step_id, sequence=sequence
                ).update(order=i)

        steps = sequence.steps.all().order_by('order')
        return Response(SequenceStepSerializer(steps, many=True).data)


class SequenceEnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing SequenceEnrollments."""

    permission_classes = [IsAuthenticated]
    serializer_class = SequenceEnrollmentSerializer
    http_method_names = ['get', 'delete']  # No create/update through API

    def get_queryset(self):
        sequence_id = self.request.query_params.get('sequence')
        contact_id = self.request.query_params.get('contact')
        status_filter = self.request.query_params.get('status')

        queryset = SequenceEnrollment.objects.all()

        if sequence_id:
            queryset = queryset.filter(sequence_id=sequence_id)
        if contact_id:
            queryset = queryset.filter(contact_id=contact_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.select_related(
            'sequence', 'contact', 'current_step'
        ).order_by('-enrolled_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return SequenceEnrollmentListSerializer
        return SequenceEnrollmentSerializer

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause an enrollment."""
        enrollment = self.get_object()
        enrollment.pause()

        SequenceEvent.objects.create(
            enrollment=enrollment,
            event_type=SequenceEvent.EventType.PAUSED,
            message="Enrollment paused manually"
        )

        return Response(SequenceEnrollmentSerializer(enrollment).data)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused enrollment."""
        enrollment = self.get_object()
        enrollment.resume()

        SequenceEvent.objects.create(
            enrollment=enrollment,
            event_type=SequenceEvent.EventType.RESUMED,
            message="Enrollment resumed manually"
        )

        return Response(SequenceEnrollmentSerializer(enrollment).data)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop an enrollment."""
        enrollment = self.get_object()
        reason = request.data.get('reason', SequenceEnrollment.StopReason.MANUAL)
        details = request.data.get('details', 'Stopped manually')

        enrollment.stop(reason, details)

        # Update sequence stats
        engine = SequenceEngine(enrollment.sequence)
        engine._update_sequence_stats_on_stop(enrollment)

        return Response(SequenceEnrollmentSerializer(enrollment).data)

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """Get step executions for an enrollment."""
        enrollment = self.get_object()
        executions = enrollment.step_executions.all().select_related('step')

        return Response(
            SequenceStepExecutionSerializer(executions, many=True).data
        )

    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get events for an enrollment."""
        enrollment = self.get_object()

        limit = int(request.query_params.get('limit', 50))
        events = enrollment.events.all()[:limit]

        return Response(SequenceEventSerializer(events, many=True).data)
