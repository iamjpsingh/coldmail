import base64
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.tracking.models import (
    TrackingDomain,
    TrackingEvent,
    UnsubscribeToken,
    BounceRecord,
    ComplaintRecord,
    SuppressionList,
    WebsiteTrackingScript,
    WebsiteVisitor,
    VisitorSession,
    PageView,
    WebsiteEvent,
)
from apps.tracking.serializers import (
    TrackingDomainSerializer,
    TrackingDomainCreateSerializer,
    TrackingEventSerializer,
    TrackingEventListSerializer,
    UnsubscribeTokenSerializer,
    BounceRecordSerializer,
    ComplaintRecordSerializer,
    SuppressionListSerializer,
    SuppressionListCreateSerializer,
    TrackingStatsSerializer,
    WebsiteTrackingScriptSerializer,
    WebsiteTrackingScriptUpdateSerializer,
    WebsiteVisitorSerializer,
    WebsiteVisitorListSerializer,
    WebsiteVisitorDetailSerializer,
    VisitorSessionSerializer,
    PageViewSerializer,
    WebsiteEventSerializer,
    WebsiteTrackingStatsSerializer,
)
from apps.tracking.services import TrackingService, WebsiteTrackingService

logger = logging.getLogger(__name__)

# 1x1 transparent GIF
TRANSPARENT_GIF = base64.b64decode(
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
)


