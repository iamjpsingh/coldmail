"""Google Sheets export service."""
import json
import logging
from datetime import datetime
from django.utils import timezone
from django.conf import settings

from ..models import Integration, GoogleSheetsIntegration, IntegrationLog

logger = logging.getLogger(__name__)

# Google API imports - optional dependency
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    logger.warning("Google API libraries not installed. Install google-api-python-client and google-auth")


class GoogleSheetsService:
    """Service for Google Sheets export."""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # Default columns for exports
    DEFAULT_CONTACT_COLUMNS = [
        'email', 'first_name', 'last_name', 'company', 'title',
        'phone', 'score', 'status', 'created_at'
    ]

    DEFAULT_HOT_LEAD_COLUMNS = [
        'email', 'first_name', 'last_name', 'company', 'title',
        'score', 'last_activity_at', 'total_opens', 'total_clicks'
    ]

    def __init__(self, integration: Integration):
        self.integration = integration
        self.sheets_config = integration.google_sheets_config
        self._service = None

    @classmethod
    def get_for_workspace(cls, workspace):
        """Get Google Sheets integration for a workspace."""
        try:
            integration = Integration.objects.select_related('google_sheets_config').get(
                workspace=workspace,
                integration_type=Integration.IntegrationType.GOOGLE_SHEETS,
                is_active=True,
            )
            return cls(integration)
        except Integration.DoesNotExist:
            return None

    def _get_service(self):
        """Get or create Google Sheets API service."""
        if not GOOGLE_APIS_AVAILABLE:
            raise Exception("Google API libraries not installed")

        if self._service:
            return self._service

        if not self.integration.access_token:
            raise Exception("No access token configured")

        creds = Credentials(
            token=self.integration.access_token,
            refresh_token=self.integration.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GOOGLE_SHEETS_CLIENT_ID,
            client_secret=settings.GOOGLE_SHEETS_CLIENT_SECRET,
        )

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self.integration.access_token = creds.token
            self.integration.save()

        self._service = build('sheets', 'v4', credentials=creds)
        return self._service

    def export_contacts(self, contacts):
        """
        Export contacts to Google Sheets.

        Args:
            contacts: QuerySet or list of Contact instances

        Returns:
            tuple: (success, result or error message)
        """
        if not self.sheets_config.export_contacts:
            return True, "Contacts export disabled"

        columns = self.sheets_config.contact_columns or self.DEFAULT_CONTACT_COLUMNS

        try:
            service = self._get_service()
            spreadsheet_id = self.sheets_config.spreadsheet_id
            sheet_name = self.sheets_config.contacts_sheet_name

            # Prepare data
            rows = [columns]  # Header row
            for contact in contacts:
                row = []
                for col in columns:
                    value = getattr(contact, col, '')
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row.append(str(value) if value else '')
                rows.append(row)

            # Clear existing data and write new
            range_name = f"{sheet_name}!A1:Z"

            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                body={}
            ).execute()

            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()

            self._log_export(
                'export',
                f"Exported {len(contacts)} contacts to Google Sheets",
                records_processed=len(contacts)
            )
            self.integration.record_sync(success=True)

            return True, {'rows_exported': len(contacts)}

        except Exception as e:
            self._log_error('export', f"Contacts export failed: {str(e)}")
            self.integration.record_sync(success=False, error_message=str(e))
            return False, str(e)

    def export_hot_leads(self, contacts, min_score=70):
        """
        Export hot leads to Google Sheets.

        Args:
            contacts: QuerySet or list of Contact instances
            min_score: Minimum score threshold

        Returns:
            tuple: (success, result or error message)
        """
        if not self.sheets_config.export_hot_leads:
            return True, "Hot leads export disabled"

        columns = self.sheets_config.hot_lead_columns or self.DEFAULT_HOT_LEAD_COLUMNS

        try:
            service = self._get_service()
            spreadsheet_id = self.sheets_config.spreadsheet_id
            sheet_name = self.sheets_config.hot_leads_sheet_name

            # Filter by score
            hot_leads = [c for c in contacts if c.score >= min_score]

            # Prepare data
            rows = [columns]  # Header row
            for contact in hot_leads:
                row = []
                for col in columns:
                    value = getattr(contact, col, '')
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row.append(str(value) if value else '')
                rows.append(row)

            # Clear existing data and write new
            range_name = f"{sheet_name}!A1:Z"

            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                body={}
            ).execute()

            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()

            self._log_export(
                'export',
                f"Exported {len(hot_leads)} hot leads to Google Sheets",
                records_processed=len(hot_leads)
            )
            self.integration.record_sync(success=True)

            return True, {'rows_exported': len(hot_leads)}

        except Exception as e:
            self._log_error('export', f"Hot leads export failed: {str(e)}")
            self.integration.record_sync(success=False, error_message=str(e))
            return False, str(e)

    def export_campaign_stats(self, campaigns):
        """
        Export campaign statistics to Google Sheets.

        Args:
            campaigns: QuerySet or list of Campaign instances

        Returns:
            tuple: (success, result or error message)
        """
        if not self.sheets_config.export_campaign_stats:
            return True, "Campaign stats export disabled"

        columns = [
            'name', 'status', 'total_contacts', 'emails_sent',
            'open_rate', 'click_rate', 'reply_count', 'created_at'
        ]

        try:
            service = self._get_service()
            spreadsheet_id = self.sheets_config.spreadsheet_id
            sheet_name = self.sheets_config.campaign_stats_sheet_name

            # Prepare data
            rows = [columns]  # Header row
            for campaign in campaigns:
                row = [
                    campaign.name,
                    campaign.status,
                    campaign.total_contacts,
                    campaign.emails_sent,
                    f"{campaign.open_rate:.1f}%",
                    f"{campaign.click_rate:.1f}%",
                    campaign.reply_count,
                    campaign.created_at.isoformat() if campaign.created_at else '',
                ]
                rows.append(row)

            # Clear existing data and write new
            range_name = f"{sheet_name}!A1:Z"

            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                body={}
            ).execute()

            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()

            self._log_export(
                'export',
                f"Exported {len(campaigns)} campaigns to Google Sheets",
                records_processed=len(campaigns)
            )
            self.integration.record_sync(success=True)

            return True, {'rows_exported': len(campaigns)}

        except Exception as e:
            self._log_error('export', f"Campaign stats export failed: {str(e)}")
            self.integration.record_sync(success=False, error_message=str(e))
            return False, str(e)

    def create_spreadsheet(self, title):
        """
        Create a new Google Spreadsheet.

        Args:
            title: Spreadsheet title

        Returns:
            tuple: (success, spreadsheet_id or error message)
        """
        try:
            service = self._get_service()

            spreadsheet = {
                'properties': {'title': title},
                'sheets': [
                    {'properties': {'title': self.sheets_config.contacts_sheet_name}},
                    {'properties': {'title': self.sheets_config.hot_leads_sheet_name}},
                    {'properties': {'title': self.sheets_config.campaign_stats_sheet_name}},
                ]
            }

            result = service.spreadsheets().create(body=spreadsheet).execute()

            spreadsheet_id = result['spreadsheetId']
            spreadsheet_url = result['spreadsheetUrl']

            # Update config
            self.sheets_config.spreadsheet_id = spreadsheet_id
            self.sheets_config.spreadsheet_name = title
            self.sheets_config.spreadsheet_url = spreadsheet_url
            self.sheets_config.save()

            self._log_export('export', f"Created spreadsheet: {title}")

            return True, spreadsheet_id

        except Exception as e:
            self._log_error('export', f"Failed to create spreadsheet: {str(e)}")
            return False, str(e)

    def test_connection(self):
        """Test the Google Sheets connection."""
        try:
            service = self._get_service()

            # Try to get spreadsheet metadata
            if self.sheets_config.spreadsheet_id:
                result = service.spreadsheets().get(
                    spreadsheetId=self.sheets_config.spreadsheet_id
                ).execute()

                self.sheets_config.spreadsheet_name = result['properties']['title']
                self.sheets_config.save()

            self.integration.status = Integration.Status.CONNECTED
            self.integration.save()
            self._log_export('test', 'Connection test successful')
            return True, "Connected successfully"

        except Exception as e:
            self._log_error('test', f'Connection test failed: {str(e)}')
            return False, str(e)

    def _log_export(self, operation, message, **kwargs):
        """Log an export operation."""
        IntegrationLog.objects.create(
            integration=self.integration,
            level=IntegrationLog.LogLevel.INFO,
            operation=operation,
            message=message,
            **kwargs
        )

    def _log_error(self, operation, message, details=None):
        """Log an error."""
        IntegrationLog.objects.create(
            integration=self.integration,
            level=IntegrationLog.LogLevel.ERROR,
            operation=operation,
            message=message,
            error_details=details or {},
        )


def get_google_sheets_oauth_url(workspace, redirect_uri):
    """Generate Google Sheets OAuth authorization URL."""
    client_id = settings.GOOGLE_SHEETS_CLIENT_ID
    scope = 'https://www.googleapis.com/auth/spreadsheets'

    state = f"{workspace.id}"

    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={state}"
    )

    return url


def exchange_google_sheets_code(code, redirect_uri):
    """Exchange OAuth code for access token."""
    import requests

    url = 'https://oauth2.googleapis.com/token'

    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.GOOGLE_SHEETS_CLIENT_ID,
        'client_secret': settings.GOOGLE_SHEETS_CLIENT_SECRET,
        'code': code,
        'redirect_uri': redirect_uri,
    }

    response = requests.post(url, data=data, timeout=10)
    result = response.json()

    if 'access_token' in result:
        return {
            'access_token': result['access_token'],
            'refresh_token': result.get('refresh_token'),
            'expires_in': result.get('expires_in', 3600),
        }
    else:
        raise Exception(result.get('error_description', 'OAuth exchange failed'))
