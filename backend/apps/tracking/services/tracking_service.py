import re
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from apps.tracking.models import (
    TrackingLink,
    TrackingPixel,
    TrackingEvent,
    UnsubscribeToken,
    TrackingDomain,
    BounceRecord,
    ComplaintRecord,
    SuppressionList,
)

logger = logging.getLogger(__name__)

# Known bot user agents patterns
BOT_PATTERNS = [
    r'googlebot',
    r'bingbot',
    r'slurp',
    r'duckduckbot',
    r'baiduspider',
    r'yandexbot',
    r'facebookexternalhit',
    r'facebot',
    r'twitterbot',
    r'linkedinbot',
    r'whatsapp',
    r'telegrambot',
    r'applebot',
    r'petalbot',
    r'semrushbot',
    r'ahrefsbot',
    r'dotbot',
    r'rogerbot',
    r'embedly',
    r'quora link preview',
    r'outbrain',
    r'pinterest',
    r'slackbot',
    r'vkshare',
    r'w3c_validator',
    r'validator',
    r'feedfetcher',
    r'mediapartners-google',
    r'adsbot-google',
    r'googleweblight',
    r'chrome-lighthouse',
    r'headlesschrome',
    r'phantomjs',
    r'prerender',
    r'screaming frog',
    r'yahoo! slurp',
    r'ia_archiver',
    r'wget',
    r'curl',
    r'python-requests',
    r'python-urllib',
    r'go-http-client',
    r'java/',
    r'apache-httpclient',
    r'okhttp',
    r'feedlybot',
    r'feedly',
    r'tiny tiny rss',
    r'newsblur',
    r'the old reader',
    r'inoreader',
    r'bazqux',
    r'google favicon',
    r'microsoft office',
    r'outlook',
    r'safelinks',
    r'barracuda',
    r'proofpoint',
    r'mimecast',
    r'zscaler',
    r'websense',
    r'fortiguard',
    r'bluecoat',
    r'forcepoint',
    r'sophos',
    r'symantec',
    r'kaspersky',
    r'avira',
    r'norton',
    r'mcafee',
    r'bitdefender',
    r'eset',
    r'avg',
    r'malwarebytes',
    r'spamhaus',
]

# Compiled bot patterns for efficiency
BOT_REGEX = re.compile('|'.join(BOT_PATTERNS), re.IGNORECASE)