# ==================== Public Tracking Endpoints ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def track_open(request, token):
    """Track email open via pixel.

    GET /t/o/<token>.gif
    """
    # Get request info
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Record the open
    service = TrackingService()
    service.record_open(
        pixel_token=token,
        ip_address=ip_address,
        user_agent=user_agent
    )

    # Return transparent 1x1 GIF
    response = HttpResponse(TRANSPARENT_GIF, content_type='image/gif')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def track_click(request, token):
    """Track link click and redirect.

    GET /t/c/<token>
    """
    # Get request info
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Record the click
    service = TrackingService()
    result = service.record_click(
        link_token=token,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if result:
        event, original_url = result
        return HttpResponseRedirect(original_url)

    # If invalid token, redirect to a default page or return 404
    return HttpResponse('Link not found', status=404)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def unsubscribe(request, token):
    """Handle unsubscribe requests.

    GET /t/u/<token> - Show unsubscribe confirmation page
    POST /t/u/<token> - Process unsubscribe
    """
    # Get request info
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    service = TrackingService()

    # Check if token is valid
    try:
        unsub_token = UnsubscribeToken.objects.select_related('contact').get(token=token)
    except UnsubscribeToken.DoesNotExist:
        return HttpResponse('Invalid unsubscribe link', status=404)

    if request.method == 'GET':
        # Show confirmation page
        context = {
            'email': unsub_token.contact.email,
            'token': token,
            'already_unsubscribed': unsub_token.is_used,
        }
        return render(request, 'tracking/unsubscribe.html', context)

    elif request.method == 'POST':
        # Process unsubscribe
        reason = request.POST.get('reason', request.data.get('reason', ''))

        result = service.process_unsubscribe(
            token=token,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if result:
            context = {
                'email': result.contact.email,
                'success': True,
            }
            return render(request, 'tracking/unsubscribe_success.html', context)

        return HttpResponse('Error processing unsubscribe', status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def one_click_unsubscribe(request, token):
    """Handle RFC 8058 one-click unsubscribe.

    POST /t/u/<token>/one-click
    """
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    service = TrackingService()
    result = service.process_unsubscribe(
        token=token,
        reason='One-click unsubscribe',
        ip_address=ip_address,
        user_agent=user_agent
    )

    if result:
        return HttpResponse(status=200)

    return HttpResponse('Invalid token', status=404)


# ==================== Website Tracking Public Endpoints ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def website_track(request):
    """Track website events (page views, clicks, etc.).

    POST /t/w/track

    This endpoint is called by the JavaScript tracking snippet.
    """
    data = request.data
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    script_id = data.get('script_id')
    visitor_id = data.get('visitor_id')
    session_id = data.get('session_id')
    event_type = data.get('event_type')

    if not all([script_id, visitor_id, session_id, event_type]):
        return Response(
            {'error': 'Missing required fields'},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = WebsiteTrackingService()

    try:
        if event_type == 'page_view':
            # Record page view
            service.record_page_view(
                script_id=script_id,
                visitor_id=visitor_id,
                session_id=session_id,
                page_url=data.get('page_url', ''),
                page_path=data.get('page_path', ''),
                page_title=data.get('page_title', ''),
                referrer=data.get('referrer', ''),
                utm_params=data.get('utm', {}),
                screen_resolution=data.get('screen_resolution', ''),
                ip_address=ip_address,
                user_agent=user_agent,
                ident_token=data.get('ident_token'),
            )

        elif event_type == 'session_start':
            # Session start is recorded as part of page view
            pass

        elif event_type == 'identify':
            # Identify visitor by email
            email = data.get('email')
            if email:
                service.identify_visitor(
                    script_id=script_id,
                    visitor_id=visitor_id,
                    email=email,
                    properties=data.get('properties', {}),
                    method='form_submit',
                )

        elif event_type == 'page_exit':
            # Update page metrics and possibly end session
            service.update_page_metrics(
                visitor_id=visitor_id,
                session_id=session_id,
                page_path=data.get('page_path', ''),
                time_on_page=data.get('time_on_page', 0),
                scroll_depth=data.get('max_scroll', 0),
            )

        else:
            # Record other events (click, form_submit, scroll, etc.)
            service.record_event(
                script_id=script_id,
                visitor_id=visitor_id,
                session_id=session_id,
                event_type=event_type,
                page_url=data.get('page_url', ''),
                page_path=data.get('page_path', ''),
                event_name=data.get('event_name', ''),
                properties=data.get('properties', {}),
                element_id=data.get('element_id', ''),
                element_class=data.get('element_class', ''),
                element_text=data.get('element_text', ''),
                target_url=data.get('target_url', ''),
                ip_address=ip_address,
                user_agent=user_agent,
            )

        # Return empty response with 204 No Content
        return Response(status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        logger.error(f"Error tracking website event: {e}")
        return Response(
            {'error': 'Internal error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def website_script(request, script_id):
    """Serve the tracking JavaScript for a workspace.

    GET /t/w/script/<script_id>.js

    This endpoint serves the tracking script that websites embed.
    """
    try:
        script = WebsiteTrackingScript.objects.select_related('workspace').get(
            script_id=script_id,
            is_enabled=True
        )
    except WebsiteTrackingScript.DoesNotExist:
        return HttpResponse(
            '// Invalid or disabled tracking script',
            content_type='application/javascript',
            status=404
        )

    service = WebsiteTrackingService()
    js_content = service.generate_tracking_snippet(script)

    # Extract just the JavaScript (without HTML comment wrapper)
    import re
    match = re.search(r'<script>(.*?)</script>', js_content, re.DOTALL)
    if match:
        js_content = match.group(1)

    response = HttpResponse(js_content, content_type='application/javascript')
    response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
    return response


# ==================== API Endpoints (Authenticated) ====================

class TrackingDomainViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tracking domains."""

    serializer_class = TrackingDomainSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TrackingDomain.objects.filter(
            workspace_id=self.request.headers.get('X-Workspace-ID')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return TrackingDomainCreateSerializer
        return TrackingDomainSerializer

    def perform_create(self, serializer):
        workspace_id = self.request.headers.get('X-Workspace-ID')

        # If setting as default, unset other defaults
        if serializer.validated_data.get('is_default'):
            TrackingDomain.objects.filter(
                workspace_id=workspace_id,
                is_default=True
            ).update(is_default=False)

        serializer.save(workspace_id=workspace_id)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a tracking domain.

        POST /api/tracking/domains/{id}/verify/
        """
        domain = self.get_object()

        # In production, you would verify DNS records here
        # For now, just mark as verified
        domain.is_verified = True
        domain.verified_at = timezone.now()
        domain.save(update_fields=['is_verified', 'verified_at', 'updated_at'])

        return Response(TrackingDomainSerializer(domain).data)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set a tracking domain as default.

        POST /api/tracking/domains/{id}/set_default/
        """
        domain = self.get_object()
        workspace_id = request.headers.get('X-Workspace-ID')

        # Unset other defaults
        TrackingDomain.objects.filter(
            workspace_id=workspace_id,
            is_default=True
        ).update(is_default=False)

        domain.is_default = True
        domain.save(update_fields=['is_default', 'updated_at'])

        return Response(TrackingDomainSerializer(domain).data)

    @action(detail=True, methods=['get'])
    def dns_records(self, request, pk=None):
        """Get DNS records required for verification.

        GET /api/tracking/domains/{id}/dns_records/
        """
        domain = self.get_object()

        records = [
            {
                'type': 'CNAME',
                'name': domain.domain,
                'value': 'track.yourservice.com',
                'purpose': 'Point tracking domain to service'
            },
            {
                'type': 'TXT',
                'name': f'_coldmail.{domain.domain}',
                'value': f'coldmail-verify={domain.verification_token}',
                'purpose': 'Domain verification'
            }
        ]

        return Response({'records': records})


class TrackingEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing tracking events."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_id = self.request.headers.get('X-Workspace-ID')
        queryset = TrackingEvent.objects.filter(
            campaign_recipient__campaign__workspace_id=workspace_id
        ).select_related(
            'campaign_recipient__campaign',
            'campaign_recipient__contact',
            'tracking_link'
        ).order_by('-created_at')

        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_recipient__campaign_id=campaign_id)

        # Filter by contact
        contact_id = self.request.query_params.get('contact_id')
        if contact_id:
            queryset = queryset.filter(campaign_recipient__contact_id=contact_id)

        # Filter out bots
        exclude_bots = self.request.query_params.get('exclude_bots', 'false').lower() == 'true'
        if exclude_bots:
            queryset = queryset.filter(is_bot=False)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return TrackingEventListSerializer
        return TrackingEventSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get tracking statistics.

        GET /api/tracking/events/stats/
        """
        workspace_id = request.headers.get('X-Workspace-ID')

        # Get campaign filter
        campaign_id = request.query_params.get('campaign_id')

        base_filter = Q(campaign_recipient__campaign__workspace_id=workspace_id)
        if campaign_id:
            base_filter &= Q(campaign_recipient__campaign_id=campaign_id)

        events = TrackingEvent.objects.filter(base_filter)

        # Calculate stats
        stats = {
            'total_opens': events.filter(event_type='open').count(),
            'unique_opens': events.filter(event_type='open', is_bot=False).values(
                'campaign_recipient'
            ).distinct().count(),
            'total_clicks': events.filter(event_type='click').count(),
            'unique_clicks': events.filter(event_type='click', is_bot=False).values(
                'campaign_recipient'
            ).distinct().count(),
            'total_unsubscribes': events.filter(event_type='unsubscribe').count(),
            'total_bounces': events.filter(event_type='bounce').count(),
            'hard_bounces': events.filter(event_type='bounce', bounce_type='hard').count(),
            'soft_bounces': events.filter(event_type='bounce', bounce_type='soft').count(),
            'total_complaints': events.filter(event_type='complaint').count(),
            'suppressed_count': SuppressionList.objects.filter(
                workspace_id=workspace_id
            ).count(),
            'bot_opens': events.filter(event_type='open', is_bot=True).count(),
            'bot_clicks': events.filter(event_type='click', is_bot=True).count(),
        }

        return Response(TrackingStatsSerializer(stats).data)

    @action(detail=False, methods=['get'])
    def device_breakdown(self, request):
        """Get device type breakdown.

        GET /api/tracking/events/device_breakdown/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        campaign_id = request.query_params.get('campaign_id')

        base_filter = Q(
            campaign_recipient__campaign__workspace_id=workspace_id,
            is_bot=False
        )
        if campaign_id:
            base_filter &= Q(campaign_recipient__campaign_id=campaign_id)

        events = TrackingEvent.objects.filter(base_filter)
        total = events.count()

        if total == 0:
            return Response([])

        breakdown = events.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')

        result = []
        for item in breakdown:
            if item['device_type']:
                result.append({
                    'device_type': item['device_type'],
                    'count': item['count'],
                    'percentage': round(item['count'] / total * 100, 1)
                })

        return Response(result)

    @action(detail=False, methods=['get'])
    def location_breakdown(self, request):
        """Get location breakdown.

        GET /api/tracking/events/location_breakdown/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        campaign_id = request.query_params.get('campaign_id')

        base_filter = Q(
            campaign_recipient__campaign__workspace_id=workspace_id,
            is_bot=False
        )
        if campaign_id:
            base_filter &= Q(campaign_recipient__campaign_id=campaign_id)

        events = TrackingEvent.objects.filter(base_filter).exclude(country='')
        total = events.count()

        if total == 0:
            return Response([])

        breakdown = events.values('country', 'country_code').annotate(
            count=Count('id')
        ).order_by('-count')[:20]  # Top 20 countries

        result = []
        for item in breakdown:
            result.append({
                'country': item['country'],
                'country_code': item['country_code'],
                'count': item['count'],
                'percentage': round(item['count'] / total * 100, 1)
            })

        return Response(result)

    @action(detail=False, methods=['get'])
    def browser_breakdown(self, request):
        """Get browser breakdown.

        GET /api/tracking/events/browser_breakdown/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        campaign_id = request.query_params.get('campaign_id')

        base_filter = Q(
            campaign_recipient__campaign__workspace_id=workspace_id,
            is_bot=False
        )
        if campaign_id:
            base_filter &= Q(campaign_recipient__campaign_id=campaign_id)

        events = TrackingEvent.objects.filter(base_filter).exclude(browser_name='')
        total = events.count()

        if total == 0:
            return Response([])

        breakdown = events.values('browser_name').annotate(
            count=Count('id')
        ).order_by('-count')

        result = []
        for item in breakdown:
            result.append({
                'browser_name': item['browser_name'],
                'count': item['count'],
                'percentage': round(item['count'] / total * 100, 1)
            })

        return Response(result)


class BounceRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing bounce records."""

    serializer_class = BounceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_id = self.request.headers.get('X-Workspace-ID')
        queryset = BounceRecord.objects.filter(
            workspace_id=workspace_id
        ).select_related('campaign', 'email_account').order_by('-created_at')

        # Filter by bounce type
        bounce_type = self.request.query_params.get('bounce_type')
        if bounce_type:
            queryset = queryset.filter(bounce_type=bounce_type)

        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get bounce statistics.

        GET /api/tracking/bounces/stats/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        bounces = BounceRecord.objects.filter(workspace_id=workspace_id)

        stats = {
            'total': bounces.count(),
            'hard': bounces.filter(bounce_type='hard').count(),
            'soft': bounces.filter(bounce_type='soft').count(),
            'by_category': list(
                bounces.values('bounce_category').annotate(
                    count=Count('id')
                ).order_by('-count')
            )
        }

        return Response(stats)


class ComplaintRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing complaint records."""

    serializer_class = ComplaintRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_id = self.request.headers.get('X-Workspace-ID')
        return ComplaintRecord.objects.filter(
            workspace_id=workspace_id
        ).select_related('campaign', 'email_account').order_by('-created_at')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get complaint statistics.

        GET /api/tracking/complaints/stats/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        complaints = ComplaintRecord.objects.filter(workspace_id=workspace_id)

        stats = {
            'total': complaints.count(),
            'by_type': list(
                complaints.values('complaint_type').annotate(
                    count=Count('id')
                ).order_by('-count')
            )
        }

        return Response(stats)


class SuppressionListViewSet(viewsets.ModelViewSet):
    """ViewSet for managing suppression list."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_id = self.request.headers.get('X-Workspace-ID')
        queryset = SuppressionList.objects.filter(
            workspace_id=workspace_id
        ).order_by('-created_at')

        # Filter by reason
        reason = self.request.query_params.get('reason')
        if reason:
            queryset = queryset.filter(reason=reason)

        # Search by email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(email__icontains=search)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return SuppressionListCreateSerializer
        return SuppressionListSerializer

    def perform_create(self, serializer):
        workspace_id = self.request.headers.get('X-Workspace-ID')
        serializer.save(workspace_id=workspace_id)

    @action(detail=False, methods=['post'])
    def bulk_add(self, request):
        """Bulk add emails to suppression list.

        POST /api/tracking/suppression/bulk_add/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        emails = request.data.get('emails', [])
        reason = request.data.get('reason', 'manual')
        source = request.data.get('source', 'Bulk import')

        if not emails:
            return Response(
                {'error': 'No emails provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.workspaces.models import Workspace
        workspace = Workspace.objects.get(id=workspace_id)

        service = TrackingService()
        added = 0
        for email in emails:
            if email:
                service.add_to_suppression_list(
                    workspace=workspace,
                    email=email.lower().strip(),
                    reason=reason,
                    source=source
                )
                added += 1

        return Response({'added': added})

    @action(detail=False, methods=['post'])
    def check(self, request):
        """Check if an email is suppressed.

        POST /api/tracking/suppression/check/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        email = request.data.get('email', '')

        if not email:
            return Response(
                {'error': 'Email required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_suppressed = SuppressionList.objects.filter(
            workspace_id=workspace_id,
            email__iexact=email
        ).exists()

        return Response({'email': email, 'is_suppressed': is_suppressed})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get suppression list statistics.

        GET /api/tracking/suppression/stats/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        suppressed = SuppressionList.objects.filter(workspace_id=workspace_id)

        stats = {
            'total': suppressed.count(),
            'by_reason': list(
                suppressed.values('reason').annotate(
                    count=Count('id')
                ).order_by('-count')
            )
        }

        return Response(stats)


# ==================== Webhook Handlers ====================

@api_view(['POST'])
@permission_classes([AllowAny])  # Webhooks need custom auth
def handle_bounce_webhook(request):
    """Handle bounce webhooks from email providers.

    POST /api/tracking/webhooks/bounce/
    """
    # Verify webhook signature (provider-specific)
    # This is a generic endpoint - actual implementation
    # depends on the email provider (SES, SendGrid, etc.)

    data = request.data
    webhook_type = data.get('type', '')

    if webhook_type in ('bounce', 'Bounce'):
        service = TrackingService()

        # Extract bounce info (format varies by provider)
        email = data.get('email') or data.get('recipient')
        bounce_type = data.get('bounce_type', 'hard')
        workspace_id = data.get('workspace_id')
        campaign_id = data.get('campaign_id')
        message_id = data.get('message_id', '')

        if email and workspace_id:
            service.process_bounce(
                email=email,
                workspace_id=workspace_id,
                bounce_type=bounce_type,
                campaign_id=campaign_id,
                message_id=message_id,
                raw_data=data
            )
            return Response({'status': 'processed'})

    return Response({'status': 'ignored'})


@api_view(['POST'])
@permission_classes([AllowAny])  # Webhooks need custom auth
def handle_complaint_webhook(request):
    """Handle complaint webhooks from email providers.

    POST /api/tracking/webhooks/complaint/
    """
    data = request.data
    webhook_type = data.get('type', '')

    if webhook_type in ('complaint', 'Complaint', 'spam'):
        service = TrackingService()

        email = data.get('email') or data.get('recipient')
        workspace_id = data.get('workspace_id')
        campaign_id = data.get('campaign_id')
        feedback_id = data.get('feedback_id', '')
        message_id = data.get('message_id', '')

        if email and workspace_id:
            service.process_complaint(
                email=email,
                workspace_id=workspace_id,
                campaign_id=campaign_id,
                feedback_id=feedback_id,
                message_id=message_id,
                raw_data=data
            )
            return Response({'status': 'processed'})

    return Response({'status': 'ignored'})


# ==================== Website Tracking API ViewSets ====================

class WebsiteTrackingScriptViewSet(viewsets.ModelViewSet):
    """ViewSet for managing website tracking script configuration."""

    serializer_class = WebsiteTrackingScriptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_id = self.request.headers.get('X-Workspace-ID')
        return WebsiteTrackingScript.objects.filter(workspace_id=workspace_id)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return WebsiteTrackingScriptUpdateSerializer
        return WebsiteTrackingScriptSerializer

    def list(self, request):
        """Get or create the tracking script for the workspace.

        GET /api/tracking/website/script/
        """
        workspace_id = request.headers.get('X-Workspace-ID')

        # Auto-create script if it doesn't exist
        service = WebsiteTrackingService()
        from apps.workspaces.models import Workspace
        workspace = Workspace.objects.get(id=workspace_id)
        script = service.get_or_create_tracking_script(workspace)

        return Response(WebsiteTrackingScriptSerializer(script).data)

    @action(detail=True, methods=['get'])
    def snippet(self, request, pk=None):
        """Get the full JavaScript snippet.

        GET /api/tracking/website/script/{id}/snippet/
        """
        script = self.get_object()
        service = WebsiteTrackingService()
        snippet = service.generate_tracking_snippet(script)
        return Response({'snippet': snippet})

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate the script ID (invalidates old scripts).

        POST /api/tracking/website/script/{id}/regenerate/
        """
        import secrets
        script = self.get_object()
        script.script_id = secrets.token_urlsafe(24)
        script.save(update_fields=['script_id', 'updated_at'])
        return Response(WebsiteTrackingScriptSerializer(script).data)


class WebsiteVisitorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing website visitors."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_id = self.request.headers.get('X-Workspace-ID')
        queryset = WebsiteVisitor.objects.filter(
            workspace_id=workspace_id
        ).select_related('contact').order_by('-last_seen_at')

        # Filter by identification status
        is_identified = self.request.query_params.get('is_identified')
        if is_identified is not None:
            is_identified = is_identified.lower() == 'true'
            queryset = queryset.filter(is_identified=is_identified)

        # Filter by contact
        contact_id = self.request.query_params.get('contact_id')
        if contact_id:
            queryset = queryset.filter(contact_id=contact_id)

        # Search by company or email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(contact__email__icontains=search) |
                Q(contact__first_name__icontains=search) |
                Q(contact__last_name__icontains=search)
            )

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(last_seen_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(last_seen_at__lte=end_date)

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WebsiteVisitorDetailSerializer
        return WebsiteVisitorListSerializer

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get all sessions for a visitor.

        GET /api/tracking/website/visitors/{id}/sessions/
        """
        visitor = self.get_object()
        sessions = visitor.sessions.order_by('-started_at')
        page = self.paginate_queryset(sessions)
        if page is not None:
            serializer = VisitorSessionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(VisitorSessionSerializer(sessions, many=True).data)

    @action(detail=True, methods=['get'])
    def page_views(self, request, pk=None):
        """Get all page views for a visitor.

        GET /api/tracking/website/visitors/{id}/page_views/
        """
        visitor = self.get_object()
        page_views = visitor.page_views.order_by('-created_at')
        page = self.paginate_queryset(page_views)
        if page is not None:
            serializer = PageViewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(PageViewSerializer(page_views, many=True).data)

    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get all events for a visitor.

        GET /api/tracking/website/visitors/{id}/events/
        """
        visitor = self.get_object()
        events = visitor.events.order_by('-created_at')

        # Filter by event type
        event_type = request.query_params.get('event_type')
        if event_type:
            events = events.filter(event_type=event_type)

        page = self.paginate_queryset(events)
        if page is not None:
            serializer = WebsiteEventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(WebsiteEventSerializer(events, many=True).data)

    @action(detail=True, methods=['post'])
    def identify(self, request, pk=None):
        """Manually identify a visitor.

        POST /api/tracking/website/visitors/{id}/identify/
        """
        visitor = self.get_object()
        contact_id = request.data.get('contact_id')

        if not contact_id:
            return Response(
                {'error': 'contact_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.contacts.models import Contact
        try:
            contact = Contact.objects.get(
                id=contact_id,
                workspace_id=visitor.workspace_id
            )
        except Contact.DoesNotExist:
            return Response(
                {'error': 'Contact not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        visitor.contact = contact
        visitor.is_identified = True
        visitor.identified_at = timezone.now()
        visitor.identification_method = 'manual'
        visitor.save()

        from apps.tracking.models import VisitorIdentification
        VisitorIdentification.objects.create(
            visitor=visitor,
            contact=contact,
            method=VisitorIdentification.Method.MANUAL,
            email=contact.email,
            source='Manual identification',
        )

        return Response(WebsiteVisitorDetailSerializer(visitor).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get website visitor statistics.

        GET /api/tracking/website/visitors/stats/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        from django.db.models import Avg, Sum
        from datetime import timedelta

        visitors = WebsiteVisitor.objects.filter(workspace_id=workspace_id)
        sessions = VisitorSession.objects.filter(visitor__workspace_id=workspace_id)

        today = timezone.now().date()
        today_start = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )

        # Calculate stats
        total_visitors = visitors.count()
        identified_visitors = visitors.filter(is_identified=True).count()
        total_sessions = sessions.count()
        total_page_views = PageView.objects.filter(
            visitor__workspace_id=workspace_id
        ).count()

        # Average session duration
        avg_duration = sessions.aggregate(avg=Avg('duration_seconds'))['avg'] or 0

        # Average pages per session
        avg_pages = sessions.aggregate(avg=Avg('page_views'))['avg'] or 0

        # Bounce rate (sessions with only 1 page view)
        single_page_sessions = sessions.filter(page_views=1).count()
        bounce_rate = (single_page_sessions / total_sessions * 100) if total_sessions > 0 else 0

        # New visitors today
        new_visitors_today = visitors.filter(first_seen_at__gte=today_start).count()

        # Returning visitors today
        returning_visitors_today = visitors.filter(
            last_seen_at__gte=today_start,
            first_seen_at__lt=today_start
        ).count()

        stats = {
            'total_visitors': total_visitors,
            'identified_visitors': identified_visitors,
            'anonymous_visitors': total_visitors - identified_visitors,
            'total_sessions': total_sessions,
            'total_page_views': total_page_views,
            'average_session_duration': round(avg_duration, 2),
            'average_pages_per_session': round(avg_pages, 2),
            'bounce_rate': round(bounce_rate, 2),
            'new_visitors_today': new_visitors_today,
            'returning_visitors_today': returning_visitors_today,
        }

        return Response(WebsiteTrackingStatsSerializer(stats).data)

    @action(detail=False, methods=['get'])
    def top_pages(self, request):
        """Get top visited pages.

        GET /api/tracking/website/visitors/top_pages/
        """
        workspace_id = request.headers.get('X-Workspace-ID')

        page_views = PageView.objects.filter(
            visitor__workspace_id=workspace_id
        ).values('page_path', 'page_title').annotate(
            views=Count('id')
        ).order_by('-views')[:20]

        return Response(list(page_views))

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently active visitors.

        GET /api/tracking/website/visitors/recent/
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        limit = int(request.query_params.get('limit', 10))

        visitors = WebsiteVisitor.objects.filter(
            workspace_id=workspace_id
        ).select_related('contact').order_by('-last_seen_at')[:limit]

        return Response(WebsiteVisitorListSerializer(visitors, many=True).data)


class VisitorSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing visitor sessions."""

    serializer_class = VisitorSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_id = self.request.headers.get('X-Workspace-ID')
        queryset = VisitorSession.objects.filter(
            visitor__workspace_id=workspace_id
        ).select_related('visitor').order_by('-started_at')

        # Filter by visitor
        visitor_id = self.request.query_params.get('visitor_id')
        if visitor_id:
            queryset = queryset.filter(visitor_id=visitor_id)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)

        return queryset

    @action(detail=True, methods=['get'])
    def page_views(self, request, pk=None):
        """Get all page views for a session.

        GET /api/tracking/website/sessions/{id}/page_views/
        """
        session = self.get_object()
        page_views = session.page_view_events.order_by('created_at')
        return Response(PageViewSerializer(page_views, many=True).data)

    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get all events for a session.

        GET /api/tracking/website/sessions/{id}/events/
        """
        session = self.get_object()
        events = session.events.order_by('created_at')
        return Response(WebsiteEventSerializer(events, many=True).data)


# ==================== Helper Functions ====================

def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
