"""Views for integrations."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.utils import timezone

from apps.core.mixins import WorkspaceViewSetMixin
from .models import (
    Integration, SlackIntegration, DiscordIntegration,
    HubSpotIntegration, SalesforceIntegration, GoogleSheetsIntegration,
    IntegrationLog
)
from .serializers import (
    IntegrationSerializer,
    IntegrationCreateSerializer,
    SlackIntegrationSerializer,
    DiscordIntegrationSerializer,
    DiscordIntegrationCreateSerializer,
    HubSpotIntegrationSerializer,
    SalesforceIntegrationSerializer,
    GoogleSheetsIntegrationSerializer,
    IntegrationLogSerializer,
    IntegrationTypeSerializer,
    TestConnectionSerializer,
    SyncResultSerializer,
)
from .services import (
    SlackNotificationService,
    DiscordNotificationService,
    HubSpotService,
    SalesforceService,
    GoogleSheetsService,
)


class IntegrationFilter(filters.FilterSet):
    """Filter for integrations."""

    integration_type = filters.CharFilter()
    status = filters.CharFilter()
    is_active = filters.BooleanFilter()

    class Meta:
        model = Integration
        fields = ['integration_type', 'status', 'is_active']


class IntegrationViewSet(WorkspaceViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for managing integrations."""

    queryset = Integration.objects.all()
    filterset_class = IntegrationFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'last_sync_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return IntegrationCreateSerializer
        return IntegrationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('created_by')

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get list of available integration types."""
        types = IntegrationTypeSerializer.get_integration_types()
        return Response(types)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test the integration connection."""
        integration = self.get_object()

        success, message = self._test_integration(integration)

        return Response({
            'success': success,
            'message': message,
        })

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Trigger a manual sync."""
        integration = self.get_object()

        result = self._run_sync(integration)

        return Response(result)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an integration."""
        integration = self.get_object()
        integration.is_active = True
        integration.save(update_fields=['is_active', 'updated_at'])
        serializer = self.get_serializer(integration)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate an integration."""
        integration = self.get_object()
        integration.is_active = False
        integration.save(update_fields=['is_active', 'updated_at'])
        serializer = self.get_serializer(integration)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs for an integration."""
        integration = self.get_object()
        logs = integration.logs.all()[:100]
        serializer = IntegrationLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'patch'])
    def settings(self, request, pk=None):
        """Get or update integration-specific settings."""
        integration = self.get_object()

        if request.method == 'GET':
            return self._get_integration_settings(integration)
        else:
            return self._update_integration_settings(integration, request.data)

    def _test_integration(self, integration):
        """Test an integration connection."""
        if integration.integration_type == Integration.IntegrationType.SLACK:
            service = SlackNotificationService(integration)
            return service.test_connection()

        elif integration.integration_type == Integration.IntegrationType.DISCORD:
            service = DiscordNotificationService(integration)
            return service.test_connection()

        elif integration.integration_type == Integration.IntegrationType.HUBSPOT:
            service = HubSpotService(integration)
            return service.test_connection()

        elif integration.integration_type == Integration.IntegrationType.SALESFORCE:
            service = SalesforceService(integration)
            return service.test_connection()

        elif integration.integration_type == Integration.IntegrationType.GOOGLE_SHEETS:
            service = GoogleSheetsService(integration)
            return service.test_connection()

        return False, "Integration type not supported for testing"

    def _run_sync(self, integration):
        """Run a sync for CRM integrations."""
        from apps.contacts.models import Contact

        workspace = integration.workspace
        contacts = Contact.objects.filter(workspace=workspace)

        if integration.integration_type == Integration.IntegrationType.HUBSPOT:
            service = HubSpotService(integration)
            return service.sync_contacts(contacts)

        elif integration.integration_type == Integration.IntegrationType.SALESFORCE:
            service = SalesforceService(integration)
            return service.sync_contacts(contacts)

        elif integration.integration_type == Integration.IntegrationType.GOOGLE_SHEETS:
            service = GoogleSheetsService(integration)
            success, result = service.export_contacts(contacts)
            return {'success': success, 'result': result}

        return {'error': 'Sync not supported for this integration type'}

    def _get_integration_settings(self, integration):
        """Get integration-specific settings."""
        if integration.integration_type == Integration.IntegrationType.SLACK:
            try:
                config = integration.slack_config
                serializer = SlackIntegrationSerializer(config)
                return Response(serializer.data)
            except SlackIntegration.DoesNotExist:
                return Response({})

        elif integration.integration_type == Integration.IntegrationType.DISCORD:
            try:
                config = integration.discord_config
                serializer = DiscordIntegrationSerializer(config)
                return Response(serializer.data)
            except DiscordIntegration.DoesNotExist:
                return Response({})

        elif integration.integration_type == Integration.IntegrationType.HUBSPOT:
            try:
                config = integration.hubspot_config
                serializer = HubSpotIntegrationSerializer(config)
                return Response(serializer.data)
            except HubSpotIntegration.DoesNotExist:
                return Response({})

        elif integration.integration_type == Integration.IntegrationType.SALESFORCE:
            try:
                config = integration.salesforce_config
                serializer = SalesforceIntegrationSerializer(config)
                return Response(serializer.data)
            except SalesforceIntegration.DoesNotExist:
                return Response({})

        elif integration.integration_type == Integration.IntegrationType.GOOGLE_SHEETS:
            try:
                config = integration.google_sheets_config
                serializer = GoogleSheetsIntegrationSerializer(config)
                return Response(serializer.data)
            except GoogleSheetsIntegration.DoesNotExist:
                return Response({})

        return Response({})

    def _update_integration_settings(self, integration, data):
        """Update integration-specific settings."""
        if integration.integration_type == Integration.IntegrationType.SLACK:
            config, _ = SlackIntegration.objects.get_or_create(integration=integration)
            serializer = SlackIntegrationSerializer(config, data=data, partial=True)

        elif integration.integration_type == Integration.IntegrationType.DISCORD:
            config, _ = DiscordIntegration.objects.get_or_create(
                integration=integration,
                defaults={'webhook_url': data.get('webhook_url', '')}
            )
            serializer = DiscordIntegrationSerializer(config, data=data, partial=True)

        elif integration.integration_type == Integration.IntegrationType.HUBSPOT:
            config, _ = HubSpotIntegration.objects.get_or_create(integration=integration)
            serializer = HubSpotIntegrationSerializer(config, data=data, partial=True)

        elif integration.integration_type == Integration.IntegrationType.SALESFORCE:
            config, _ = SalesforceIntegration.objects.get_or_create(integration=integration)
            serializer = SalesforceIntegrationSerializer(config, data=data, partial=True)

        elif integration.integration_type == Integration.IntegrationType.GOOGLE_SHEETS:
            config, _ = GoogleSheetsIntegration.objects.get_or_create(integration=integration)
            serializer = GoogleSheetsIntegrationSerializer(config, data=data, partial=True)

        else:
            return Response(
                {'error': 'Settings not supported for this integration type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DiscordIntegrationViewSet(WorkspaceViewSetMixin, viewsets.ViewSet):
    """ViewSet for creating Discord integrations (no OAuth required)."""

    @action(detail=False, methods=['post'])
    def create_integration(self, request):
        """Create a new Discord integration with webhook URL."""
        serializer = DiscordIntegrationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workspace = request.user.current_workspace
        user = request.user

        # Create the integration
        integration = Integration.objects.create(
            workspace=workspace,
            created_by=user,
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            integration_type=Integration.IntegrationType.DISCORD,
            status=Integration.Status.PENDING,
        )

        # Create the Discord config
        DiscordIntegration.objects.create(
            integration=integration,
            webhook_url=serializer.validated_data['webhook_url'],
            bot_username=serializer.validated_data.get('bot_username', 'ColdMail'),
            bot_avatar_url=serializer.validated_data.get('bot_avatar_url', ''),
        )

        # Test the connection
        service = DiscordNotificationService(integration)
        success, message = service.test_connection()

        if success:
            integration.status = Integration.Status.CONNECTED
            integration.save()

        return Response(
            IntegrationSerializer(integration).data,
            status=status.HTTP_201_CREATED
        )


class IntegrationLogViewSet(WorkspaceViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing integration logs."""

    queryset = IntegrationLog.objects.all()
    serializer_class = IntegrationLogSerializer
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter logs by workspace through integration relationship."""
        workspace = self.request.user.current_workspace
        return self.queryset.filter(integration__workspace=workspace)
