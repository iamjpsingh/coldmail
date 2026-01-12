from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.services import ReportsService


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics.

    GET /api/v1/reports/dashboard/
    Query params:
        - days: Number of days to look back (default: 30)
    """
    workspace_id = request.headers.get('X-Workspace-ID')
    days = int(request.query_params.get('days', 30))

    service = ReportsService(workspace_id)
    stats = service.get_dashboard_stats(days=days)

    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def email_stats_over_time(request):
    """Get email statistics over time.

    GET /api/v1/reports/email-stats/
    Query params:
        - days: Number of days (default: 30)
        - granularity: 'hour', 'day', 'week', 'month' (default: 'day')
    """
    workspace_id = request.headers.get('X-Workspace-ID')
    days = int(request.query_params.get('days', 30))
    granularity = request.query_params.get('granularity', 'day')

    service = ReportsService(workspace_id)
    stats = service.get_email_stats_over_time(days=days, granularity=granularity)

    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_report(request, campaign_id):
    """Get detailed campaign report.

    GET /api/v1/reports/campaigns/{id}/
    """
    workspace_id = request.headers.get('X-Workspace-ID')

    service = ReportsService(workspace_id)
    try:
        report = service.get_campaign_report(campaign_id)
        return Response(report)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def campaigns_comparison(request):
    """Compare multiple campaigns.

    POST /api/v1/reports/campaigns/compare/
    Body: { "campaign_ids": ["id1", "id2", ...] }
    """
    workspace_id = request.headers.get('X-Workspace-ID')
    campaign_ids = request.data.get('campaign_ids', [])

    if not campaign_ids:
        return Response(
            {'error': 'campaign_ids required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = ReportsService(workspace_id)
    comparison = service.get_campaigns_comparison(campaign_ids)

    return Response(comparison)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_timeline(request):
    """Get activity timeline.

    GET /api/v1/reports/activity/
    Query params:
        - limit: Max events (default: 50)
        - event_types: Comma-separated event types
        - contact_id: Filter by contact
        - campaign_id: Filter by campaign
    """
    workspace_id = request.headers.get('X-Workspace-ID')
    limit = int(request.query_params.get('limit', 50))
    event_types = request.query_params.get('event_types')
    contact_id = request.query_params.get('contact_id')
    campaign_id = request.query_params.get('campaign_id')

    if event_types:
        event_types = event_types.split(',')

    service = ReportsService(workspace_id)
    timeline = service.get_activity_timeline(
        limit=limit,
        event_types=event_types,
        contact_id=contact_id,
        campaign_id=campaign_id,
    )

    return Response(timeline)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hot_leads_report(request):
    """Get hot leads report.

    GET /api/v1/reports/hot-leads/
    Query params:
        - limit: Max leads (default: 50)
        - min_score: Minimum score threshold
    """
    workspace_id = request.headers.get('X-Workspace-ID')
    limit = int(request.query_params.get('limit', 50))
    min_score = request.query_params.get('min_score')

    if min_score:
        min_score = int(min_score)

    service = ReportsService(workspace_id)
    report = service.get_hot_leads_report(limit=limit, min_score=min_score)

    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def score_distribution(request):
    """Get contact score distribution.

    GET /api/v1/reports/score-distribution/
    """
    workspace_id = request.headers.get('X-Workspace-ID')

    service = ReportsService(workspace_id)
    distribution = service.get_score_distribution()

    return Response(distribution)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_summary(request):
    """Get performance summary with period comparison.

    GET /api/v1/reports/performance/
    Query params:
        - days: Period length in days (default: 7)
    """
    workspace_id = request.headers.get('X-Workspace-ID')
    days = int(request.query_params.get('days', 7))

    service = ReportsService(workspace_id)
    summary = service.get_performance_summary(days=days)

    return Response(summary)


# ==================== Export Endpoints ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_campaign_report(request, campaign_id):
    """Export campaign report to CSV.

    GET /api/v1/reports/campaigns/{id}/export/
    """
    workspace_id = request.headers.get('X-Workspace-ID')

    service = ReportsService(workspace_id)
    csv_data = service.export_campaign_report_csv(campaign_id)

    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="campaign_{campaign_id}_report.csv"'

    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_contacts(request):
    """Export contacts to CSV.

    POST /api/v1/reports/contacts/export/
    Body: {
        "filters": { "tags": [], "score_min": 0, "score_max": 100 },
        "fields": ["email", "first_name", "last_name", ...]
    }
    """
    workspace_id = request.headers.get('X-Workspace-ID')
    filters = request.data.get('filters')
    fields = request.data.get('fields')

    service = ReportsService(workspace_id)
    csv_data = service.export_contacts_csv(filters=filters, fields=fields)

    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts_export.csv"'

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_hot_leads(request):
    """Export hot leads to CSV.

    GET /api/v1/reports/hot-leads/export/
    Query params:
        - min_score: Minimum score threshold (default: 70)
    """
    workspace_id = request.headers.get('X-Workspace-ID')
    min_score = int(request.query_params.get('min_score', 70))

    service = ReportsService(workspace_id)
    csv_data = service.export_hot_leads_csv(min_score=min_score)

    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hot_leads.csv"'

    return response
