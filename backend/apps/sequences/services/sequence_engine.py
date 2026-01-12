import random
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from dataclasses import dataclass
import pytz

from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from apps.sequences.models import (
    Sequence, SequenceStep, SequenceEnrollment,
    SequenceStepExecution, SequenceEvent
)
from apps.campaigns.services.template_engine import TemplateEngine
from apps.contacts.models import Contact, ContactActivity, Tag
from apps.email_accounts.models import EmailAccount
from apps.email_accounts.services.email_service import EmailService


logger = logging.getLogger(__name__)


@dataclass
class EnrollResult:
    """Result of enrolling a contact."""
    success: bool
    message: str
    enrollment_id: Optional[str] = None


@dataclass
class StepResult:
    """Result of executing a step."""
    success: bool
    message: str
    message_id: Optional[str] = None
    next_step: Optional[SequenceStep] = None


class SequenceEngine:
    """Engine for managing sequence operations."""

    def __init__(self, sequence: Sequence):
        self.sequence = sequence
        self.template_engine = TemplateEngine()

    def enroll_contact(
        self,
        contact: Contact,
        enrolled_by=None,
        source: str = 'manual'
    ) -> EnrollResult:
        """Enroll a contact in the sequence."""
        # Check if already enrolled
        existing = SequenceEnrollment.objects.filter(
            sequence=self.sequence,
            contact=contact,
            status=SequenceEnrollment.Status.ACTIVE
        ).exists()

        if existing:
            return EnrollResult(
                success=False,
                message="Contact is already enrolled in this sequence"
            )

        # Check if contact is valid
        if contact.status != Contact.Status.ACTIVE:
            return EnrollResult(
                success=False,
                message=f"Contact is not active: {contact.status}"
            )

        # Check if sequence is active
        if self.sequence.status != Sequence.Status.ACTIVE:
            return EnrollResult(
                success=False,
                message=f"Sequence is not active: {self.sequence.status}"
            )

        # Get first step
        first_step = self.sequence.steps.filter(
            is_active=True
        ).order_by('order').first()

        if not first_step:
            return EnrollResult(
                success=False,
                message="Sequence has no active steps"
            )

        try:
            with transaction.atomic():
                # Create enrollment
                enrollment = SequenceEnrollment.objects.create(
                    sequence=self.sequence,
                    contact=contact,
                    status=SequenceEnrollment.Status.ACTIVE,
                    current_step=first_step,
                    current_step_index=0,
                    enrolled_by=enrolled_by,
                    enrollment_source=source,
                    started_at=timezone.now(),
                )

                # Calculate next step time
                next_step_at = self._calculate_next_step_time(first_step)
                enrollment.next_step_at = next_step_at
                enrollment.save(update_fields=['next_step_at'])

                # Create initial step execution
                SequenceStepExecution.objects.create(
                    enrollment=enrollment,
                    step=first_step,
                    status=SequenceStepExecution.Status.SCHEDULED,
                    scheduled_at=next_step_at,
                )

                # Create enrollment event
                SequenceEvent.objects.create(
                    enrollment=enrollment,
                    event_type=SequenceEvent.EventType.ENROLLED,
                    message=f"Contact enrolled in sequence: {self.sequence.name}"
                )

                # Update sequence stats
                self.sequence.total_enrolled += 1
                self.sequence.active_enrolled += 1
                self.sequence.save(update_fields=['total_enrolled', 'active_enrolled'])

                # Create contact activity
                ContactActivity.objects.create(
                    contact=contact,
                    activity_type=ContactActivity.ActivityType.SEQUENCE_STARTED,
                    description=f"Enrolled in sequence: {self.sequence.name}",
                    metadata={'sequence_id': str(self.sequence.id)}
                )

                return EnrollResult(
                    success=True,
                    message="Contact enrolled successfully",
                    enrollment_id=str(enrollment.id)
                )

        except Exception as e:
            logger.exception(f"Error enrolling contact {contact.id} in sequence {self.sequence.id}")
            return EnrollResult(
                success=False,
                message=f"Failed to enroll contact: {str(e)}"
            )

    def bulk_enroll(
        self,
        contacts: List[Contact],
        enrolled_by=None,
        source: str = 'bulk'
    ) -> Tuple[int, int, List[str]]:
        """Enroll multiple contacts. Returns (success_count, failed_count, errors)."""
        success_count = 0
        failed_count = 0
        errors = []

        for contact in contacts:
            result = self.enroll_contact(contact, enrolled_by, source)
            if result.success:
                success_count += 1
            else:
                failed_count += 1
                errors.append(f"{contact.email}: {result.message}")

        return success_count, failed_count, errors

    def process_enrollment(self, enrollment: SequenceEnrollment) -> StepResult:
        """Process the current step for an enrollment."""
        if enrollment.status != SequenceEnrollment.Status.ACTIVE:
            return StepResult(
                success=False,
                message=f"Enrollment is not active: {enrollment.status}"
            )

        step = enrollment.current_step
        if not step:
            # No more steps, complete the enrollment
            enrollment.complete()
            self._update_sequence_stats_on_completion(enrollment)
            return StepResult(
                success=True,
                message="Sequence completed - no more steps"
            )

        # Check stop conditions before processing
        should_stop, stop_reason = self._check_stop_conditions(enrollment)
        if should_stop:
            enrollment.stop(stop_reason)
            self._update_sequence_stats_on_stop(enrollment)
            return StepResult(
                success=True,
                message=f"Enrollment stopped: {stop_reason}"
            )

        # Get or create execution record
        execution, created = SequenceStepExecution.objects.get_or_create(
            enrollment=enrollment,
            step=step,
            defaults={
                'status': SequenceStepExecution.Status.PENDING,
                'scheduled_at': enrollment.next_step_at or timezone.now()
            }
        )

        # Process based on step type
        if step.step_type == SequenceStep.StepType.EMAIL:
            result = self._execute_email_step(enrollment, step, execution)
        elif step.step_type == SequenceStep.StepType.DELAY:
            result = self._execute_delay_step(enrollment, step, execution)
        elif step.step_type == SequenceStep.StepType.TAG:
            result = self._execute_tag_step(enrollment, step, execution)
        elif step.step_type == SequenceStep.StepType.WEBHOOK:
            result = self._execute_webhook_step(enrollment, step, execution)
        elif step.step_type == SequenceStep.StepType.CONDITION:
            result = self._execute_condition_step(enrollment, step, execution)
        elif step.step_type == SequenceStep.StepType.TASK:
            result = self._execute_task_step(enrollment, step, execution)
        else:
            result = StepResult(
                success=False,
                message=f"Unknown step type: {step.step_type}"
            )

        return result

    def _execute_email_step(
        self,
        enrollment: SequenceEnrollment,
        step: SequenceStep,
        execution: SequenceStepExecution
    ) -> StepResult:
        """Execute an email step."""
        contact = enrollment.contact
        email_account = self.sequence.email_account

        if not email_account:
            execution.status = SequenceStepExecution.Status.FAILED
            execution.last_error = "No email account configured"
            execution.save()
            return StepResult(success=False, message="No email account configured")

        if not email_account.can_send:
            execution.status = SequenceStepExecution.Status.FAILED
            execution.last_error = "Email account cannot send"
            execution.save()
            return StepResult(success=False, message="Email account cannot send")

        try:
            # Render content
            context = self._build_contact_context(contact)

            subject = step.subject
            content_html = step.content_html
            content_text = step.content_text

            # If using template, get content from template
            if step.template:
                subject = step.template.subject
                content_html = step.template.content_html
                content_text = step.template.content_text

            render_result = self.template_engine.render(
                subject=subject,
                content_html=content_html,
                content_text=content_text or '',
                context=context,
                process_spintax=True
            )

            # Update execution with rendered content
            execution.status = SequenceStepExecution.Status.SENDING
            execution.rendered_subject = render_result.subject
            execution.rendered_html = render_result.content_html
            execution.rendered_text = render_result.content_text
            execution.email_account = email_account
            execution.save()

            # Send email
            email_service = EmailService(email_account)
            from_name = self.sequence.from_name or email_account.from_name
            reply_to = self.sequence.reply_to or email_account.reply_to

            result = email_service.send_email(
                to_email=contact.email,
                subject=render_result.subject,
                html_body=render_result.content_html,
                text_body=render_result.content_text or None,
                reply_to=reply_to,
                headers={
                    'X-Sequence-ID': str(self.sequence.id),
                    'X-Enrollment-ID': str(enrollment.id),
                    'X-Step-ID': str(step.id),
                }
            )

            if result.success:
                # Update execution
                execution.status = SequenceStepExecution.Status.SENT
                execution.sent_at = timezone.now()
                execution.executed_at = timezone.now()
                execution.message_id = result.message_id or ''
                execution.save()

                # Update step stats
                step.sent_count += 1
                step.save(update_fields=['sent_count'])

                # Update sequence stats
                self.sequence.total_sent += 1
                self.sequence.save(update_fields=['total_sent'])

                # Update enrollment
                enrollment.emails_sent += 1
                enrollment.last_step_at = timezone.now()
                enrollment.save(update_fields=['emails_sent', 'last_step_at'])

                # Update contact
                contact.emails_sent += 1
                contact.last_emailed_at = timezone.now()
                contact.save(update_fields=['emails_sent', 'last_emailed_at'])

                # Create event
                SequenceEvent.objects.create(
                    enrollment=enrollment,
                    step=step,
                    event_type=SequenceEvent.EventType.EMAIL_SENT,
                    message=f"Email sent: {render_result.subject}"
                )

                # Create contact activity
                ContactActivity.objects.create(
                    contact=contact,
                    activity_type=ContactActivity.ActivityType.EMAIL_SENT,
                    description=f"Sequence email: {self.sequence.name} - Step {step.order + 1}",
                    metadata={
                        'sequence_id': str(self.sequence.id),
                        'step_id': str(step.id),
                        'subject': render_result.subject
                    }
                )

                # Move to next step
                self._advance_to_next_step(enrollment, step)

                return StepResult(
                    success=True,
                    message="Email sent successfully",
                    message_id=result.message_id
                )
            else:
                # Handle failure
                execution.status = SequenceStepExecution.Status.FAILED
                execution.last_error = result.message
                execution.retry_count += 1
                execution.save()

                # Create error event
                SequenceEvent.objects.create(
                    enrollment=enrollment,
                    step=step,
                    event_type=SequenceEvent.EventType.ERROR,
                    message=f"Email failed: {result.message}"
                )

                return StepResult(
                    success=False,
                    message=result.message
                )

        except Exception as e:
            logger.exception(f"Error sending sequence email for enrollment {enrollment.id}")
            execution.status = SequenceStepExecution.Status.FAILED
            execution.last_error = str(e)
            execution.retry_count += 1
            execution.save()

            return StepResult(success=False, message=str(e))

    def _execute_delay_step(
        self,
        enrollment: SequenceEnrollment,
        step: SequenceStep,
        execution: SequenceStepExecution
    ) -> StepResult:
        """Execute a delay step (just advance to next step after delay)."""
        execution.status = SequenceStepExecution.Status.SENT
        execution.executed_at = timezone.now()
        execution.save()

        # Create event
        SequenceEvent.objects.create(
            enrollment=enrollment,
            step=step,
            event_type=SequenceEvent.EventType.STEP_EXECUTED,
            message=f"Delay completed: {step.delay_value} {step.delay_unit}"
        )

        # Move to next step
        self._advance_to_next_step(enrollment, step)

        return StepResult(
            success=True,
            message=f"Delay step completed"
        )

    def _execute_tag_step(
        self,
        enrollment: SequenceEnrollment,
        step: SequenceStep,
        execution: SequenceStepExecution
    ) -> StepResult:
        """Execute a tag step (add or remove tag)."""
        contact = enrollment.contact

        if not step.tag:
            execution.status = SequenceStepExecution.Status.FAILED
            execution.last_error = "No tag configured"
            execution.save()
            return StepResult(success=False, message="No tag configured")

        try:
            if step.tag_action == 'add':
                contact.tags.add(step.tag)
                event_type = SequenceEvent.EventType.TAG_ADDED
                message = f"Tag added: {step.tag.name}"
            elif step.tag_action == 'remove':
                contact.tags.remove(step.tag)
                event_type = SequenceEvent.EventType.TAG_REMOVED
                message = f"Tag removed: {step.tag.name}"
            else:
                return StepResult(success=False, message=f"Unknown tag action: {step.tag_action}")

            execution.status = SequenceStepExecution.Status.SENT
            execution.executed_at = timezone.now()
            execution.save()

            # Create event
            SequenceEvent.objects.create(
                enrollment=enrollment,
                step=step,
                event_type=event_type,
                message=message
            )

            # Move to next step
            self._advance_to_next_step(enrollment, step)

            return StepResult(success=True, message=message)

        except Exception as e:
            execution.status = SequenceStepExecution.Status.FAILED
            execution.last_error = str(e)
            execution.save()
            return StepResult(success=False, message=str(e))

    def _execute_webhook_step(
        self,
        enrollment: SequenceEnrollment,
        step: SequenceStep,
        execution: SequenceStepExecution
    ) -> StepResult:
        """Execute a webhook step."""
        if not step.webhook_url:
            execution.status = SequenceStepExecution.Status.FAILED
            execution.last_error = "No webhook URL configured"
            execution.save()
            return StepResult(success=False, message="No webhook URL configured")

        try:
            contact = enrollment.contact

            # Build payload
            payload = step.webhook_payload.copy() if step.webhook_payload else {}
            payload.update({
                'sequence_id': str(self.sequence.id),
                'sequence_name': self.sequence.name,
                'enrollment_id': str(enrollment.id),
                'step_id': str(step.id),
                'contact': {
                    'id': str(contact.id),
                    'email': contact.email,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'company': contact.company,
                    'score': contact.score,
                }
            })

            # Send webhook
            headers = step.webhook_headers.copy() if step.webhook_headers else {}
            headers['Content-Type'] = 'application/json'

            response = requests.request(
                method=step.webhook_method or 'POST',
                url=step.webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.ok:
                execution.status = SequenceStepExecution.Status.SENT
                execution.executed_at = timezone.now()
                execution.save()

                SequenceEvent.objects.create(
                    enrollment=enrollment,
                    step=step,
                    event_type=SequenceEvent.EventType.WEBHOOK_TRIGGERED,
                    message=f"Webhook triggered: {step.webhook_url}",
                    metadata={'status_code': response.status_code}
                )

                self._advance_to_next_step(enrollment, step)
                return StepResult(success=True, message="Webhook triggered successfully")
            else:
                execution.status = SequenceStepExecution.Status.FAILED
                execution.last_error = f"Webhook failed: {response.status_code}"
                execution.retry_count += 1
                execution.save()
                return StepResult(
                    success=False,
                    message=f"Webhook failed with status {response.status_code}"
                )

        except Exception as e:
            logger.exception(f"Error executing webhook for enrollment {enrollment.id}")
            execution.status = SequenceStepExecution.Status.FAILED
            execution.last_error = str(e)
            execution.retry_count += 1
            execution.save()
            return StepResult(success=False, message=str(e))

    def _execute_condition_step(
        self,
        enrollment: SequenceEnrollment,
        step: SequenceStep,
        execution: SequenceStepExecution
    ) -> StepResult:
        """Execute a condition step (branching)."""
        contact = enrollment.contact
        condition_met = False

        # Evaluate condition
        condition_type = step.condition_type
        condition_value = step.condition_value or {}

        if condition_type == 'opened':
            condition_met = enrollment.emails_opened > 0
        elif condition_type == 'clicked':
            condition_met = enrollment.emails_clicked > 0
        elif condition_type == 'replied':
            condition_met = enrollment.has_replied
        elif condition_type == 'score_above':
            threshold = condition_value.get('threshold', 50)
            condition_met = contact.score >= threshold
        elif condition_type == 'score_below':
            threshold = condition_value.get('threshold', 50)
            condition_met = contact.score < threshold
        elif condition_type == 'has_tag':
            tag_id = condition_value.get('tag_id')
            if tag_id:
                condition_met = contact.tags.filter(id=tag_id).exists()
        elif condition_type == 'email_count':
            count = condition_value.get('count', 1)
            operator = condition_value.get('operator', 'gte')
            if operator == 'gte':
                condition_met = enrollment.emails_sent >= count
            elif operator == 'lte':
                condition_met = enrollment.emails_sent <= count
            elif operator == 'eq':
                condition_met = enrollment.emails_sent == count

        execution.status = SequenceStepExecution.Status.SENT
        execution.executed_at = timezone.now()
        execution.save()

        SequenceEvent.objects.create(
            enrollment=enrollment,
            step=step,
            event_type=SequenceEvent.EventType.STEP_EXECUTED,
            message=f"Condition evaluated: {condition_type} = {condition_met}",
            metadata={'condition_met': condition_met}
        )

        # Determine next step based on condition result
        if condition_met and step.true_branch_step:
            next_step = step.true_branch_step
        elif not condition_met and step.false_branch_step:
            next_step = step.false_branch_step
        else:
            # No branch configured, advance normally
            next_step = self._get_next_step(step)

        if next_step:
            self._set_current_step(enrollment, next_step)
        else:
            enrollment.complete()
            self._update_sequence_stats_on_completion(enrollment)

        return StepResult(
            success=True,
            message=f"Condition evaluated: {condition_met}",
            next_step=next_step
        )

    def _execute_task_step(
        self,
        enrollment: SequenceEnrollment,
        step: SequenceStep,
        execution: SequenceStepExecution
    ) -> StepResult:
        """Execute a task step (create a task/reminder)."""
        # For now, just log the task creation event
        # In a full implementation, this would create a Task model entry

        execution.status = SequenceStepExecution.Status.SENT
        execution.executed_at = timezone.now()
        execution.save()

        SequenceEvent.objects.create(
            enrollment=enrollment,
            step=step,
            event_type=SequenceEvent.EventType.TASK_CREATED,
            message=f"Task created: {step.task_title}",
            metadata={
                'title': step.task_title,
                'description': step.task_description,
                'assignee_id': str(step.task_assignee.id) if step.task_assignee else None
            }
        )

        self._advance_to_next_step(enrollment, step)

        return StepResult(success=True, message=f"Task created: {step.task_title}")

    def _advance_to_next_step(self, enrollment: SequenceEnrollment, current_step: SequenceStep):
        """Advance enrollment to the next step."""
        next_step = self._get_next_step(current_step)

        if next_step:
            self._set_current_step(enrollment, next_step)
        else:
            # No more steps, complete the enrollment
            enrollment.complete()
            self._update_sequence_stats_on_completion(enrollment)

    def _get_next_step(self, current_step: SequenceStep) -> Optional[SequenceStep]:
        """Get the next step in the sequence."""
        return self.sequence.steps.filter(
            order__gt=current_step.order,
            is_active=True
        ).order_by('order').first()

    def _set_current_step(self, enrollment: SequenceEnrollment, step: SequenceStep):
        """Set the current step for an enrollment and schedule it."""
        next_step_at = self._calculate_next_step_time(step)

        enrollment.current_step = step
        enrollment.current_step_index = step.order
        enrollment.next_step_at = next_step_at
        enrollment.save(update_fields=['current_step', 'current_step_index', 'next_step_at'])

        # Create execution record for next step
        SequenceStepExecution.objects.create(
            enrollment=enrollment,
            step=step,
            status=SequenceStepExecution.Status.SCHEDULED,
            scheduled_at=next_step_at,
        )

    def _calculate_next_step_time(self, step: SequenceStep) -> datetime:
        """Calculate when the next step should be executed."""
        now = timezone.now()

        # If it's an email step, add the delay from the step or previous delay step
        if step.step_type == SequenceStep.StepType.EMAIL:
            # Look for a delay step before this email step
            delay_step = self.sequence.steps.filter(
                order__lt=step.order,
                step_type=SequenceStep.StepType.DELAY,
                is_active=True
            ).order_by('-order').first()

            if delay_step:
                delay_seconds = delay_step.delay_seconds
            else:
                # Use minimum delay between emails from sequence settings
                delay_seconds = self.sequence.min_delay_between_emails
        elif step.step_type == SequenceStep.StepType.DELAY:
            delay_seconds = step.delay_seconds
        else:
            # For other step types, execute immediately (or with minimal delay)
            delay_seconds = 0

        next_time = now + timedelta(seconds=delay_seconds)

        # Apply sending window if enabled
        if self.sequence.send_window_enabled:
            next_time = self._apply_send_window(next_time)

        return next_time

    def _apply_send_window(self, target_time: datetime) -> datetime:
        """Adjust time to fit within sending window."""
        if not self.sequence.send_window_start or not self.sequence.send_window_end:
            return target_time

        tz = pytz.timezone(self.sequence.send_window_timezone)
        local_time = target_time.astimezone(tz)

        window_days = self.sequence.send_window_days or [0, 1, 2, 3, 4]  # Default Mon-Fri

        # Check if current day is allowed
        while local_time.weekday() not in window_days:
            local_time = local_time + timedelta(days=1)
            local_time = local_time.replace(
                hour=self.sequence.send_window_start.hour,
                minute=self.sequence.send_window_start.minute,
                second=0
            )

        # Check if within time window
        window_start = local_time.replace(
            hour=self.sequence.send_window_start.hour,
            minute=self.sequence.send_window_start.minute,
            second=0
        )
        window_end = local_time.replace(
            hour=self.sequence.send_window_end.hour,
            minute=self.sequence.send_window_end.minute,
            second=0
        )

        if local_time < window_start:
            # Before window, schedule at window start
            local_time = window_start
        elif local_time > window_end:
            # After window, schedule next valid day
            local_time = local_time + timedelta(days=1)
            while local_time.weekday() not in window_days:
                local_time = local_time + timedelta(days=1)
            local_time = local_time.replace(
                hour=self.sequence.send_window_start.hour,
                minute=self.sequence.send_window_start.minute,
                second=0
            )

        return local_time.astimezone(pytz.UTC)

    def _check_stop_conditions(self, enrollment: SequenceEnrollment) -> Tuple[bool, str]:
        """Check if any stop conditions are met."""
        contact = enrollment.contact

        if self.sequence.stop_on_reply and enrollment.has_replied:
            return True, SequenceEnrollment.StopReason.REPLY

        if self.sequence.stop_on_click and enrollment.emails_clicked > 0:
            return True, SequenceEnrollment.StopReason.CLICK

        if self.sequence.stop_on_open and enrollment.emails_opened > 0:
            return True, SequenceEnrollment.StopReason.OPEN

        if self.sequence.stop_on_bounce:
            # Check if any execution has bounced
            if enrollment.step_executions.filter(
                status=SequenceStepExecution.Status.BOUNCED
            ).exists():
                return True, SequenceEnrollment.StopReason.BOUNCE

        if self.sequence.stop_on_score_above is not None:
            if contact.score >= self.sequence.stop_on_score_above:
                return True, SequenceEnrollment.StopReason.SCORE_HIGH

        if self.sequence.stop_on_score_below is not None:
            if contact.score <= self.sequence.stop_on_score_below:
                return True, SequenceEnrollment.StopReason.SCORE_LOW

        # Check contact status
        if contact.status == Contact.Status.UNSUBSCRIBED:
            return True, SequenceEnrollment.StopReason.UNSUBSCRIBE

        return False, ''

    def _update_sequence_stats_on_completion(self, enrollment: SequenceEnrollment):
        """Update sequence stats when enrollment completes."""
        self.sequence.completed_count += 1
        self.sequence.active_enrolled -= 1
        self.sequence.save(update_fields=['completed_count', 'active_enrolled'])

        SequenceEvent.objects.create(
            enrollment=enrollment,
            event_type=SequenceEvent.EventType.COMPLETED,
            message="Sequence completed"
        )

    def _update_sequence_stats_on_stop(self, enrollment: SequenceEnrollment):
        """Update sequence stats when enrollment is stopped."""
        self.sequence.stopped_count += 1
        self.sequence.active_enrolled -= 1
        self.sequence.save(update_fields=['stopped_count', 'active_enrolled'])

        SequenceEvent.objects.create(
            enrollment=enrollment,
            event_type=SequenceEvent.EventType.STOPPED,
            message=f"Enrollment stopped: {enrollment.get_stop_reason_display()}"
        )

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

    def pause_sequence(self):
        """Pause the sequence and all active enrollments."""
        if self.sequence.status != Sequence.Status.ACTIVE:
            return False, "Sequence is not active"

        with transaction.atomic():
            self.sequence.status = Sequence.Status.PAUSED
            self.sequence.save(update_fields=['status'])

            # Pause all active enrollments
            SequenceEnrollment.objects.filter(
                sequence=self.sequence,
                status=SequenceEnrollment.Status.ACTIVE
            ).update(
                status=SequenceEnrollment.Status.PAUSED,
                paused_at=timezone.now()
            )

        return True, "Sequence paused"

    def resume_sequence(self):
        """Resume a paused sequence and its enrollments."""
        if self.sequence.status != Sequence.Status.PAUSED:
            return False, "Sequence is not paused"

        with transaction.atomic():
            self.sequence.status = Sequence.Status.ACTIVE
            self.sequence.save(update_fields=['status'])

            # Resume paused enrollments
            SequenceEnrollment.objects.filter(
                sequence=self.sequence,
                status=SequenceEnrollment.Status.PAUSED
            ).update(
                status=SequenceEnrollment.Status.ACTIVE,
                paused_at=None
            )

        return True, "Sequence resumed"

    def get_enrollments_to_process(self, limit: int = 50) -> List[SequenceEnrollment]:
        """Get enrollments that are ready to be processed."""
        now = timezone.now()

        return list(
            SequenceEnrollment.objects.filter(
                sequence=self.sequence,
                status=SequenceEnrollment.Status.ACTIVE,
                next_step_at__lte=now
            ).select_related(
                'contact', 'current_step'
            ).order_by('next_step_at')[:limit]
        )

    def record_open(self, enrollment: SequenceEnrollment, step: SequenceStep, metadata: dict = None):
        """Record an email open event."""
        enrollment.emails_opened += 1
        enrollment.save(update_fields=['emails_opened'])

        step.opened_count += 1
        step.save(update_fields=['opened_count'])

        self.sequence.total_opened += 1
        self.sequence.save(update_fields=['total_opened'])

        # Update execution
        execution = SequenceStepExecution.objects.filter(
            enrollment=enrollment,
            step=step
        ).first()
        if execution:
            execution.status = SequenceStepExecution.Status.OPENED
            execution.opened_at = timezone.now()
            execution.open_count += 1
            execution.save()

        SequenceEvent.objects.create(
            enrollment=enrollment,
            step=step,
            event_type=SequenceEvent.EventType.EMAIL_OPENED,
            message="Email opened",
            metadata=metadata or {}
        )

    def record_click(self, enrollment: SequenceEnrollment, step: SequenceStep, url: str, metadata: dict = None):
        """Record an email click event."""
        enrollment.emails_clicked += 1
        enrollment.save(update_fields=['emails_clicked'])

        step.clicked_count += 1
        step.save(update_fields=['clicked_count'])

        self.sequence.total_clicked += 1
        self.sequence.save(update_fields=['total_clicked'])

        # Update execution
        execution = SequenceStepExecution.objects.filter(
            enrollment=enrollment,
            step=step
        ).first()
        if execution:
            execution.status = SequenceStepExecution.Status.CLICKED
            execution.clicked_at = timezone.now()
            execution.click_count += 1
            if url:
                clicked_urls = execution.clicked_urls or []
                clicked_urls.append(url)
                execution.clicked_urls = clicked_urls
            execution.save()

        SequenceEvent.objects.create(
            enrollment=enrollment,
            step=step,
            event_type=SequenceEvent.EventType.EMAIL_CLICKED,
            message="Email clicked",
            clicked_url=url,
            metadata=metadata or {}
        )

    def record_reply(self, enrollment: SequenceEnrollment, step: SequenceStep = None):
        """Record a reply event."""
        enrollment.has_replied = True
        enrollment.save(update_fields=['has_replied'])

        if step:
            step.replied_count += 1
            step.save(update_fields=['replied_count'])

        self.sequence.total_replied += 1
        self.sequence.save(update_fields=['total_replied'])

        SequenceEvent.objects.create(
            enrollment=enrollment,
            step=step,
            event_type=SequenceEvent.EventType.EMAIL_REPLIED,
            message="Contact replied"
        )

        # Check stop condition
        if self.sequence.stop_on_reply:
            enrollment.stop(SequenceEnrollment.StopReason.REPLY)
            self._update_sequence_stats_on_stop(enrollment)

    def record_bounce(self, enrollment: SequenceEnrollment, step: SequenceStep = None, reason: str = ''):
        """Record a bounce event."""
        if step:
            step.bounced_count += 1
            step.save(update_fields=['bounced_count'])

        # Update execution
        execution = SequenceStepExecution.objects.filter(
            enrollment=enrollment,
            step=step
        ).first()
        if execution:
            execution.status = SequenceStepExecution.Status.BOUNCED
            execution.status_reason = reason
            execution.save()

        SequenceEvent.objects.create(
            enrollment=enrollment,
            step=step,
            event_type=SequenceEvent.EventType.EMAIL_BOUNCED,
            message=f"Email bounced: {reason}"
        )

        # Check stop condition
        if self.sequence.stop_on_bounce:
            enrollment.stop(SequenceEnrollment.StopReason.BOUNCE, reason)
            self._update_sequence_stats_on_stop(enrollment)

    def get_stats(self) -> dict:
        """Get sequence statistics."""
        return {
            'total_enrolled': self.sequence.total_enrolled,
            'active_enrolled': self.sequence.active_enrolled,
            'completed': self.sequence.completed_count,
            'stopped': self.sequence.stopped_count,
            'total_sent': self.sequence.total_sent,
            'total_opened': self.sequence.total_opened,
            'total_clicked': self.sequence.total_clicked,
            'total_replied': self.sequence.total_replied,
            'open_rate': self.sequence.open_rate,
            'click_rate': self.sequence.click_rate,
            'reply_rate': self.sequence.reply_rate,
            'steps': self.sequence.step_count,
        }
