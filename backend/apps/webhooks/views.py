"""Views for API keys and webhooks."""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters

from apps.core.mixins import WorkspaceViewSetMixin
from .models import APIKey, Webhook, WebhookDelivery, WebhookEventLog
from .serializers import (
    APIKeySerializer,
    APIKeyCreateSerializer,
    APIKeyCreateResponseSerializer,
    APIKeyUpdateSerializer,
    WebhookSerializer,
    WebhookCreateSerializer,
    WebhookUpdateSerializer,
    WebhookSecretSerializer,
    WebhookDeliverySerializer,
    WebhookDeliveryListSerializer,
    WebhookEventLogSerializer,
    WebhookEventLogListSerializer,
    WebhookTestSerializer,
    EventTypeSerializer,
)
from .tasks import test_webhook, reactivate_webhook


class APIKeyFilter(filters.FilterSet):
    """Filter for API keys."""

    is_active = filters.BooleanFilter()
    permission = filters.CharFilter()
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = APIKey
        fields = ['is_active', 'permission']


class APIKeyViewSet(WorkspaceViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for managing API keys."""

    queryset = APIKey.objects.all()
    filterset_class = APIKeyFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'last_used_at', 'total_requests']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return APIKeyCreateSerializer
        if self.action in ['update', 'partial_update']:
            return APIKeyUpdateSerializer
        return APIKeySerializer

    def create(self, request, *args, **kwargs):
        """Create a new API key."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key = serializer.save()

        # Return the response with raw key (only shown once)
        response_serializer = APIKeyCreateResponseSerializer(api_key)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke (deactivate) an API key."""
        api_key = self.get_object()
        api_key.is_active = False
        api_key.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'revoked'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a revoked API key."""
        api_key = self.get_object()
        api_key.is_active = True
        api_key.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'activated'})


class WebhookFilter(filters.FilterSet):
    """Filter for webhooks."""

    is_active = filters.BooleanFilter()
    event_type = filters.CharFilter(method='filter_by_event')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Webhook
        fields = ['is_active']

    def filter_by_event(self, queryset, name, value):
        """Filter webhooks that subscribe to a specific event type."""
        # This is a simplified filter - for JSON contains
        return queryset.filter(events__contains=[value])


class WebhookViewSet(WorkspaceViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for managing webhooks."""

    queryset = Webhook.objects.all()
    filterset_class = WebhookFilter
    search_fields = ['name', 'description', 'url']
    ordering_fields = ['name', 'created_at', 'last_delivery_at', 'total_deliveries']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return WebhookCreateSerializer
        if self.action in ['update', 'partial_update']:
            return WebhookUpdateSerializer
        if self.action == 'secret':
            return WebhookSecretSerializer
        if self.action == 'test':
            return WebhookTestSerializer
        return WebhookSerializer

    @action(detail=True, methods=['get'])
    def secret(self, request, pk=None):
        """Get the webhook secret."""
        webhook = self.get_object()
        return Response({'secret': webhook.secret})

    @action(detail=True, methods=['post'])
    def regenerate_secret(self, request, pk=None):
        """Regenerate the webhook secret."""
        webhook = self.get_object()
        new_secret = webhook.regenerate_secret()
        return Response({'secret': new_secret})

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Send a test webhook event."""
        webhook = self.get_object()

        # Run synchronously for immediate feedback
        result = test_webhook(str(webhook.id))

        return Response(result)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a disabled webhook."""
        webhook = self.get_object()
        reactivate_webhook(str(webhook.id))
        webhook.refresh_from_db()
        serializer = self.get_serializer(webhook)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        """Get delivery logs for this webhook."""
        webhook = self.get_object()
        deliveries = webhook.deliveries.all()[:100]  # Limit to last 100
        serializer = WebhookDeliveryListSerializer(deliveries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def event_types(self, request):
        """Get list of available event types."""
        events = EventTypeSerializer.get_event_types()
        return Response(events)


class WebhookDeliveryFilter(filters.FilterSet):
    """Filter for webhook deliveries."""

    webhook = filters.UUIDFilter()
    status = filters.CharFilter()
    event_type = filters.CharFilter()
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = WebhookDelivery
        fields = ['webhook', 'status', 'event_type']


class WebhookDeliveryViewSet(WorkspaceViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing webhook delivery logs."""

    queryset = WebhookDelivery.objects.select_related('webhook').all()
    filterset_class = WebhookDeliveryFilter
    ordering_fields = ['created_at', 'delivered_at', 'duration_ms']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return WebhookDeliveryListSerializer
        return WebhookDeliverySerializer

    def get_queryset(self):
        """Filter deliveries by workspace through webhook relationship."""
        workspace = self.request.user.current_workspace
        return self.queryset.filter(webhook__workspace=workspace)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed delivery."""
        from .tasks import deliver_webhook

        delivery = self.get_object()

        if delivery.status == WebhookDelivery.Status.SUCCESS:
            return Response(
                {'error': 'Cannot retry a successful delivery'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not delivery.webhook.is_active:
            return Response(
                {'error': 'Webhook is disabled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reset and requeue
        delivery.status = WebhookDelivery.Status.PENDING
        delivery.attempt_number = 1
        delivery.next_retry_at = None
        delivery.save()

        deliver_webhook.delay(str(delivery.id))

        return Response({'status': 'queued'})


class WebhookEventLogFilter(filters.FilterSet):
    """Filter for webhook event logs."""

    event_type = filters.CharFilter()
    contact_id = filters.UUIDFilter()
    campaign_id = filters.UUIDFilter()
    sequence_id = filters.UUIDFilter()
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = WebhookEventLog
        fields = ['event_type', 'contact_id', 'campaign_id', 'sequence_id']


class WebhookEventLogViewSet(WorkspaceViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing webhook event logs."""

    queryset = WebhookEventLog.objects.all()
    filterset_class = WebhookEventLogFilter
    ordering_fields = ['created_at', 'event_type']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return WebhookEventLogListSerializer
        return WebhookEventLogSerializer
