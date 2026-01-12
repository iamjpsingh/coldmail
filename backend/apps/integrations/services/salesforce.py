"""Salesforce CRM sync service."""
import json
import logging
import requests
from datetime import datetime
from django.utils import timezone
from django.conf import settings

from ..models import Integration, SalesforceIntegration, IntegrationLog

logger = logging.getLogger(__name__)


class SalesforceService:
    """Service for Salesforce CRM synchronization."""

    # Default field mapping for Leads
    DEFAULT_LEAD_MAPPING = {
        'email': 'Email',
        'first_name': 'FirstName',
        'last_name': 'LastName',
        'company': 'Company',
        'title': 'Title',
        'phone': 'Phone',
    }

    # Default field mapping for Contacts
    DEFAULT_CONTACT_MAPPING = {
        'email': 'Email',
        'first_name': 'FirstName',
        'last_name': 'LastName',
        'title': 'Title',
        'phone': 'Phone',
    }

    def __init__(self, integration: Integration):
        self.integration = integration
        self.salesforce_config = integration.salesforce_config

    @classmethod
    def get_for_workspace(cls, workspace):
        """Get Salesforce integration for a workspace."""
        try:
            integration = Integration.objects.select_related('salesforce_config').get(
                workspace=workspace,
                integration_type=Integration.IntegrationType.SALESFORCE,
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

    def _get_api_url(self, endpoint):
        """Get full API URL."""
        instance_url = self.salesforce_config.instance_url
        return f"{instance_url}/services/data/v58.0/{endpoint}"

    def _refresh_token_if_needed(self):
        """Refresh the access token if expired."""
        if not self.integration.token_expires_at:
            return True

        if timezone.now() < self.integration.token_expires_at:
            return True

        return self._refresh_access_token()

    def _refresh_access_token(self):
        """Refresh the Salesforce access token."""
        url = 'https://login.salesforce.com/services/oauth2/token'

        data = {
            'grant_type': 'refresh_token',
            'client_id': settings.SALESFORCE_CLIENT_ID,
            'client_secret': settings.SALESFORCE_CLIENT_SECRET,
            'refresh_token': self.integration.refresh_token,
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.json()

            if 'access_token' in result:
                self.integration.access_token = result['access_token']
                # Salesforce tokens typically last 2 hours
                self.integration.token_expires_at = timezone.now() + timezone.timedelta(hours=2)
                self.integration.save()
                return True
            else:
                logger.error(f"Salesforce token refresh failed: {result}")
                return False

        except requests.RequestException as e:
            logger.error(f"Salesforce token refresh request failed: {e}")
            return False

    def sync_contact(self, contact):
        """
        Sync a single contact to Salesforce as Lead or Contact.

        Args:
            contact: Contact model instance

        Returns:
            tuple: (success, salesforce_id or error message)
        """
        if not self._refresh_token_if_needed():
            return False, "Token refresh failed"

        # Check filters
        if self.salesforce_config.sync_only_hot_leads:
            if contact.score < self.salesforce_config.min_score_to_sync:
                return True, "Skipped - score below threshold"

        # Determine if we're creating a Lead or Contact
        if self.salesforce_config.create_as_lead:
            return self._sync_as_lead(contact)
        else:
            return self._sync_as_contact(contact)

    def _sync_as_lead(self, contact):
        """Sync contact as a Salesforce Lead."""
        # Map fields
        properties = self._map_contact_to_salesforce(contact, is_lead=True)

        # Ensure required fields
        if not properties.get('Company'):
            properties['Company'] = contact.company or 'Unknown'

        if not properties.get('LastName'):
            properties['LastName'] = contact.last_name or contact.email.split('@')[0]

        # Check if lead exists
        existing_id = self._find_lead_by_email(contact.email)

        if existing_id:
            success, result = self._update_record('Lead', existing_id, properties)
        else:
            success, result = self._create_record('Lead', properties)

        if success:
            self._log_sync('sync', f"Synced lead {contact.email}", records_processed=1)
            self.integration.record_sync(success=True)
        else:
            self._log_error('sync', f"Failed to sync lead {contact.email}: {result}")
            self.integration.record_sync(success=False, error_message=str(result))

        return success, result

    def _sync_as_contact(self, contact):
        """Sync contact as a Salesforce Contact."""
        properties = self._map_contact_to_salesforce(contact, is_lead=False)

        # Ensure required fields
        if not properties.get('LastName'):
            properties['LastName'] = contact.last_name or contact.email.split('@')[0]

        # Check if contact exists
        existing_id = self._find_contact_by_email(contact.email)

        if existing_id:
            success, result = self._update_record('Contact', existing_id, properties)
        else:
            success, result = self._create_record('Contact', properties)

        if success:
            self._log_sync('sync', f"Synced contact {contact.email}", records_processed=1)
            self.integration.record_sync(success=True)
        else:
            self._log_error('sync', f"Failed to sync contact {contact.email}: {result}")
            self.integration.record_sync(success=False, error_message=str(result))

        return success, result

    def sync_contacts(self, contacts):
        """
        Sync multiple contacts to Salesforce.

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
            if self.salesforce_config.sync_only_hot_leads:
                if contact.score < self.salesforce_config.min_score_to_sync:
                    results['skipped'] += 1
                    continue

            success, result = self.sync_contact(contact)

            if success:
                if 'created' in str(result).lower() or result and len(result) == 18:
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

    def _map_contact_to_salesforce(self, contact, is_lead=True):
        """Map ColdMail contact fields to Salesforce fields."""
        mapping = self.salesforce_config.field_mapping

        if not mapping:
            mapping = self.DEFAULT_LEAD_MAPPING if is_lead else self.DEFAULT_CONTACT_MAPPING

        properties = {}

        for coldmail_field, sf_field in mapping.items():
            value = getattr(contact, coldmail_field, None)
            if value is not None:
                properties[sf_field] = str(value)

        return properties

    def _find_lead_by_email(self, email):
        """Find a Salesforce Lead by email."""
        query = f"SELECT Id FROM Lead WHERE Email = '{email}' LIMIT 1"
        return self._query_record(query)

    def _find_contact_by_email(self, email):
        """Find a Salesforce Contact by email."""
        query = f"SELECT Id FROM Contact WHERE Email = '{email}' LIMIT 1"
        return self._query_record(query)

    def _query_record(self, query):
        """Execute a SOQL query."""
        url = self._get_api_url('query')

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params={'q': query},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('totalSize', 0) > 0:
                    return data['records'][0]['Id']
            return None

        except requests.RequestException:
            return None

    def _create_record(self, sobject, properties):
        """Create a new record in Salesforce."""
        url = self._get_api_url(f'sobjects/{sobject}')

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=properties,
                timeout=10
            )

            if response.status_code == 201:
                data = response.json()
                return True, data.get('id')
            else:
                errors = response.json()
                error_msg = errors[0].get('message') if isinstance(errors, list) else str(errors)
                return False, error_msg

        except requests.RequestException as e:
            return False, str(e)

    def _update_record(self, sobject, record_id, properties):
        """Update an existing record in Salesforce."""
        url = self._get_api_url(f'sobjects/{sobject}/{record_id}')

        try:
            response = requests.patch(
                url,
                headers=self._get_headers(),
                json=properties,
                timeout=10
            )

            if response.status_code == 204:
                return True, record_id
            else:
                errors = response.json()
                error_msg = errors[0].get('message') if isinstance(errors, list) else str(errors)
                return False, error_msg

        except requests.RequestException as e:
            return False, str(e)

    def test_connection(self):
        """Test the Salesforce connection."""
        if not self._refresh_token_if_needed():
            return False, "Token refresh failed"

        url = self._get_api_url('sobjects')

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
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


def get_salesforce_oauth_url(workspace, redirect_uri):
    """Generate Salesforce OAuth authorization URL."""
    client_id = settings.SALESFORCE_CLIENT_ID
    # Full access scope
    scope = 'api refresh_token'

    state = f"{workspace.id}"

    url = (
        f"https://login.salesforce.com/services/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&state={state}"
    )

    return url


def exchange_salesforce_code(code, redirect_uri):
    """Exchange OAuth code for access token."""
    url = 'https://login.salesforce.com/services/oauth2/token'

    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.SALESFORCE_CLIENT_ID,
        'client_secret': settings.SALESFORCE_CLIENT_SECRET,
        'code': code,
        'redirect_uri': redirect_uri,
    }

    response = requests.post(url, data=data, timeout=10)
    result = response.json()

    if 'access_token' in result:
        return {
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'instance_url': result['instance_url'],
            'id': result.get('id'),
        }
    else:
        raise Exception(result.get('error_description', 'OAuth exchange failed'))
