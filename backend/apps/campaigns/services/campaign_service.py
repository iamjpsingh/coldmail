import random
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from dataclasses import dataclass
import pytz

from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from apps.campaigns.models import (
    Campaign, CampaignRecipient, CampaignEvent, CampaignLog,
    ABTestVariant, EmailTemplate
)
from apps.campaigns.services.template_engine import TemplateEngine
from apps.contacts.models import Contact, ContactActivity
from apps.email_accounts.models import EmailAccount
from apps.email_accounts.services.email_service import EmailService


@dataclass
class PrepareResult:
    """Result of preparing campaign recipients."""
    success: bool
    message: str
    total_recipients: int = 0
    skipped_count: int = 0
    errors: list = None


@dataclass
class SendResult:
    """Result of sending a single email."""
    success: bool
    message: str
    message_id: Optional[str] = None
    recipient_id: Optional[str] = None


class CampaignService:
    """Service for managing campaign operations."""

    def __init__(self, campaign: Campaign):
        self.campaign = campaign
        self.template_engine = TemplateEngine()

    def prepare_recipients(self) -> PrepareResult:
        """
        Prepare recipients for a campaign by collecting contacts
        from lists and tags, excluding specified contacts.
        """
        try:
            # Get contacts from selected lists
            contacts = Contact.objects.none()

            for contact_list in self.campaign.contact_lists.all():
                contacts = contacts | contact_list.get_contacts()

            # Get contacts from selected tags
            for tag in self.campaign.contact_tags.all():
                contacts = contacts | tag.contacts.filter(
                    workspace=self.campaign.workspace,
                    status=Contact.Status.ACTIVE
                )

            # If no lists or tags selected, use all active contacts
            if not self.campaign.contact_lists.exists() and not self.campaign.contact_tags.exists():
                contacts = Contact.objects.filter(
                    workspace=self.campaign.workspace,
                    status=Contact.Status.ACTIVE
                )

            # Exclude contacts from excluded lists
            for exclude_list in self.campaign.exclude_lists.all():
                exclude_contacts = exclude_list.get_contacts()
                contacts = contacts.exclude(pk__in=exclude_contacts.values_list('pk', flat=True))

            # Exclude contacts with excluded tags
            for exclude_tag in self.campaign.exclude_tags.all():
                contacts = contacts.exclude(tags=exclude_tag)

            # Exclude already added recipients
            existing_contact_ids = self.campaign.recipients.values_list('contact_id', flat=True)
            contacts = contacts.exclude(pk__in=existing_contact_ids)

            # Get unique contacts
            contacts = contacts.distinct()

            # Create recipients
            recipients_to_create = []
            skipped_count = 0

            for contact in contacts:
                # Skip if contact has unsubscribed or bounced
                if contact.status != Contact.Status.ACTIVE:
                    skipped_count += 1
                    continue

                # Render personalized content
                context = self._build_contact_context(contact)
                render_result = self.template_engine.render(
                    subject=self.campaign.subject,
                    content_html=self.campaign.content_html,
                    content_text=self.campaign.content_text or '',
                    context=context,
                    process_spintax=True
                )

                recipient = CampaignRecipient(
                    campaign=self.campaign,
                    contact=contact,
                    status=CampaignRecipient.Status.PENDING,
                    rendered_subject=render_result.subject,
                    rendered_html=render_result.content_html,
                    rendered_text=render_result.content_text,
                )
                recipients_to_create.append(recipient)

            # Bulk create recipients
            with transaction.atomic():
                CampaignRecipient.objects.bulk_create(recipients_to_create, batch_size=1000)

                # Update campaign total
                total_recipients = self.campaign.recipients.count()
                self.campaign.total_recipients = total_recipients
                self.campaign.save(update_fields=['total_recipients'])

                # Log the action
                self._log(
                    CampaignLog.LogType.RECIPIENTS_ADDED,
                    f"Added {len(recipients_to_create)} recipients",
                    details={
                        'added': len(recipients_to_create),
                        'skipped': skipped_count,
                        'total': total_recipients
                    }
                )

            return PrepareResult(
                success=True,
                message=f"Successfully prepared {len(recipients_to_create)} recipients",
                total_recipients=len(recipients_to_create),
                skipped_count=skipped_count
            )

        except Exception as e:
            return PrepareResult(
                success=False,
                message=f"Failed to prepare recipients: {str(e)}",
                errors=[str(e)]
            )

    def assign_ab_variants(self):
        """Assign A/B test variants to recipients."""
        if not self.campaign.is_ab_test:
            return

        variants = list(self.campaign.ab_variants.all())
        if not variants:
            return

        recipients = self.campaign.recipients.filter(
            status=CampaignRecipient.Status.PENDING,
            ab_variant__isnull=True
        )

        for recipient in recipients:
            # Randomly assign a variant
            variant = random.choice(variants)
            recipient.ab_variant = variant

            # Re-render content with variant's subject/content
            context = self._build_contact_context(recipient.contact)
            render_result = self.template_engine.render(
                subject=variant.subject,
                content_html=variant.content_html,
                content_text=variant.content_text or '',
                context=context,
                process_spintax=True
            )

            recipient.rendered_subject = render_result.subject
            recipient.rendered_html = render_result.content_html
            recipient.rendered_text = render_result.content_text
            recipient.save()

    def schedule_recipients(self):
        """
        Schedule recipients based on campaign settings.
        Handles immediate, scheduled, and spread sending modes.
        """
        recipients = self.campaign.recipients.filter(
            status=CampaignRecipient.Status.PENDING
        ).order_by('created_at')

        if not recipients.exists():
            return

        now = timezone.now()
        campaign_tz = pytz.timezone(self.campaign.timezone)

        if self.campaign.sending_mode == Campaign.SendingMode.IMMEDIATE:
            # Schedule all immediately with random delays
            self._schedule_with_delays(recipients, now)

        elif self.campaign.sending_mode == Campaign.SendingMode.SCHEDULED:
            # Schedule all starting at scheduled time
            start_time = self.campaign.scheduled_at or now
            self._schedule_with_delays(recipients, start_time)

        elif self.campaign.sending_mode == Campaign.SendingMode.SPREAD:
            # Spread across time window
            self._schedule_spread(recipients, campaign_tz)

        # Mark as queued
        recipients.update(status=CampaignRecipient.Status.QUEUED)

    def _schedule_with_delays(self, recipients, start_time: datetime):
        """Schedule recipients with random delays between them."""
        current_time = start_time
        batch_count = 0

        for recipient in recipients:
            recipient.scheduled_at = current_time
            recipient.send_after = current_time
            recipient.queued_at = timezone.now()
            recipient.save(update_fields=['scheduled_at', 'send_after', 'queued_at'])

            # Add random delay
            delay = random.randint(
                self.campaign.min_delay_seconds,
                self.campaign.max_delay_seconds
            )
            current_time += timedelta(seconds=delay)

            batch_count += 1

            # Add batch delay after batch_size emails
            if batch_count >= self.campaign.batch_size:
                current_time += timedelta(minutes=self.campaign.batch_delay_minutes)
                batch_count = 0

    def _schedule_spread(self, recipients, campaign_tz):
        """Spread recipients across time window and days."""
        if not self.campaign.spread_start_time or not self.campaign.spread_end_time:
            # Fall back to immediate scheduling
            self._schedule_with_delays(recipients, timezone.now())
            return

        spread_days = self.campaign.spread_days or [0, 1, 2, 3, 4]  # Default Mon-Fri

        # Calculate total sending slots
        start_hour = self.campaign.spread_start_time.hour
        start_minute = self.campaign.spread_start_time.minute
        end_hour = self.campaign.spread_end_time.hour
        end_minute = self.campaign.spread_end_time.minute

        # Minutes in window per day
        daily_window_minutes = (end_hour * 60 + end_minute) - (start_hour * 60 + start_minute)
        if daily_window_minutes <= 0:
            daily_window_minutes = 24 * 60 + daily_window_minutes  # Handle overnight windows

        recipients_list = list(recipients)
        total_recipients = len(recipients_list)

        if total_recipients == 0:
            return

        # Find the next valid sending day/time
        now = timezone.now().astimezone(campaign_tz)
        current_date = now.date()
        current_time_slot = now

        # Distribute recipients
        recipient_index = 0
        while recipient_index < total_recipients:
            # Find next valid day
            while current_date.weekday() not in spread_days:
                current_date += timedelta(days=1)

            # Calculate time slot for this day
            day_start = campaign_tz.localize(
                datetime.combine(current_date, self.campaign.spread_start_time)
            )
            day_end = campaign_tz.localize(
                datetime.combine(current_date, self.campaign.spread_end_time)
            )

            # If same day, adjust start time
            if current_date == now.date() and now > day_start:
                day_start = now

            # Skip if past end time
            if now > day_end:
                current_date += timedelta(days=1)
                continue

            # Calculate how many recipients can be sent today
            remaining_minutes = (day_end - day_start).total_seconds() / 60
            avg_delay_minutes = (
                self.campaign.min_delay_seconds + self.campaign.max_delay_seconds
            ) / 2 / 60

            recipients_today = min(
                int(remaining_minutes / avg_delay_minutes),
                total_recipients - recipient_index
            )

            # Schedule recipients for today
            current_time = day_start
            for _ in range(recipients_today):
                if recipient_index >= total_recipients:
                    break

                recipient = recipients_list[recipient_index]
                recipient.scheduled_at = current_time
                recipient.send_after = current_time
                recipient.queued_at = timezone.now()
                recipient.save(update_fields=['scheduled_at', 'send_after', 'queued_at'])

                # Add random delay
                delay = random.randint(
                    self.campaign.min_delay_seconds,
                    self.campaign.max_delay_seconds
                )
                current_time += timedelta(seconds=delay)
                recipient_index += 1

            # Move to next day
            current_date += timedelta(days=1)

    def start_sending(self):
        """Start the campaign sending process."""
        if self.campaign.status not in [Campaign.Status.DRAFT, Campaign.Status.SCHEDULED]:
            return False, "Campaign cannot be started in current status"

        with transaction.atomic():
            self.campaign.status = Campaign.Status.SENDING
            self.campaign.started_at = timezone.now()
            self.campaign.save(update_fields=['status', 'started_at'])

            self._log(
                CampaignLog.LogType.STARTED,
                "Campaign sending started"
            )

        return True, "Campaign started"

    def pause_sending(self):
        """Pause the campaign sending."""
        if self.campaign.status != Campaign.Status.SENDING:
            return False, "Campaign is not currently sending"

        with transaction.atomic():
            self.campaign.status = Campaign.Status.PAUSED
            self.campaign.paused_at = timezone.now()
            self.campaign.save(update_fields=['status', 'paused_at'])

            self._log(
                CampaignLog.LogType.PAUSED,
                "Campaign sending paused"
            )

        return True, "Campaign paused"

    def resume_sending(self):
        """Resume paused campaign."""
        if self.campaign.status != Campaign.Status.PAUSED:
            return False, "Campaign is not paused"

        with transaction.atomic():
            self.campaign.status = Campaign.Status.SENDING
            self.campaign.save(update_fields=['status'])

            self._log(
                CampaignLog.LogType.RESUMED,
                "Campaign sending resumed"
            )

        return True, "Campaign resumed"

    def cancel_campaign(self):
        """Cancel the campaign."""
        if self.campaign.status == Campaign.Status.COMPLETED:
            return False, "Campaign is already completed"

        with transaction.atomic():
            self.campaign.status = Campaign.Status.CANCELLED
            self.campaign.save(update_fields=['status'])

            # Mark pending/queued recipients as skipped
            self.campaign.recipients.filter(
                status__in=[
                    CampaignRecipient.Status.PENDING,
                    CampaignRecipient.Status.QUEUED
                ]
            ).update(
                status=CampaignRecipient.Status.SKIPPED,
                status_reason="Campaign cancelled"
            )

            self._log(
                CampaignLog.LogType.CANCELLED,
                "Campaign cancelled"
            )

        return True, "Campaign cancelled"

    def send_to_recipient(self, recipient: CampaignRecipient) -> SendResult:
        """Send email to a single recipient."""
        if recipient.status not in [
            CampaignRecipient.Status.QUEUED,
            CampaignRecipient.Status.PENDING
        ]:
            return SendResult(
                success=False,
                message=f"Recipient not in sendable status: {recipient.status}",
                recipient_id=str(recipient.id)
            )

        # Get email account
        email_account = self.campaign.email_account
        if not email_account:
            return SendResult(
                success=False,
                message="No email account configured for campaign",
                recipient_id=str(recipient.id)
            )

        # Check if account can send
        if not email_account.can_send:
            return SendResult(
                success=False,
                message="Email account cannot send (limit reached or inactive)",
                recipient_id=str(recipient.id)
            )

        try:
            # Update status to sending
            recipient.status = CampaignRecipient.Status.SENDING
            recipient.email_account = email_account
            recipient.save(update_fields=['status', 'email_account'])

            # Send email
            email_service = EmailService(email_account)
            from_name = self.campaign.from_name or email_account.from_name
            reply_to = self.campaign.reply_to or email_account.reply_to

            result = email_service.send_email(
                to_email=recipient.contact.email,
                subject=recipient.rendered_subject,
                html_body=recipient.rendered_html,
                text_body=recipient.rendered_text or None,
                reply_to=reply_to,
                headers={
                    'X-Campaign-ID': str(self.campaign.id),
                    'X-Recipient-ID': str(recipient.id),
                }
            )

            if result.success:
                # Update recipient
                recipient.status = CampaignRecipient.Status.SENT
                recipient.sent_at = timezone.now()
                recipient.message_id = result.message_id or ''
                recipient.save(update_fields=['status', 'sent_at', 'message_id'])

                # Update campaign stats
                self.campaign.sent_count += 1
                self.campaign.save(update_fields=['sent_count'])

                # Update contact
                contact = recipient.contact
                contact.emails_sent += 1
                contact.last_emailed_at = timezone.now()
                contact.save(update_fields=['emails_sent', 'last_emailed_at'])

                # Create activity
                ContactActivity.objects.create(
                    contact=contact,
                    activity_type=ContactActivity.ActivityType.EMAIL_SENT,
                    description=f"Campaign: {self.campaign.name}",
                    campaign_id=self.campaign.id,
                    metadata={'subject': recipient.rendered_subject}
                )

                # Create event
                CampaignEvent.objects.create(
                    recipient=recipient,
                    event_type=CampaignEvent.EventType.SENT
                )

                # Update A/B variant stats if applicable
                if recipient.ab_variant:
                    recipient.ab_variant.sent_count += 1
                    recipient.ab_variant.save(update_fields=['sent_count'])

                return SendResult(
                    success=True,
                    message="Email sent successfully",
                    message_id=result.message_id,
                    recipient_id=str(recipient.id)
                )
            else:
                # Handle failure
                recipient.status = CampaignRecipient.Status.FAILED
                recipient.last_error = result.message
                recipient.retry_count += 1
                recipient.save(update_fields=['status', 'last_error', 'retry_count'])

                # Update campaign stats
                self.campaign.failed_count += 1
                self.campaign.save(update_fields=['failed_count'])

                # Create event
                CampaignEvent.objects.create(
                    recipient=recipient,
                    event_type=CampaignEvent.EventType.FAILED,
                    metadata={'error': result.message}
                )

                return SendResult(
                    success=False,
                    message=result.message,
                    recipient_id=str(recipient.id)
                )

        except Exception as e:
            recipient.status = CampaignRecipient.Status.FAILED
            recipient.last_error = str(e)
            recipient.retry_count += 1
            recipient.save(update_fields=['status', 'last_error', 'retry_count'])

            self.campaign.failed_count += 1
            self.campaign.save(update_fields=['failed_count'])

            return SendResult(
                success=False,
                message=str(e),
                recipient_id=str(recipient.id)
            )

    def get_next_recipients(self, limit: int = 10) -> List[CampaignRecipient]:
        """Get the next batch of recipients to send."""
        now = timezone.now()

        return list(
            self.campaign.recipients.filter(
                status=CampaignRecipient.Status.QUEUED,
                send_after__lte=now
            ).select_related('contact', 'ab_variant').order_by('scheduled_at')[:limit]
        )

    def check_completion(self):
        """Check if campaign is complete and update status."""
        pending_count = self.campaign.recipients.filter(
            status__in=[
                CampaignRecipient.Status.PENDING,
                CampaignRecipient.Status.QUEUED,
                CampaignRecipient.Status.SENDING
            ]
        ).count()

        if pending_count == 0 and self.campaign.status == Campaign.Status.SENDING:
            self.campaign.status = Campaign.Status.COMPLETED
            self.campaign.completed_at = timezone.now()
            self.campaign.save(update_fields=['status', 'completed_at'])

            self._log(
                CampaignLog.LogType.COMPLETED,
                "Campaign sending completed",
                details={
                    'sent': self.campaign.sent_count,
                    'failed': self.campaign.failed_count,
                    'bounced': self.campaign.bounced_count
                }
            )

    def select_ab_winner(self):
        """Select the winning A/B test variant."""
        if not self.campaign.is_ab_test:
            return None

        variants = self.campaign.ab_variants.all()
        if not variants:
            return None

        criteria = self.campaign.ab_test_winner_criteria or 'open_rate'

        best_variant = None
        best_score = -1

        for variant in variants:
            if criteria == 'open_rate':
                score = variant.open_rate
            elif criteria == 'click_rate':
                score = variant.click_rate
            else:
                score = variant.open_rate

            if score > best_score:
                best_score = score
                best_variant = variant

        if best_variant:
            # Mark as winner
            variants.update(is_winner=False)
            best_variant.is_winner = True
            best_variant.save(update_fields=['is_winner'])

            self._log(
                CampaignLog.LogType.AB_WINNER,
                f"A/B test winner selected: {best_variant.name}",
                details={
                    'variant': best_variant.name,
                    'criteria': criteria,
                    'score': best_score
                }
            )

        return best_variant

    def get_stats(self) -> dict:
        """Get campaign statistics."""
        return {
            'total_recipients': self.campaign.total_recipients,
            'sent': self.campaign.sent_count,
            'delivered': self.campaign.delivered_count,
            'opened': self.campaign.opened_count,
            'unique_opens': self.campaign.unique_opens,
            'clicked': self.campaign.clicked_count,
            'unique_clicks': self.campaign.unique_clicks,
            'replied': self.campaign.replied_count,
            'bounced': self.campaign.bounced_count,
            'unsubscribed': self.campaign.unsubscribed_count,
            'complained': self.campaign.complained_count,
            'failed': self.campaign.failed_count,
            'open_rate': self.campaign.open_rate,
            'click_rate': self.campaign.click_rate,
            'reply_rate': self.campaign.reply_rate,
            'bounce_rate': self.campaign.bounce_rate,
            'progress': self.campaign.progress_percentage,
        }

    def _build_contact_context(self, contact: Contact) -> dict:
        """Build context dictionary for template rendering."""
        context = {
            'email': contact.email,
            'firstName': contact.first_name,
            'first_name': contact.first_name,
            'lastName': contact.last_name,
            'last_name': contact.last_name,
            'fullName': contact.full_name,
            'full_name': contact.full_name,
            'company': contact.company,
            'jobTitle': contact.job_title,
            'job_title': contact.job_title,
            'phone': contact.phone,
            'website': contact.website,
            'city': contact.city,
            'state': contact.state,
            'country': contact.country,
        }

        # Add custom fields
        if contact.custom_fields:
            for key, value in contact.custom_fields.items():
                context[key] = value

        return context

    def _log(self, log_type: str, message: str, details: dict = None):
        """Create a campaign log entry."""
        CampaignLog.objects.create(
            campaign=self.campaign,
            log_type=log_type,
            message=message,
            details=details or {},
            created_by=self.campaign.created_by
        )
