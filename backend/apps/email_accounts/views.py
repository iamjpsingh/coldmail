import uuid

from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import EmailAccount, EmailAccountLog
from .serializers import (
    EmailAccountSerializer,
    EmailAccountCreateSerializer,
    EmailAccountUpdateSerializer,
    EmailAccountLogSerializer,
    ConnectionTestSerializer,
    SendTestEmailSerializer,
)
from .services import EmailService, GoogleOAuthService, MicrosoftOAuthService


class EmailAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email accounts."""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'provider']

    def get_queryset(self):
        """Return email accounts for the current user."""
        return EmailAccount.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return EmailAccountCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmailAccountUpdateSerializer
        return EmailAccountSerializer

    def perform_create(self, serializer):
        """Set the user when creating an email account."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test SMTP/IMAP connection for an email account."""
        account = self.get_object()
        serializer = ConnectionTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = EmailService(account)
        results = {}

        if serializer.validated_data.get('test_smtp', True):
            smtp_result = service.test_smtp_connection()
            results['smtp'] = {
                'success': smtp_result.success,
                'message': smtp_result.message
            }

        if serializer.validated_data.get('test_imap', False):
            imap_result = service.test_imap_connection()
            results['imap'] = {
                'success': imap_result.success,
                'message': imap_result.message
            }

        overall_success = all(r.get('success', False) for r in results.values())

        return Response({
            'success': overall_success,
            'results': results
        }, status=status.HTTP_200_OK if overall_success else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def send_test_email(self, request, pk=None):
        """Send a test email."""
        account = self.get_object()
        serializer = SendTestEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Use appropriate service based on provider
        if account.provider == EmailAccount.Provider.GMAIL:
            service = GoogleOAuthService()
            result = service.send_email(
                account,
                to_email=serializer.validated_data['to_email'],
                subject=serializer.validated_data['subject'],
                html_body=f"<p>{serializer.validated_data['body']}</p>",
                text_body=serializer.validated_data['body']
            )
        elif account.provider == EmailAccount.Provider.OUTLOOK:
            service = MicrosoftOAuthService()
            result = service.send_email(
                account,
                to_email=serializer.validated_data['to_email'],
                subject=serializer.validated_data['subject'],
                html_body=f"<p>{serializer.validated_data['body']}</p>",
                text_body=serializer.validated_data['body']
            )
        else:
            service = EmailService(account)
            result = service.send_email(
                to_email=serializer.validated_data['to_email'],
                subject=serializer.validated_data['subject'],
                html_body=f"<p>{serializer.validated_data['body']}</p>",
                text_body=serializer.validated_data['body']
            )

        if result.success:
            return Response({
                'success': True,
                'message': result.message,
                'message_id': getattr(result, 'message_id', None) or result.data.get('message_id') if result.data else None
            })
        else:
            return Response({
                'success': False,
                'message': result.message
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause an email account."""
        account = self.get_object()
        account.status = EmailAccount.Status.PAUSED
        account.save(update_fields=['status'])
        return Response({'status': 'paused'})

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused email account."""
        account = self.get_object()
        account.status = EmailAccount.Status.ACTIVE
        account.save(update_fields=['status'])
        return Response({'status': 'active'})

    @action(detail=True, methods=['post'])
    def start_warmup(self, request, pk=None):
        """Start email warmup process."""
        account = self.get_object()
        daily_increase = request.data.get('daily_increase', 5)
        starting_limit = request.data.get('starting_limit', 10)

        account.is_warming_up = True
        account.warmup_daily_increase = daily_increase
        account.warmup_current_limit = starting_limit
        account.warmup_started_at = timezone.now()
        account.save(update_fields=[
            'is_warming_up', 'warmup_daily_increase',
            'warmup_current_limit', 'warmup_started_at'
        ])

        return Response({
            'status': 'warmup_started',
            'current_limit': account.warmup_current_limit,
            'daily_increase': account.warmup_daily_increase
        })

    @action(detail=True, methods=['post'])
    def stop_warmup(self, request, pk=None):
        """Stop email warmup process."""
        account = self.get_object()
        account.is_warming_up = False
        account.save(update_fields=['is_warming_up'])
        return Response({'status': 'warmup_stopped'})

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs for an email account."""
        account = self.get_object()
        logs = account.logs.all()[:100]
        serializer = EmailAccountLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for an email account."""
        account = self.get_object()
        return Response({
            'total_emails_sent': account.total_emails_sent,
            'emails_sent_today': account.emails_sent_today,
            'emails_sent_this_hour': account.emails_sent_this_hour,
            'remaining_today': account.remaining_today,
            'remaining_this_hour': account.remaining_this_hour,
            'can_send': account.can_send,
            'bounce_rate': account.bounce_rate,
            'reputation_score': account.reputation_score,
            'is_warming_up': account.is_warming_up,
            'warmup_current_limit': account.warmup_current_limit,
            'last_email_sent_at': account.last_email_sent_at,
        })


class GoogleOAuthInitView(APIView):
    """Initiate Google OAuth flow."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = GoogleOAuthService()
        state = f"{request.user.id}:{uuid.uuid4()}"

        # Store state in session
        request.session['oauth_state'] = state

        auth_url, _ = service.get_authorization_url(state=state)
        return Response({'authorization_url': auth_url})


class GoogleOAuthCallbackView(APIView):
    """Handle Google OAuth callback."""
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')

        if error:
            return redirect(f"{self._get_frontend_url()}/email-accounts?error={error}")

        if not code:
            return redirect(f"{self._get_frontend_url()}/email-accounts?error=no_code")

        # Extract user_id from state
        try:
            user_id = state.split(':')[0]
        except:
            return redirect(f"{self._get_frontend_url()}/email-accounts?error=invalid_state")

        service = GoogleOAuthService()
        result = service.exchange_code(code)

        if not result.success:
            return redirect(f"{self._get_frontend_url()}/email-accounts?error={result.message}")

        # Create or update email account
        from apps.users.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect(f"{self._get_frontend_url()}/email-accounts?error=user_not_found")

        email_account, created = EmailAccount.objects.update_or_create(
            user=user,
            email=result.data['email'],
            defaults={
                'name': result.data.get('name') or result.data['email'],
                'provider': EmailAccount.Provider.GMAIL,
                'oauth_access_token': result.data['access_token'],
                'oauth_refresh_token': result.data['refresh_token'],
                'oauth_token_expires_at': result.data.get('token_expires_at'),
                'from_name': result.data.get('name', ''),
                'status': EmailAccount.Status.ACTIVE,
            }
        )

        return redirect(f"{self._get_frontend_url()}/email-accounts?success=true&email={result.data['email']}")

    def _get_frontend_url(self):
        import os
        return os.environ.get('FRONTEND_URL', 'http://localhost:5173')


class MicrosoftOAuthInitView(APIView):
    """Initiate Microsoft OAuth flow."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = MicrosoftOAuthService()
        state = f"{request.user.id}:{uuid.uuid4()}"

        request.session['oauth_state'] = state

        auth_url, _ = service.get_authorization_url(state=state)
        return Response({'authorization_url': auth_url})


class MicrosoftOAuthCallbackView(APIView):
    """Handle Microsoft OAuth callback."""
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')

        if error:
            error_desc = request.query_params.get('error_description', error)
            return redirect(f"{self._get_frontend_url()}/email-accounts?error={error_desc}")

        if not code:
            return redirect(f"{self._get_frontend_url()}/email-accounts?error=no_code")

        try:
            user_id = state.split(':')[0]
        except:
            return redirect(f"{self._get_frontend_url()}/email-accounts?error=invalid_state")

        service = MicrosoftOAuthService()
        result = service.exchange_code(code)

        if not result.success:
            return redirect(f"{self._get_frontend_url()}/email-accounts?error={result.message}")

        from apps.users.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect(f"{self._get_frontend_url()}/email-accounts?error=user_not_found")

        email_account, created = EmailAccount.objects.update_or_create(
            user=user,
            email=result.data['email'],
            defaults={
                'name': result.data.get('name') or result.data['email'],
                'provider': EmailAccount.Provider.OUTLOOK,
                'oauth_access_token': result.data['access_token'],
                'oauth_refresh_token': result.data['refresh_token'],
                'oauth_token_expires_at': result.data.get('token_expires_at'),
                'from_name': result.data.get('name', ''),
                'status': EmailAccount.Status.ACTIVE,
            }
        )

        return redirect(f"{self._get_frontend_url()}/email-accounts?success=true&email={result.data['email']}")

    def _get_frontend_url(self):
        import os
        return os.environ.get('FRONTEND_URL', 'http://localhost:5173')
