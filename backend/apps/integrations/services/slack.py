"""Slack notification service."""
import json
import logging
import requests
from datetime import datetime
from django.utils import timezone
from django.conf import settings

from ..models import Integration, SlackIntegration, IntegrationLog

logger = logging.getLogger(__name__)


class SlackNotificationService:
    """Service for sending Slack notifications."""

    def __init__(self, integration: Integration):
        self.integration = integration
        self.slack_config = integration.slack_config

    @classmethod
    def get_for_workspace(cls, workspace):
        """Get all active Slack integrations for a workspace."""
        integrations = Integration.objects.filter(
            workspace=workspace,
            integration_type=Integration.IntegrationType.SLACK,
            is_active=True,
            status=Integration.Status.CONNECTED,
        ).select_related('slack_config')

        return [cls(integration) for integration in integrations]

    def send_notification(self, message, blocks=None, channel=None):
        """
        Send a notification to Slack.

        Args:
            message: The fallback text message
            blocks: Slack Block Kit blocks for rich formatting
            channel: Override channel (uses default if not specified)

        Returns:
            bool: True if successful
        """
        if not self.integration.access_token:
            logger.error(f"No access token for Slack integration {self.integration.id}")
            return False

        channel_id = channel or self.slack_config.default_channel_id
        if not channel_id:
            logger.error(f"No channel configured for Slack integration {self.integration.id}")
            return False

        url = 'https://slack.com/api/chat.postMessage'
        headers = {
            'Authorization': f'Bearer {self.integration.access_token}',
            'Content-Type': 'application/json',
        }

        payload = {
            'channel': channel_id,
            'text': message,
        }

        if blocks:
            payload['blocks'] = blocks

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            data = response.json()

            if data.get('ok'):
                self._log_success('notification', 'Notification sent successfully')
                self.integration.record_sync(success=True)
                return True
            else:
                error = data.get('error', 'Unknown error')
                self._log_error('notification', f'Slack API error: {error}')
                self.integration.record_sync(success=False, error_message=error)
                return False

        except requests.RequestException as e:
            self._log_error('notification', f'Request failed: {str(e)}')
            self.integration.record_sync(success=False, error_message=str(e))
            return False

    def notify_hot_lead(self, contact):
        """Send notification for a hot lead."""
        if not self.slack_config.notify_on_hot_lead:
            return False

        if contact.score < self.slack_config.hot_lead_threshold:
            return False

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔥 Hot Lead Alert!",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Contact:*\n{contact.full_name or contact.email}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Score:*\n{contact.score} points"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Email:*\n{contact.email}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Company:*\n{contact.company or 'N/A'}"
                    }
                ]
            },
        ]

        if contact.title:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Title:* {contact.title}"
                }
            })

        message = f"🔥 Hot Lead: {contact.full_name or contact.email} (Score: {contact.score})"
        return self.send_notification(message, blocks)

    def notify_email_reply(self, email_log):
        """Send notification for an email reply."""
        if not self.slack_config.notify_on_email_reply:
            return False

        contact_name = email_log.contact.full_name if email_log.contact else email_log.to_email

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📩 Email Reply Received!",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*From:*\n{contact_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Subject:*\n{email_log.subject}"
                    }
                ]
            },
        ]

        if email_log.campaign:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Campaign:* {email_log.campaign.name}"
                }
            })

        message = f"📩 Reply received from {contact_name}"
        return self.send_notification(message, blocks)

    def notify_campaign_complete(self, campaign):
        """Send notification when a campaign completes."""
        if not self.slack_config.notify_on_campaign_complete:
            return False

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Campaign Completed!",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Campaign:* {campaign.name}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Emails Sent:*\n{campaign.emails_sent}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Open Rate:*\n{campaign.open_rate:.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Click Rate:*\n{campaign.click_rate:.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Replies:*\n{campaign.reply_count}"
                    }
                ]
            },
        ]

        message = f"✅ Campaign '{campaign.name}' completed - {campaign.emails_sent} emails sent"
        return self.send_notification(message, blocks)

    def notify_form_submit(self, visitor, form_data):
        """Send notification for a form submission."""
        if not self.slack_config.notify_on_form_submit:
            return False

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📝 Form Submitted!",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Visitor:*\n{visitor.email or visitor.visitor_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Page:*\n{form_data.get('page_url', 'N/A')}"
                    }
                ]
            },
        ]

        # Add form fields if available
        fields_text = []
        for key, value in form_data.items():
            if key not in ['page_url', 'form_id']:
                fields_text.append(f"• *{key}:* {value}")

        if fields_text:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Form Data:*\n" + "\n".join(fields_text[:10])
                }
            })

        message = f"📝 Form submitted by {visitor.email or 'anonymous visitor'}"
        return self.send_notification(message, blocks)

    def notify_new_contact(self, contact):
        """Send notification for a new contact."""
        if not self.slack_config.notify_on_new_contact:
            return False

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "👤 New Contact Added!",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Name:*\n{contact.full_name or 'N/A'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Email:*\n{contact.email}"
                    }
                ]
            },
        ]

        if contact.company:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Company:* {contact.company}"
                }
            })

        message = f"👤 New contact: {contact.full_name or contact.email}"
        return self.send_notification(message, blocks)

    def notify_sequence_complete(self, enrollment):
        """Send notification when a contact completes a sequence."""
        if not self.slack_config.notify_on_sequence_complete:
            return False

        contact = enrollment.contact
        sequence = enrollment.sequence

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🏁 Sequence Completed!",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Contact:*\n{contact.full_name or contact.email}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Sequence:*\n{sequence.name}"
                    }
                ]
            },
        ]

        message = f"🏁 {contact.full_name or contact.email} completed sequence '{sequence.name}'"
        return self.send_notification(message, blocks)

    def test_connection(self):
        """Test the Slack connection."""
        if not self.integration.access_token:
            return False, "No access token configured"

        url = 'https://slack.com/api/auth.test'
        headers = {
            'Authorization': f'Bearer {self.integration.access_token}',
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if data.get('ok'):
                # Update team info
                self.slack_config.team_id = data.get('team_id', '')
                self.slack_config.team_name = data.get('team', '')
                self.slack_config.save()

                self.integration.status = Integration.Status.CONNECTED
                self.integration.save()

                self._log_success('test', 'Connection test successful')
                return True, "Connected successfully"
            else:
                error = data.get('error', 'Unknown error')
                self._log_error('test', f'Connection test failed: {error}')
                return False, error

        except requests.RequestException as e:
            self._log_error('test', f'Connection test failed: {str(e)}')
            return False, str(e)

    def _log_success(self, operation, message):
        """Log a successful operation."""
        IntegrationLog.objects.create(
            integration=self.integration,
            level=IntegrationLog.LogLevel.INFO,
            operation=operation,
            message=message,
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


def get_slack_oauth_url(workspace, redirect_uri):
    """Generate Slack OAuth authorization URL."""
    client_id = settings.SLACK_CLIENT_ID
    scope = 'chat:write,channels:read,users:read'

    state = f"{workspace.id}"

    url = (
        f"https://slack.com/oauth/v2/authorize"
        f"?client_id={client_id}"
        f"&scope={scope}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )

    return url


def exchange_slack_code(code, redirect_uri):
    """Exchange OAuth code for access token."""
    url = 'https://slack.com/api/oauth.v2.access'

    data = {
        'client_id': settings.SLACK_CLIENT_ID,
        'client_secret': settings.SLACK_CLIENT_SECRET,
        'code': code,
        'redirect_uri': redirect_uri,
    }

    response = requests.post(url, data=data, timeout=10)
    result = response.json()

    if result.get('ok'):
        return {
            'access_token': result.get('access_token'),
            'team_id': result.get('team', {}).get('id'),
            'team_name': result.get('team', {}).get('name'),
        }
    else:
        raise Exception(result.get('error', 'OAuth exchange failed'))