class TrackingService:
    """Service for email tracking operations."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize tracking service.

        Args:
            base_url: Base URL for tracking endpoints (defaults to settings)
        """
        self.base_url = base_url or getattr(
            settings, 'TRACKING_BASE_URL',
            getattr(settings, 'BASE_URL', 'http://localhost:8000')
        )

    # ==================== Pixel/Link Generation ====================

    def get_or_create_tracking_pixel(self, campaign_recipient) -> TrackingPixel:
        """Get or create a tracking pixel for a campaign recipient.

        Args:
            campaign_recipient: CampaignRecipient instance

        Returns:
            TrackingPixel instance
        """
        pixel, created = TrackingPixel.objects.get_or_create(
            campaign_recipient=campaign_recipient
        )
        if created:
            logger.debug(f"Created tracking pixel {pixel.token[:8]} for recipient {campaign_recipient.id}")
        return pixel

    def get_pixel_url(self, pixel: TrackingPixel, tracking_domain: Optional[TrackingDomain] = None) -> str:
        """Generate the pixel URL for embedding in emails.

        Args:
            pixel: TrackingPixel instance
            tracking_domain: Optional custom tracking domain

        Returns:
            URL string for the tracking pixel
        """
        base = self._get_tracking_base_url(tracking_domain)
        return urljoin(base, f'/t/o/{pixel.token}.gif')

    def create_tracking_link(self, campaign_recipient, original_url: str) -> TrackingLink:
        """Create a tracking link for URL click tracking.

        Args:
            campaign_recipient: CampaignRecipient instance
            original_url: Original URL to track

        Returns:
            TrackingLink instance
        """
        # Check if we already have a tracking link for this URL and recipient
        existing = TrackingLink.objects.filter(
            campaign_recipient=campaign_recipient,
            original_url=original_url
        ).first()

        if existing:
            return existing

        link = TrackingLink.objects.create(
            campaign_recipient=campaign_recipient,
            original_url=original_url
        )
        logger.debug(f"Created tracking link {link.token[:8]} for URL: {original_url[:50]}")
        return link

    def get_tracking_link_url(
        self,
        link: TrackingLink,
        tracking_domain: Optional[TrackingDomain] = None
    ) -> str:
        """Generate the tracking URL for a link.

        Args:
            link: TrackingLink instance
            tracking_domain: Optional custom tracking domain

        Returns:
            URL string for the tracked link
        """
        base = self._get_tracking_base_url(tracking_domain)
        return urljoin(base, f'/t/c/{link.token}')

    def get_or_create_unsubscribe_token(self, contact, campaign=None) -> UnsubscribeToken:
        """Get or create an unsubscribe token for a contact.

        Args:
            contact: Contact instance
            campaign: Optional Campaign instance

        Returns:
            UnsubscribeToken instance
        """
        # Try to find existing unused token
        existing = UnsubscribeToken.objects.filter(
            contact=contact,
            campaign=campaign,
            is_used=False
        ).first()

        if existing:
            return existing

        token = UnsubscribeToken.objects.create(
            contact=contact,
            campaign=campaign
        )
        logger.debug(f"Created unsubscribe token {token.token[:8]} for contact {contact.email}")
        return token

    def get_unsubscribe_url(
        self,
        token: UnsubscribeToken,
        tracking_domain: Optional[TrackingDomain] = None
    ) -> str:
        """Generate the unsubscribe URL.

        Args:
            token: UnsubscribeToken instance
            tracking_domain: Optional custom tracking domain

        Returns:
            URL string for unsubscribe
        """
        base = self._get_tracking_base_url(tracking_domain)
        return urljoin(base, f'/t/u/{token.token}')

    # ==================== Email Content Processing ====================

    def process_email_content(
        self,
        html_content: str,
        campaign_recipient,
        tracking_domain: Optional[TrackingDomain] = None,
        track_opens: bool = True,
        track_clicks: bool = True,
        add_unsubscribe: bool = True
    ) -> str:
        """Process email HTML content to add tracking.

        Args:
            html_content: Original HTML content
            campaign_recipient: CampaignRecipient instance
            tracking_domain: Optional custom tracking domain
            track_opens: Whether to add open tracking pixel
            track_clicks: Whether to track link clicks
            add_unsubscribe: Whether to add unsubscribe link

        Returns:
            Processed HTML content with tracking
        """
        processed = html_content

        # Track clicks - replace URLs with tracking URLs
        if track_clicks:
            processed = self._rewrite_links(processed, campaign_recipient, tracking_domain)

        # Add tracking pixel for open tracking
        if track_opens:
            processed = self._inject_tracking_pixel(processed, campaign_recipient, tracking_domain)

        # Add unsubscribe link if requested
        if add_unsubscribe:
            processed = self._add_unsubscribe_link(processed, campaign_recipient, tracking_domain)

        return processed

    def _rewrite_links(
        self,
        html_content: str,
        campaign_recipient,
        tracking_domain: Optional[TrackingDomain] = None
    ) -> str:
        """Rewrite links in HTML to use tracking URLs.

        Args:
            html_content: HTML content
            campaign_recipient: CampaignRecipient instance
            tracking_domain: Optional custom tracking domain

        Returns:
            HTML with rewritten links
        """
        # Pattern to match href attributes
        href_pattern = re.compile(
            r'(<a\s+[^>]*href\s*=\s*["\'])([^"\']+)(["\'][^>]*>)',
            re.IGNORECASE
        )

        def replace_link(match):
            prefix = match.group(1)
            url = match.group(2)
            suffix = match.group(3)

            # Skip certain URLs
            if self._should_skip_url(url):
                return match.group(0)

            # Create tracking link and get URL
            tracking_link = self.create_tracking_link(campaign_recipient, url)
            tracking_url = self.get_tracking_link_url(tracking_link, tracking_domain)

            return f'{prefix}{tracking_url}{suffix}'

        return href_pattern.sub(replace_link, html_content)

    def _should_skip_url(self, url: str) -> bool:
        """Check if a URL should be skipped for tracking.

        Args:
            url: URL to check

        Returns:
            True if URL should be skipped
        """
        url_lower = url.lower()

        # Skip mailto links
        if url_lower.startswith('mailto:'):
            return True

        # Skip tel links
        if url_lower.startswith('tel:'):
            return True

        # Skip anchors
        if url_lower.startswith('#'):
            return True

        # Skip javascript
        if url_lower.startswith('javascript:'):
            return True

        # Skip unsubscribe links (already tracked separately)
        if 'unsubscribe' in url_lower:
            return True

        return False

    def _inject_tracking_pixel(
        self,
        html_content: str,
        campaign_recipient,
        tracking_domain: Optional[TrackingDomain] = None
    ) -> str:
        """Inject tracking pixel into HTML content.

        Args:
            html_content: HTML content
            campaign_recipient: CampaignRecipient instance
            tracking_domain: Optional custom tracking domain

        Returns:
            HTML with tracking pixel
        """
        pixel = self.get_or_create_tracking_pixel(campaign_recipient)
        pixel_url = self.get_pixel_url(pixel, tracking_domain)

        # Create invisible 1x1 tracking pixel
        pixel_html = (
            f'<img src="{pixel_url}" width="1" height="1" '
            f'alt="" style="display:block;width:1px;height:1px;border:0;" />'
        )

        # Try to inject before </body>
        if '</body>' in html_content.lower():
            # Find the </body> tag (case-insensitive)
            pattern = re.compile(r'(</body>)', re.IGNORECASE)
            return pattern.sub(f'{pixel_html}\\1', html_content)

        # Otherwise append to end
        return html_content + pixel_html

    def _add_unsubscribe_link(
        self,
        html_content: str,
        campaign_recipient,
        tracking_domain: Optional[TrackingDomain] = None
    ) -> str:
        """Add unsubscribe link to HTML content.

        Args:
            html_content: HTML content
            campaign_recipient: CampaignRecipient instance
            tracking_domain: Optional custom tracking domain

        Returns:
            HTML with unsubscribe link
        """
        # Check if {{unsubscribe_url}} placeholder exists
        if '{{unsubscribe_url}}' in html_content:
            token = self.get_or_create_unsubscribe_token(
                campaign_recipient.contact,
                campaign_recipient.campaign
            )
            unsubscribe_url = self.get_unsubscribe_url(token, tracking_domain)
            return html_content.replace('{{unsubscribe_url}}', unsubscribe_url)

        return html_content

    def get_list_unsubscribe_header(
        self,
        campaign_recipient,
        tracking_domain: Optional[TrackingDomain] = None
    ) -> dict:
        """Generate List-Unsubscribe headers for the email.

        Args:
            campaign_recipient: CampaignRecipient instance
            tracking_domain: Optional custom tracking domain

        Returns:
            Dict with List-Unsubscribe and List-Unsubscribe-Post headers
        """
        token = self.get_or_create_unsubscribe_token(
            campaign_recipient.contact,
            campaign_recipient.campaign
        )
        unsubscribe_url = self.get_unsubscribe_url(token, tracking_domain)

        return {
            'List-Unsubscribe': f'<{unsubscribe_url}>',
            'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
        }

    # ==================== Event Processing ====================

    @transaction.atomic
    def record_open(
        self,
        pixel_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[TrackingEvent]:
        """Record an email open event.

        Args:
            pixel_token: Tracking pixel token
            ip_address: Request IP address
            user_agent: Request user agent

        Returns:
            TrackingEvent if recorded, None if bot or invalid
        """
        try:
            pixel = TrackingPixel.objects.select_related(
                'campaign_recipient__campaign',
                'campaign_recipient__contact'
            ).get(token=pixel_token)
        except TrackingPixel.DoesNotExist:
            logger.warning(f"Invalid pixel token: {pixel_token[:8]}")
            return None

        # Parse user agent and check for bots
        device_info = self.parse_user_agent(user_agent)
        is_bot = self.is_bot(user_agent, device_info)

        # Update pixel stats
        now = timezone.now()
        pixel.open_count += 1
        if not pixel.first_opened_at:
            pixel.first_opened_at = now
        pixel.last_opened_at = now
        pixel.save(update_fields=['open_count', 'first_opened_at', 'last_opened_at', 'updated_at'])

        # Get geo info
        geo_info = self.get_geo_info(ip_address)

        # Create tracking event
        event = TrackingEvent.objects.create(
            event_type=TrackingEvent.EventType.OPEN,
            campaign_recipient=pixel.campaign_recipient,
            ip_address=ip_address,
            user_agent=user_agent or '',
            is_bot=is_bot,
            **device_info,
            **geo_info
        )

        # Update campaign recipient
        recipient = pixel.campaign_recipient
        if not recipient.opened_at:
            recipient.opened_at = now
            recipient.open_count = 1
        else:
            recipient.open_count = (recipient.open_count or 0) + 1
        recipient.save(update_fields=['opened_at', 'open_count', 'updated_at'])

        # Award score if not a bot
        if not is_bot:
            self._award_score(recipient.contact, 'email_open', event)

        logger.info(f"Recorded open for pixel {pixel_token[:8]} (bot: {is_bot})")
        return event

    @transaction.atomic
    def record_click(
        self,
        link_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[tuple[TrackingEvent, str]]:
        """Record a link click event.

        Args:
            link_token: Tracking link token
            ip_address: Request IP address
            user_agent: Request user agent

        Returns:
            Tuple of (TrackingEvent, original_url) if recorded, None if invalid
        """
        try:
            link = TrackingLink.objects.select_related(
                'campaign_recipient__campaign',
                'campaign_recipient__contact'
            ).get(token=link_token)
        except TrackingLink.DoesNotExist:
            logger.warning(f"Invalid link token: {link_token[:8]}")
            return None

        # Parse user agent and check for bots
        device_info = self.parse_user_agent(user_agent)
        is_bot = self.is_bot(user_agent, device_info)

        # Update link stats
        now = timezone.now()
        link.click_count += 1
        if not link.first_clicked_at:
            link.first_clicked_at = now
        link.last_clicked_at = now
        link.save(update_fields=['click_count', 'first_clicked_at', 'last_clicked_at', 'updated_at'])

        # Get geo info
        geo_info = self.get_geo_info(ip_address)

        # Create tracking event
        event = TrackingEvent.objects.create(
            event_type=TrackingEvent.EventType.CLICK,
            campaign_recipient=link.campaign_recipient,
            tracking_link=link,
            clicked_url=link.original_url,
            ip_address=ip_address,
            user_agent=user_agent or '',
            is_bot=is_bot,
            **device_info,
            **geo_info
        )

        # Update campaign recipient
        recipient = link.campaign_recipient
        if not recipient.clicked_at:
            recipient.clicked_at = now
            recipient.click_count = 1
        else:
            recipient.click_count = (recipient.click_count or 0) + 1
        recipient.save(update_fields=['clicked_at', 'click_count', 'updated_at'])

        # Award score if not a bot
        if not is_bot:
            self._award_score(recipient.contact, 'link_click', event)

        logger.info(f"Recorded click for link {link_token[:8]} (bot: {is_bot})")
        return event, link.original_url

    @transaction.atomic
    def process_unsubscribe(
        self,
        token: str,
        reason: str = '',
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[UnsubscribeToken]:
        """Process an unsubscribe request.

        Args:
            token: Unsubscribe token
            reason: Optional reason for unsubscribe
            ip_address: Request IP address
            user_agent: Request user agent

        Returns:
            UnsubscribeToken if processed, None if invalid
        """
        try:
            unsub_token = UnsubscribeToken.objects.select_related(
                'contact__workspace',
                'campaign'
            ).get(token=token)
        except UnsubscribeToken.DoesNotExist:
            logger.warning(f"Invalid unsubscribe token: {token[:8]}")
            return None

        if unsub_token.is_used:
            logger.info(f"Unsubscribe token already used: {token[:8]}")
            return unsub_token

        now = timezone.now()

        # Mark token as used
        unsub_token.is_used = True
        unsub_token.used_at = now
        unsub_token.reason = reason
        unsub_token.save(update_fields=['is_used', 'used_at', 'reason', 'updated_at'])

        # Update contact status
        contact = unsub_token.contact
        contact.is_unsubscribed = True
        contact.unsubscribed_at = now
        contact.save(update_fields=['is_unsubscribed', 'unsubscribed_at', 'updated_at'])

        # Add to suppression list
        SuppressionList.objects.get_or_create(
            workspace=contact.workspace,
            email=contact.email,
            defaults={
                'reason': SuppressionList.Reason.UNSUBSCRIBE,
                'source': unsub_token.campaign.name if unsub_token.campaign else 'Manual',
            }
        )

        # Create tracking event if we have a campaign recipient
        if unsub_token.campaign:
            try:
                from apps.campaigns.models import CampaignRecipient
                recipient = CampaignRecipient.objects.get(
                    campaign=unsub_token.campaign,
                    contact=contact
                )

                device_info = self.parse_user_agent(user_agent)
                geo_info = self.get_geo_info(ip_address)

                TrackingEvent.objects.create(
                    event_type=TrackingEvent.EventType.UNSUBSCRIBE,
                    campaign_recipient=recipient,
                    ip_address=ip_address,
                    user_agent=user_agent or '',
                    **device_info,
                    **geo_info
                )

                # Update recipient status
                recipient.status = 'unsubscribed'
                recipient.save(update_fields=['status', 'updated_at'])

            except Exception as e:
                logger.error(f"Error creating unsubscribe event: {e}")

        logger.info(f"Processed unsubscribe for {contact.email}")
        return unsub_token

    # ==================== Bounce/Complaint Processing ====================

    @transaction.atomic
    def process_bounce(
        self,
        email: str,
        workspace_id: str,
        bounce_type: str,
        bounce_code: str = '',
        bounce_message: str = '',
        bounce_category: str = 'other',
        email_account_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        message_id: str = '',
        raw_data: Optional[dict] = None
    ) -> BounceRecord:
        """Process an email bounce.

        Args:
            email: Bounced email address
            workspace_id: Workspace ID
            bounce_type: 'hard' or 'soft'
            bounce_code: SMTP bounce code
            bounce_message: Bounce message
            bounce_category: Category of bounce
            email_account_id: Email account ID
            campaign_id: Campaign ID if available
            message_id: Original message ID
            raw_data: Raw bounce data

        Returns:
            BounceRecord instance
        """
        from apps.workspaces.models import Workspace

        workspace = Workspace.objects.get(id=workspace_id)

        # Create bounce record
        bounce = BounceRecord.objects.create(
            email=email,
            workspace=workspace,
            email_account_id=email_account_id,
            campaign_id=campaign_id,
            bounce_type=bounce_type,
            bounce_category=bounce_category,
            bounce_code=bounce_code,
            bounce_message=bounce_message,
            message_id=message_id,
            raw_data=raw_data or {}
        )

        # For hard bounces, add to suppression list
        if bounce_type == 'hard':
            SuppressionList.objects.get_or_create(
                workspace=workspace,
                email=email,
                defaults={
                    'reason': SuppressionList.Reason.HARD_BOUNCE,
                    'source': f'Bounce: {bounce_message[:100]}' if bounce_message else 'Hard bounce',
                }
            )

            # Update contact if exists
            try:
                from apps.contacts.models import Contact
                contact = Contact.objects.get(workspace=workspace, email=email)
                contact.is_bounced = True
                contact.bounced_at = timezone.now()
                contact.save(update_fields=['is_bounced', 'bounced_at', 'updated_at'])
            except Exception:
                pass

        # Update campaign recipient if we have campaign info
        if campaign_id:
            try:
                from apps.campaigns.models import CampaignRecipient
                recipient = CampaignRecipient.objects.get(
                    campaign_id=campaign_id,
                    contact__email=email
                )
                recipient.status = 'bounced'
                recipient.bounced_at = timezone.now()
                recipient.save(update_fields=['status', 'bounced_at', 'updated_at'])

                # Create tracking event
                TrackingEvent.objects.create(
                    event_type=TrackingEvent.EventType.BOUNCE,
                    campaign_recipient=recipient,
                    bounce_type=bounce_type,
                    bounce_code=bounce_code,
                    bounce_message=bounce_message
                )
            except Exception as e:
                logger.error(f"Error updating campaign recipient for bounce: {e}")

        logger.info(f"Processed {bounce_type} bounce for {email}")
        return bounce

    @transaction.atomic
    def process_complaint(
        self,
        email: str,
        workspace_id: str,
        complaint_type: str = 'spam',
        email_account_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        feedback_id: str = '',
        message_id: str = '',
        raw_data: Optional[dict] = None
    ) -> ComplaintRecord:
        """Process a spam complaint.

        Args:
            email: Complaining email address
            workspace_id: Workspace ID
            complaint_type: Type of complaint
            email_account_id: Email account ID
            campaign_id: Campaign ID if available
            feedback_id: Feedback loop ID
            message_id: Original message ID
            raw_data: Raw complaint data

        Returns:
            ComplaintRecord instance
        """
        from apps.workspaces.models import Workspace

        workspace = Workspace.objects.get(id=workspace_id)

        # Create complaint record
        complaint = ComplaintRecord.objects.create(
            email=email,
            workspace=workspace,
            email_account_id=email_account_id,
            campaign_id=campaign_id,
            complaint_type=complaint_type,
            feedback_id=feedback_id,
            message_id=message_id,
            raw_data=raw_data or {}
        )

        # Add to suppression list
        SuppressionList.objects.get_or_create(
            workspace=workspace,
            email=email,
            defaults={
                'reason': SuppressionList.Reason.COMPLAINT,
                'source': f'Complaint: {complaint_type}',
            }
        )

        # Update contact if exists
        try:
            from apps.contacts.models import Contact
            contact = Contact.objects.get(workspace=workspace, email=email)
            contact.is_unsubscribed = True
            contact.unsubscribed_at = timezone.now()
            contact.save(update_fields=['is_unsubscribed', 'unsubscribed_at', 'updated_at'])
        except Exception:
            pass

        # Update campaign recipient if we have campaign info
        if campaign_id:
            try:
                from apps.campaigns.models import CampaignRecipient
                recipient = CampaignRecipient.objects.get(
                    campaign_id=campaign_id,
                    contact__email=email
                )
                recipient.status = 'complained'
                recipient.save(update_fields=['status', 'updated_at'])

                # Create tracking event
                TrackingEvent.objects.create(
                    event_type=TrackingEvent.EventType.COMPLAINT,
                    campaign_recipient=recipient
                )
            except Exception as e:
                logger.error(f"Error updating campaign recipient for complaint: {e}")

        logger.info(f"Processed complaint for {email}")
        return complaint

    # ==================== Bot Detection ====================

    def is_bot(self, user_agent: Optional[str], device_info: Optional[dict] = None) -> bool:
        """Check if the user agent indicates a bot.

        Args:
            user_agent: User agent string
            device_info: Parsed device info

        Returns:
            True if likely a bot
        """
        if not user_agent:
            return False

        # Check against known bot patterns
        if BOT_REGEX.search(user_agent):
            return True

        # Check for headless browsers
        if device_info:
            browser = device_info.get('browser_name', '').lower()
            if 'headless' in browser:
                return True

        # Additional heuristics
        ua_lower = user_agent.lower()

        # Empty or very short user agents are suspicious
        if len(user_agent) < 10:
            return True

        # Check for common bot indicators
        bot_indicators = ['bot', 'spider', 'crawler', 'scan', 'preview', 'fetch']
        if any(indicator in ua_lower for indicator in bot_indicators):
            return True

        return False

    def get_bot_name(self, user_agent: str) -> str:
        """Extract bot name from user agent.

        Args:
            user_agent: User agent string

        Returns:
            Bot name if detected, empty string otherwise
        """
        ua_lower = user_agent.lower()

        # Common bots mapping
        bot_names = {
            'googlebot': 'Googlebot',
            'bingbot': 'Bingbot',
            'slurp': 'Yahoo Slurp',
            'duckduckbot': 'DuckDuckBot',
            'facebookexternalhit': 'Facebook',
            'twitterbot': 'Twitter',
            'linkedinbot': 'LinkedIn',
            'slackbot': 'Slack',
            'outlook': 'Outlook',
            'safelinks': 'Microsoft SafeLinks',
            'barracuda': 'Barracuda',
            'proofpoint': 'Proofpoint',
            'mimecast': 'Mimecast',
        }

        for pattern, name in bot_names.items():
            if pattern in ua_lower:
                return name

        return ''

    # ==================== Device Detection ====================

    def parse_user_agent(self, user_agent: Optional[str]) -> dict:
        """Parse user agent string for device information.

        Args:
            user_agent: User agent string

        Returns:
            Dict with device info
        """
        if not user_agent:
            return {
                'device_type': '',
                'device_brand': '',
                'device_model': '',
                'browser_name': '',
                'browser_version': '',
                'os_name': '',
                'os_version': '',
                'bot_name': '',
            }

        result = {
            'device_type': self._detect_device_type(user_agent),
            'device_brand': '',
            'device_model': '',
            'browser_name': '',
            'browser_version': '',
            'os_name': '',
            'os_version': '',
            'bot_name': self.get_bot_name(user_agent) if self.is_bot(user_agent) else '',
        }

        # Parse browser
        browser_info = self._parse_browser(user_agent)
        result.update(browser_info)

        # Parse OS
        os_info = self._parse_os(user_agent)
        result.update(os_info)

        # Parse device brand/model for mobile
        if result['device_type'] in ('mobile', 'tablet'):
            device_info = self._parse_device(user_agent)
            result.update(device_info)

        return result

    def _detect_device_type(self, user_agent: str) -> str:
        """Detect device type from user agent.

        Args:
            user_agent: User agent string

        Returns:
            Device type: 'mobile', 'tablet', or 'desktop'
        """
        ua_lower = user_agent.lower()

        # Tablet patterns (check first as some tablets have 'mobile' in UA)
        tablet_patterns = ['ipad', 'tablet', 'kindle', 'silk', 'playbook']
        if any(pattern in ua_lower for pattern in tablet_patterns):
            return 'tablet'

        # Mobile patterns
        mobile_patterns = [
            'mobile', 'android', 'iphone', 'ipod', 'blackberry',
            'windows phone', 'opera mini', 'opera mobi'
        ]
        if any(pattern in ua_lower for pattern in mobile_patterns):
            return 'mobile'

        return 'desktop'

    def _parse_browser(self, user_agent: str) -> dict:
        """Parse browser info from user agent.

        Args:
            user_agent: User agent string

        Returns:
            Dict with browser_name and browser_version
        """
        result = {'browser_name': '', 'browser_version': ''}

        # Browser patterns with version extraction
        patterns = [
            (r'Edg[eA]?/(\d+[\.\d]*)', 'Edge'),
            (r'OPR/(\d+[\.\d]*)', 'Opera'),
            (r'Chrome/(\d+[\.\d]*)', 'Chrome'),
            (r'Safari/(\d+[\.\d]*)', 'Safari'),
            (r'Firefox/(\d+[\.\d]*)', 'Firefox'),
            (r'MSIE\s+(\d+[\.\d]*)', 'Internet Explorer'),
            (r'Trident.*rv:(\d+[\.\d]*)', 'Internet Explorer'),
        ]

        for pattern, name in patterns:
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                result['browser_name'] = name
                result['browser_version'] = match.group(1)
                break

        return result

    def _parse_os(self, user_agent: str) -> dict:
        """Parse OS info from user agent.

        Args:
            user_agent: User agent string

        Returns:
            Dict with os_name and os_version
        """
        result = {'os_name': '', 'os_version': ''}

        # OS patterns with version extraction
        patterns = [
            (r'Windows NT (\d+[\.\d]*)', 'Windows'),
            (r'Mac OS X (\d+[_\.\d]*)', 'macOS'),
            (r'iPhone OS (\d+[_\.\d]*)', 'iOS'),
            (r'iPad.*OS (\d+[_\.\d]*)', 'iPadOS'),
            (r'Android (\d+[\.\d]*)', 'Android'),
            (r'Linux', 'Linux'),
        ]

        for pattern, name in patterns:
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                result['os_name'] = name
                if match.lastindex:
                    result['os_version'] = match.group(1).replace('_', '.')
                break

        return result

    def _parse_device(self, user_agent: str) -> dict:
        """Parse device brand/model from user agent.

        Args:
            user_agent: User agent string

        Returns:
            Dict with device_brand and device_model
        """
        result = {'device_brand': '', 'device_model': ''}

        # iPhone/iPad
        if 'iPhone' in user_agent:
            result['device_brand'] = 'Apple'
            result['device_model'] = 'iPhone'
        elif 'iPad' in user_agent:
            result['device_brand'] = 'Apple'
            result['device_model'] = 'iPad'
        # Samsung
        elif 'Samsung' in user_agent or 'SM-' in user_agent:
            result['device_brand'] = 'Samsung'
            match = re.search(r'(SM-[A-Z0-9]+)', user_agent)
            if match:
                result['device_model'] = match.group(1)
        # Pixel
        elif 'Pixel' in user_agent:
            result['device_brand'] = 'Google'
            match = re.search(r'(Pixel\s*\d*\s*\w*)', user_agent)
            if match:
                result['device_model'] = match.group(1)

        return result

    # ==================== Geo Detection ====================

    def get_geo_info(self, ip_address: Optional[str]) -> dict:
        """Get geographic information from IP address.

        Note: This is a placeholder. In production, you would integrate
        with a geo IP service like MaxMind GeoIP2 or ip-api.com

        Args:
            ip_address: IP address to lookup

        Returns:
            Dict with geo info
        """
        # Return empty geo info for now
        # In production, integrate with a geo IP service
        return {
            'country': '',
            'country_code': '',
            'region': '',
            'city': '',
            'postal_code': '',
            'latitude': None,
            'longitude': None,
            'timezone': '',
        }

    # ==================== Scoring Integration ====================

    def _award_score(self, contact, event_type: str, event: TrackingEvent):
        """Award score to contact based on tracking event.

        Args:
            contact: Contact instance
            event_type: Type of event (email_open, link_click)
            event: TrackingEvent instance
        """
        try:
            from apps.contacts.services.scoring_engine import ScoringEngine
            engine = ScoringEngine(contact.workspace)
            engine.apply_event(contact, event_type, metadata={
                'event_id': str(event.id),
                'campaign_id': str(event.campaign_recipient.campaign_id),
            })
        except Exception as e:
            logger.error(f"Error awarding score for {event_type}: {e}")

    # ==================== Suppression List ====================

    def is_suppressed(self, workspace, email: str) -> bool:
        """Check if an email is on the suppression list.

        Args:
            workspace: Workspace instance
            email: Email address to check

        Returns:
            True if email is suppressed
        """
        return SuppressionList.objects.filter(
            workspace=workspace,
            email__iexact=email
        ).exists()

    def add_to_suppression_list(
        self,
        workspace,
        email: str,
        reason: str,
        source: str = '',
        notes: str = ''
    ) -> SuppressionList:
        """Add an email to the suppression list.

        Args:
            workspace: Workspace instance
            email: Email address to suppress
            reason: Reason for suppression
            source: Source of suppression
            notes: Additional notes

        Returns:
            SuppressionList instance
        """
        suppression, created = SuppressionList.objects.get_or_create(
            workspace=workspace,
            email=email.lower(),
            defaults={
                'reason': reason,
                'source': source,
                'notes': notes,
            }
        )
        return suppression

    def remove_from_suppression_list(self, workspace, email: str) -> bool:
        """Remove an email from the suppression list.

        Args:
            workspace: Workspace instance
            email: Email address to remove

        Returns:
            True if removed, False if not found
        """
        deleted, _ = SuppressionList.objects.filter(
            workspace=workspace,
            email__iexact=email
        ).delete()
        return deleted > 0

    # ==================== Helpers ====================

    def _get_tracking_base_url(self, tracking_domain: Optional[TrackingDomain] = None) -> str:
        """Get the base URL for tracking endpoints.

        Args:
            tracking_domain: Optional custom tracking domain

        Returns:
            Base URL string
        """
        if tracking_domain and tracking_domain.is_verified:
            protocol = 'https' if tracking_domain.ssl_enabled else 'http'
            return f'{protocol}://{tracking_domain.domain}'
        return self.base_url
