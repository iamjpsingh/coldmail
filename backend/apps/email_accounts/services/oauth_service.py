import os
import json
import base64
from typing import Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import msal

from apps.email_accounts.models import EmailAccount, EmailAccountLog


@dataclass
class OAuthResult:
    """Result of OAuth operation."""
    success: bool
    message: str
    data: dict = None


class GoogleOAuthService:
    """Service for Google OAuth operations."""

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
    ]

    def __init__(self):
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
        self.redirect_uri = os.environ.get(
            'GOOGLE_REDIRECT_URI',
            'http://localhost:8000/api/v1/email-accounts/oauth/google/callback/'
        )

    def get_authorization_url(self, state: str = None) -> Tuple[str, str]:
        """Get the Google OAuth authorization URL."""
        flow = Flow.from_client_config(
            {
                'web': {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'redirect_uris': [self.redirect_uri],
                }
            },
            scopes=self.SCOPES
        )
        flow.redirect_uri = self.redirect_uri

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state
        )

        return authorization_url, state

    def exchange_code(self, code: str) -> OAuthResult:
        """Exchange authorization code for tokens."""
        try:
            flow = Flow.from_client_config(
                {
                    'web': {
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                        'token_uri': 'https://oauth2.googleapis.com/token',
                        'redirect_uris': [self.redirect_uri],
                    }
                },
                scopes=self.SCOPES
            )
            flow.redirect_uri = self.redirect_uri
            flow.fetch_token(code=code)

            credentials = flow.credentials

            # Get user info
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()

            return OAuthResult(
                success=True,
                message='Successfully authenticated with Google',
                data={
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_expires_at': credentials.expiry.isoformat() if credentials.expiry else None,
                    'email': user_info.get('email'),
                    'name': user_info.get('name', ''),
                }
            )

        except Exception as e:
            return OAuthResult(
                success=False,
                message=f'Failed to authenticate with Google: {str(e)}'
            )

    def refresh_token(self, email_account: EmailAccount) -> OAuthResult:
        """Refresh the access token."""
        try:
            credentials = Credentials(
                token=email_account.oauth_access_token,
                refresh_token=email_account.oauth_refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            # Force refresh
            from google.auth.transport.requests import Request
            credentials.refresh(Request())

            # Update account
            email_account.oauth_access_token = credentials.token
            if credentials.refresh_token:
                email_account.oauth_refresh_token = credentials.refresh_token
            email_account.oauth_token_expires_at = credentials.expiry
            email_account.save(update_fields=[
                'oauth_access_token', 'oauth_refresh_token', 'oauth_token_expires_at'
            ])

            # Log refresh
            EmailAccountLog.objects.create(
                email_account=email_account,
                log_type=EmailAccountLog.LogType.OAUTH_REFRESH,
                message='OAuth token refreshed successfully',
                is_success=True
            )

            return OAuthResult(
                success=True,
                message='Token refreshed successfully'
            )

        except Exception as e:
            EmailAccountLog.objects.create(
                email_account=email_account,
                log_type=EmailAccountLog.LogType.OAUTH_REFRESH,
                message=f'Failed to refresh token: {str(e)}',
                is_success=False
            )
            return OAuthResult(
                success=False,
                message=f'Failed to refresh token: {str(e)}'
            )

    def send_email(
        self,
        email_account: EmailAccount,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> OAuthResult:
        """Send email using Gmail API."""
        try:
            # Check if token needs refresh
            if email_account.oauth_token_expires_at:
                if timezone.now() >= email_account.oauth_token_expires_at - timedelta(minutes=5):
                    refresh_result = self.refresh_token(email_account)
                    if not refresh_result.success:
                        return refresh_result

            credentials = Credentials(
                token=email_account.oauth_access_token,
                refresh_token=email_account.oauth_refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            service = build('gmail', 'v1', credentials=credentials)

            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['from'] = f"{email_account.from_name} <{email_account.email}>" if email_account.from_name else email_account.email
            message['subject'] = subject

            if text_body:
                message.attach(MIMEText(text_body, 'plain'))
            message.attach(MIMEText(html_body, 'html'))

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            # Update counters
            email_account.increment_sent_count()

            return OAuthResult(
                success=True,
                message='Email sent successfully',
                data={'message_id': result.get('id')}
            )

        except Exception as e:
            return OAuthResult(
                success=False,
                message=f'Failed to send email: {str(e)}'
            )


class MicrosoftOAuthService:
    """Service for Microsoft OAuth operations."""

    SCOPES = [
        'https://graph.microsoft.com/Mail.Send',
        'https://graph.microsoft.com/Mail.Read',
        'https://graph.microsoft.com/User.Read',
        'offline_access',
    ]

    def __init__(self):
        self.client_id = os.environ.get('MICROSOFT_CLIENT_ID', '')
        self.client_secret = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
        self.tenant_id = os.environ.get('MICROSOFT_TENANT_ID', 'common')
        self.redirect_uri = os.environ.get(
            'MICROSOFT_REDIRECT_URI',
            'http://localhost:8000/api/v1/email-accounts/oauth/microsoft/callback/'
        )
        self.authority = f'https://login.microsoftonline.com/{self.tenant_id}'

    def _get_msal_app(self) -> msal.ConfidentialClientApplication:
        """Get MSAL application instance."""
        return msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )

    def get_authorization_url(self, state: str = None) -> Tuple[str, str]:
        """Get the Microsoft OAuth authorization URL."""
        app = self._get_msal_app()

        auth_url = app.get_authorization_request_url(
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri,
            state=state,
        )

        return auth_url, state

    def exchange_code(self, code: str) -> OAuthResult:
        """Exchange authorization code for tokens."""
        try:
            app = self._get_msal_app()

            result = app.acquire_token_by_authorization_code(
                code=code,
                scopes=self.SCOPES,
                redirect_uri=self.redirect_uri,
            )

            if 'access_token' not in result:
                return OAuthResult(
                    success=False,
                    message=result.get('error_description', 'Failed to get access token')
                )

            # Get user info
            import requests
            headers = {'Authorization': f"Bearer {result['access_token']}"}
            user_response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers
            )
            user_info = user_response.json()

            # Calculate expiry
            expires_in = result.get('expires_in', 3600)
            expires_at = timezone.now() + timedelta(seconds=expires_in)

            return OAuthResult(
                success=True,
                message='Successfully authenticated with Microsoft',
                data={
                    'access_token': result['access_token'],
                    'refresh_token': result.get('refresh_token', ''),
                    'token_expires_at': expires_at.isoformat(),
                    'email': user_info.get('mail') or user_info.get('userPrincipalName'),
                    'name': user_info.get('displayName', ''),
                }
            )

        except Exception as e:
            return OAuthResult(
                success=False,
                message=f'Failed to authenticate with Microsoft: {str(e)}'
            )

    def refresh_token(self, email_account: EmailAccount) -> OAuthResult:
        """Refresh the access token."""
        try:
            app = self._get_msal_app()

            result = app.acquire_token_by_refresh_token(
                refresh_token=email_account.oauth_refresh_token,
                scopes=self.SCOPES,
            )

            if 'access_token' not in result:
                return OAuthResult(
                    success=False,
                    message=result.get('error_description', 'Failed to refresh token')
                )

            # Calculate expiry
            expires_in = result.get('expires_in', 3600)
            expires_at = timezone.now() + timedelta(seconds=expires_in)

            # Update account
            email_account.oauth_access_token = result['access_token']
            if result.get('refresh_token'):
                email_account.oauth_refresh_token = result['refresh_token']
            email_account.oauth_token_expires_at = expires_at
            email_account.save(update_fields=[
                'oauth_access_token', 'oauth_refresh_token', 'oauth_token_expires_at'
            ])

            EmailAccountLog.objects.create(
                email_account=email_account,
                log_type=EmailAccountLog.LogType.OAUTH_REFRESH,
                message='OAuth token refreshed successfully',
                is_success=True
            )

            return OAuthResult(
                success=True,
                message='Token refreshed successfully'
            )

        except Exception as e:
            EmailAccountLog.objects.create(
                email_account=email_account,
                log_type=EmailAccountLog.LogType.OAUTH_REFRESH,
                message=f'Failed to refresh token: {str(e)}',
                is_success=False
            )
            return OAuthResult(
                success=False,
                message=f'Failed to refresh token: {str(e)}'
            )

    def send_email(
        self,
        email_account: EmailAccount,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> OAuthResult:
        """Send email using Microsoft Graph API."""
        try:
            import requests

            # Check if token needs refresh
            if email_account.oauth_token_expires_at:
                if timezone.now() >= email_account.oauth_token_expires_at - timedelta(minutes=5):
                    refresh_result = self.refresh_token(email_account)
                    if not refresh_result.success:
                        return refresh_result

            headers = {
                'Authorization': f'Bearer {email_account.oauth_access_token}',
                'Content-Type': 'application/json',
            }

            # Create message
            message = {
                'message': {
                    'subject': subject,
                    'body': {
                        'contentType': 'HTML',
                        'content': html_body,
                    },
                    'toRecipients': [
                        {'emailAddress': {'address': to_email}}
                    ],
                },
                'saveToSentItems': True,
            }

            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/sendMail',
                headers=headers,
                json=message
            )

            if response.status_code == 202:
                # Update counters
                email_account.increment_sent_count()

                return OAuthResult(
                    success=True,
                    message='Email sent successfully'
                )
            else:
                error = response.json()
                return OAuthResult(
                    success=False,
                    message=f"Failed to send email: {error.get('error', {}).get('message', 'Unknown error')}"
                )

        except Exception as e:
            return OAuthResult(
                success=False,
                message=f'Failed to send email: {str(e)}'
            )
