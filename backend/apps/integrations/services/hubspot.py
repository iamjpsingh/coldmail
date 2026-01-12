"""HubSpot CRM sync service."""
import json
import logging
import requests
from datetime import datetime
from django.utils import timezone
from django.conf import settings

from ..models import Integration, HubSpotIntegration, IntegrationLog

logger = logging.getLogger(__name__)


class HubSpotService:
    """Service for HubSpot CRM synchronization."""

    BASE_URL = 'https://api.hubapi.com'

    # Default field mapping
    DEFAULT_FIELD_MAPPING = {
        'email': 'email',
        'first_name': 'firstname',
        'last_name': 'lastname',
        'company': 'company',
        'title': 'jobtitle',
        'phone': 'phone',
        'score': 'coldmail_score',
        'status': 'coldmail_status',
    }

    def __init__(self, integration: Integration):
        self.integration = integration
        self.hubspot_config = integration.hubspot_config

    @classmethod
    def get_for_workspace(cls, workspace):
        """Get HubSpot integration for a workspace."""
        try:
            integration = Integration.objects.select_related('hubspot_config').get(
                workspace=workspace,
                integration_type=Integration.IntegrationType.HUBSPOT,
                is_active=True,
            )
            return cls(integration)
        except Integration.DoesNotExist:
            return None

    def _get_headers(self):
        """Get authorization headers."""
        return {
            'Authorization': f'Bearer {self.integration.access_token}',
            'Content-Type': 'application/json',
        }

    def _refresh_token_if_needed(self):
        """Refresh the access token if expired."""
        if not self.integration.token_expires_at:
            return True

        if timezone.now() < self.integration.token_expires_at:
            return True

        # Need to refresh
        return self._refresh_access_token()

    def _refresh_access_token(self):
        """Refresh the HubSpot access token."""
        url = 'https://api.hubapi.com/oauth/v1/token'

        data = {
            'grant_type': 'refresh_token',
            'client_id': settings.HUBSPOT_CLIENT_ID,
            'client_secret': settings.HUBSPOT_CLIENT_SECRET,
            'refresh_token': self.integration.refresh_token,
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.json()

            if 'access_token' in result:
                self.integration.access_token = result['access_token']
                if 'refresh_token' in result:
                    self.integration.refresh_token = result['refresh_token']
                if 'expires_in' in result:
                    self.integration.token_expires_at = timezone.now() + timezone.timedelta(
                        seconds=result['expires_in']
                    )
                self.integration.save()
                return True
            else:
                logger.error(f"HubSpot token refresh failed: {result}")
                return False

        except requests.RequestException as e:
            logger.error(f"HubSpot token refresh request failed: {e}")
            return False

    def sync_contact(self, contact):
        """
        Sync a single contact to HubSpot.

        Args:
            contact: Contact model instance

        Returns:
            tuple: (success, hubspot_id or error message)
        """
        if not self._refresh_token_if_needed():
            return False, "Token refresh failed"

        # Check filters
        if self.hubspot_config.sync_only_hot_leads:
            if contact.score < self.hubspot_config.min_score_to_sync:
                return True, "Skipped - score below threshold"

        # Map fields
        properties = self._map_contact_to_hubspot(contact)

        # Check if contact exists in HubSpot
        hubspot_id = self._find_contact_by_email(contact.email)

        if hubspot_id:
            # Update existing contact
            success, result = self._update_contact(hubspot_id, properties)
        else:
            # Create new contact
            success, result = self._create_contact(properties)

        if success:
            self._log_sync('sync', f"Synced contact {contact.email}", records_processed=1)
            self.integration.record_sync(success=True)
        else:
            self._log_error('sync', f"Failed to sync contact {contact.email}: {result}")
            self.integration.record_sync(success=False, error_message=str(result))

        return success, result

    def sync_contacts(self, contacts):
        """
        Sync multiple contacts to HubSpot.

        Args:
            contacts: QuerySet or list of Contact instances

        Returns:
            dict: Sync results
        """
        if not self._refresh_token_if_needed():
            return {'success': False, 'error': 'Token refresh failed'}

        results = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
        }

        start_time = timezone.now()

        for contact in contacts:
            results['processed'] += 1

            # Check filters
            if self.hubspot_config.sync_only_hot_leads:
                if contact.score < self.hubspot_config.min_score_to_sync:
                    results['skipped'] += 1
                    continue

            success, result = self.sync_contact(contact)

            if success:
                if 'created' in str(result).lower():
                    results['created'] += 1
                else:
                    results['updated'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'email': contact.email,
                    'error': str(result),
                })

        duration = int((timezone.now() - start_time).total_seconds() * 1000)

        self._log_sync(
            'sync',
            f"Bulk sync completed: {results['processed']} processed, {results['created']} created, {results['updated']} updated, {results['failed']} failed",
            records_processed=results['processed'],
            records_created=results['created'],
            records_updated=results['updated'],
            records_failed=results['failed'],
            duration_ms=duration,
        )

        return results

    def _map_contact_to_hubspot(self, contact):
        """Map ColdMail contact fields to HubSpot properties."""
        mapping = self.hubspot_config.field_mapping or self.DEFAULT_FIELD_MAPPING
        properties = {}

        for coldmail_field, hubspot_field in mapping.items():
            value = getattr(contact, coldmail_field, None)
            if value is not None:
                properties[hubspot_field] = str(value)

        return properties

    def _find_contact_by_email(self, email):
        """Find a HubSpot contact by email."""
        url = f"{self.BASE_URL}/crm/v3/objects/contacts/search"

        payload = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }]
        }

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('total', 0) > 0:
                    return data['results'][0]['id']
            return None

        except requests.RequestException:
            return None

    def _create_contact(self, properties):
        """Create a new contact in HubSpot."""
        url = f"{self.BASE_URL}/crm/v3/objects/contacts"

        payload = {"properties": properties}

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )

            if response.status_code == 201:
                data = response.json()
                return True, data.get('id')
            else:
                return False, response.json().get('message', response.text)

        except requests.RequestException as e:
            return False, str(e)

    def _update_contact(self, hubspot_id, properties):
        """Update an existing contact in HubSpot."""
        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{hubspot_id}"

        payload = {"properties": properties}

        try:
            response = requests.patch(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                return True, hubspot_id
            else:
                return False, response.json().get('message', response.text)

        except requests.RequestException as e:
            return False, str(e)

    def get_contact(self, hubspot_id):
        """Get a contact from HubSpot."""
        if not self._refresh_token_if_needed():
            return None

        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{hubspot_id}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            return None

        except requests.RequestException:
            return None

    def test_connection(self):
        """Test the HubSpot connection."""
        if not self._refresh_token_if_needed():
            return False, "Token refresh failed"

        url = f"{self.BASE_URL}/crm/v3/objects/contacts"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params={'limit': 1},
                timeout=10
            )

            if response.status_code == 200:
                self.integration.status = Integration.Status.CONNECTED
                self.integration.save()
                self._log_sync('test', 'Connection test successful')
                return True, "Connected successfully"
            else:
                error = response.json().get('message', response.text)
                self._log_error('test', f'Connection test failed: {error}')
                return False, error

        except requests.RequestException as e:
            self._log_error('test', f'Connection test failed: {str(e)}')
            return False, str(e)

    def _log_sync(self, operation, message, **kwargs):
        """Log a sync operation."""
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


def get_hubspot_oauth_url(workspace, redirect_uri):
    """Generate HubSpot OAuth authorization URL."""
    client_id = settings.HUBSPOT_CLIENT_ID
    scope = 'crm.objects.contacts.read crm.objects.contacts.write'

    state = f"{workspace.id}"

    url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&scope={scope}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )

    return url


def exchange_hubspot_code(code, redirect_uri):
    """Exchange OAuth code for access token."""
    url = 'https://api.hubapi.com/oauth/v1/token'

    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.HUBSPOT_CLIENT_ID,
        'client_secret': settings.HUBSPOT_CLIENT_SECRET,
        'code': code,
        'redirect_uri': redirect_uri,
    }

    response = requests.post(url, data=data, timeout=10)
    result = response.json()

    if 'access_token' in result:
        return {
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'expires_in': result.get('expires_in', 21600),
        }
    else:
        raise Exception(result.get('message', 'OAuth exchange failed'))
