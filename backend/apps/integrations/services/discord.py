"""Discord notification service."""
import json
import logging
import requests
from datetime import datetime
from django.utils import timezone

from ..models import Integration, DiscordIntegration, IntegrationLog

logger = logging.getLogger(__name__)


class DiscordNotificationService:
    """Service for sending Discord notifications via webhook."""

    # Discord embed colors
    COLOR_SUCCESS = 0x22C55E  # Green
    COLOR_INFO = 0x3B82F6    # Blue
    COLOR_WARNING = 0xF59E0B  # Amber
    COLOR_ERROR = 0xEF4444   # Red
    COLOR_HOT = 0xFF6B35     # Orange/Fire

    def __init__(self, integration: Integration):
        self.integration = integration
        self.discord_config = integration.discord_config

    @classmethod
    def get_for_workspace(cls, workspace):
        """Get all active Discord integrations for a workspace."""
        integrations = Integration.objects.filter(
            workspace=workspace,
            integration_type=Integration.IntegrationType.DISCORD,
            is_active=True,
            status=Integration.Status.CONNECTED,
        ).select_related('discord_config')

        return [cls(integration) for integration in integrations]

    def send_notification(self, content=None, embeds=None):
        """
        Send a notification to Discord via webhook.

        Args:
            content: Plain text message
            embeds: List of Discord embed objects

        Returns:
            bool: True if successful
        """
        webhook_url = self.discord_config.webhook_url
        if not webhook_url:
            logger.error(f"No webhook URL for Discord integration {self.integration.id}")
            return False

        payload = {}

        if content:
            payload['content'] = content

        if embeds:
            payload['embeds'] = embeds

        # Add bot customization
        if self.discord_config.bot_username:
            payload['username'] = self.discord_config.bot_username

        if self.discord_config.bot_avatar_url:
            payload['avatar_url'] = self.discord_config.bot_avatar_url

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )

            # Discord returns 204 on success
            if response.status_code in [200, 204]:
                self._log_success('notification', 'Notification sent successfully')
                self.integration.record_sync(success=True)
                return True
            else:
                error = f"HTTP {response.status_code}: {response.text}"
                self._log_error('notification', f'Discord webhook error: {error}')
                self.integration.record_sync(success=False, error_message=error)
                return False

        except requests.RequestException as e:
            self._log_error('notification', f'Request failed: {str(e)}')
            self.integration.record_sync(success=False, error_message=str(e))
            return False

    def notify_hot_lead(self, contact):
        """Send notification for a hot lead."""
        if not self.discord_config.notify_on_hot_lead:
            return False

        if contact.score < self.discord_config.hot_lead_threshold:
            return False

        embed = {
            "title": "🔥 Hot Lead Alert!",
            "color": self.COLOR_HOT,
            "fields": [
                {
                    "name": "Contact",
                    "value": contact.full_name or contact.email,
                    "inline": True
                },
                {
                    "name": "Score",
                    "value": f"{contact.score} points",
                    "inline": True
                },
                {
                    "name": "Email",
                    "value": contact.email,
                    "inline": False
                },
            ],
            "timestamp": timezone.now().isoformat(),
        }

        if contact.company:
            embed["fields"].append({
                "name": "Company",
                "value": contact.company,
                "inline": True
            })

        if contact.title:
            embed["fields"].append({
                "name": "Title",
                "value": contact.title,
                "inline": True
            })

        return self.send_notification(embeds=[embed])

    def notify_email_reply(self, email_log):
        """Send notification for an email reply."""
        if not self.discord_config.notify_on_email_reply:
            return False

        contact_name = email_log.contact.full_name if email_log.contact else email_log.to_email

        embed = {
            "title": "📩 Email Reply Received!",
            "color": self.COLOR_SUCCESS,
            "fields": [
                {
                    "name": "From",
                    "value": contact_name,
                    "inline": True
                },
                {
                    "name": "Subject",
                    "value": email_log.subject[:100],
                    "inline": True
                },
            ],
            "timestamp": timezone.now().isoformat(),
        }

        if email_log.campaign:
            embed["fields"].append({
                "name": "Campaign",
                "value": email_log.campaign.name,
                "inline": False
            })

        return self.send_notification(embeds=[embed])

    def notify_campaign_complete(self, campaign):
        """Send notification when a campaign completes."""
        if not self.discord_config.notify_on_campaign_complete:
            return False

        embed = {
            "title": "✅ Campaign Completed!",
            "color": self.COLOR_SUCCESS,
            "description": f"**{campaign.name}**",
            "fields": [
                {
                    "name": "Emails Sent",
                    "value": str(campaign.emails_sent),
                    "inline": True
                },
                {
                    "name": "Open Rate",
                    "value": f"{campaign.open_rate:.1f}%",
                    "inline": True
                },
                {
                    "name": "Click Rate",
                    "value": f"{campaign.click_rate:.1f}%",
                    "inline": True
                },
                {
                    "name": "Replies",
                    "value": str(campaign.reply_count),
                    "inline": True
                },
            ],
            "timestamp": timezone.now().isoformat(),
        }

        return self.send_notification(embeds=[embed])

    def notify_form_submit(self, visitor, form_data):
        """Send notification for a form submission."""
        if not self.discord_config.notify_on_form_submit:
            return False

        embed = {
            "title": "📝 Form Submitted!",
            "color": self.COLOR_INFO,
            "fields": [
                {
                    "name": "Visitor",
                    "value": visitor.email or visitor.visitor_id,
                    "inline": True
                },
                {
                    "name": "Page",
                    "value": form_data.get('page_url', 'N/A')[:100],
                    "inline": True
                },
            ],
            "timestamp": timezone.now().isoformat(),
        }

        # Add form fields
        fields_text = []
        for key, value in form_data.items():
            if key not in ['page_url', 'form_id']:
                fields_text.append(f"**{key}:** {value}")

        if fields_text:
            embed["fields"].append({
                "name": "Form Data",
                "value": "\n".join(fields_text[:5]),
                "inline": False
            })

        return self.send_notification(embeds=[embed])

    def notify_new_contact(self, contact):
        """Send notification for a new contact."""
        if not self.discord_config.notify_on_new_contact:
            return False

        embed = {
            "title": "👤 New Contact Added!",
            "color": self.COLOR_INFO,
            "fields": [
                {
                    "name": "Name",
                    "value": contact.full_name or "N/A",
                    "inline": True
                },
                {
                    "name": "Email",
                    "value": contact.email,
                    "inline": True
                },
            ],
            "timestamp": timezone.now().isoformat(),
        }

        if contact.company:
            embed["fields"].append({
                "name": "Company",
                "value": contact.company,
                "inline": True
            })

        return self.send_notification(embeds=[embed])

    def notify_sequence_complete(self, enrollment):
        """Send notification when a contact completes a sequence."""
        if not self.discord_config.notify_on_sequence_complete:
            return False

        contact = enrollment.contact
        sequence = enrollment.sequence

        embed = {
            "title": "🏁 Sequence Completed!",
            "color": self.COLOR_SUCCESS,
            "fields": [
                {
                    "name": "Contact",
                    "value": contact.full_name or contact.email,
                    "inline": True
                },
                {
                    "name": "Sequence",
                    "value": sequence.name,
                    "inline": True
                },
            ],
            "timestamp": timezone.now().isoformat(),
        }

        return self.send_notification(embeds=[embed])

    def test_connection(self):
        """Test the Discord webhook connection."""
        webhook_url = self.discord_config.webhook_url
        if not webhook_url:
            return False, "No webhook URL configured"

        embed = {
            "title": "🔔 ColdMail Connection Test",
            "description": "Your Discord integration is working correctly!",
            "color": self.COLOR_SUCCESS,
            "timestamp": timezone.now().isoformat(),
        }

        payload = {
            'embeds': [embed],
        }

        if self.discord_config.bot_username:
            payload['username'] = self.discord_config.bot_username

        if self.discord_config.bot_avatar_url:
            payload['avatar_url'] = self.discord_config.bot_avatar_url

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code in [200, 204]:
                self.integration.status = Integration.Status.CONNECTED
                self.integration.save()
                self._log_success('test', 'Connection test successful')
                return True, "Connected successfully"
            else:
                error = f"HTTP {response.status_code}: {response.text}"
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
