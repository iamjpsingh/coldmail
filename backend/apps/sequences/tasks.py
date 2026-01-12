import logging
from celery import shared_task
from django.db import models, transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_sequence_enrollments(self):
    """
    Process all active sequence enrollments that are due.
    This task should be run every minute via Celery beat.
    """
    from apps.sequences.models import Sequence, SequenceEnrollment
    from apps.sequences.services.sequence_engine import SequenceEngine

    now = timezone.now()
    processed_count = 0
    error_count = 0

    # Get all active sequences
    active_sequences = Sequence.objects.filter(status=Sequence.Status.ACTIVE)

    for sequence in active_sequences:
        engine = SequenceEngine(sequence)

        # Get enrollments ready to process
        enrollments = engine.get_enrollments_to_process(limit=100)

        for enrollment in enrollments:
            try:
                result = engine.process_enrollment(enrollment)
                if result.success:
                    processed_count += 1
                else:
                    error_count += 1
                    logger.warning(
                        f"Failed to process enrollment {enrollment.id}: {result.message}"
                    )
            except Exception as e:
                error_count += 1
                logger.exception(
                    f"Error processing enrollment {enrollment.id}: {str(e)}"
                )
                # Mark enrollment with error
                enrollment.last_error = str(e)
                enrollment.retry_count += 1
                enrollment.save(update_fields=['last_error', 'retry_count'])

    logger.info(f"Processed {processed_count} enrollments, {error_count} errors")
    return {'processed': processed_count, 'errors': error_count}


@shared_task(bind=True, max_retries=3)
def process_single_enrollment(self, enrollment_id: str):
    """Process a single enrollment."""
    from apps.sequences.models import SequenceEnrollment
    from apps.sequences.services.sequence_engine import SequenceEngine

    try:
        enrollment = SequenceEnrollment.objects.select_related(
            'sequence', 'contact', 'current_step'
        ).get(id=enrollment_id)

        engine = SequenceEngine(enrollment.sequence)
        result = engine.process_enrollment(enrollment)

        return {
            'success': result.success,
            'message': result.message,
            'enrollment_id': str(enrollment_id)
        }

    except SequenceEnrollment.DoesNotExist:
        logger.error(f"Enrollment {enrollment_id} not found")
        return {'success': False, 'message': 'Enrollment not found'}
    except Exception as e:
        logger.exception(f"Error processing enrollment {enrollment_id}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def enroll_contact_in_sequence(sequence_id: str, contact_id: str, user_id: str = None, source: str = 'api'):
    """Enroll a contact in a sequence asynchronously."""
    from apps.sequences.models import Sequence
    from apps.sequences.services.sequence_engine import SequenceEngine
    from apps.contacts.models import Contact
    from apps.users.models import User

    try:
        sequence = Sequence.objects.get(id=sequence_id)
        contact = Contact.objects.get(id=contact_id)
        user = User.objects.get(id=user_id) if user_id else None

        engine = SequenceEngine(sequence)
        result = engine.enroll_contact(contact, enrolled_by=user, source=source)

        return {
            'success': result.success,
            'message': result.message,
            'enrollment_id': result.enrollment_id
        }

    except (Sequence.DoesNotExist, Contact.DoesNotExist) as e:
        logger.error(f"Sequence or Contact not found: {str(e)}")
        return {'success': False, 'message': str(e)}
    except Exception as e:
        logger.exception(f"Error enrolling contact {contact_id} in sequence {sequence_id}")
        return {'success': False, 'message': str(e)}


@shared_task
def bulk_enroll_contacts_in_sequence(
    sequence_id: str,
    contact_ids: list,
    user_id: str = None,
    source: str = 'bulk'
):
    """Enroll multiple contacts in a sequence asynchronously."""
    from apps.sequences.models import Sequence
    from apps.sequences.services.sequence_engine import SequenceEngine
    from apps.contacts.models import Contact
    from apps.users.models import User

    try:
        sequence = Sequence.objects.get(id=sequence_id)
        contacts = Contact.objects.filter(id__in=contact_ids)
        user = User.objects.get(id=user_id) if user_id else None

        engine = SequenceEngine(sequence)
        success_count, failed_count, errors = engine.bulk_enroll(
            list(contacts), enrolled_by=user, source=source
        )

        return {
            'success': True,
            'enrolled': success_count,
            'failed': failed_count,
            'errors': errors[:10]  # Limit error messages
        }

    except Sequence.DoesNotExist:
        logger.error(f"Sequence {sequence_id} not found")
        return {'success': False, 'message': 'Sequence not found'}
    except Exception as e:
        logger.exception(f"Error bulk enrolling contacts in sequence {sequence_id}")
        return {'success': False, 'message': str(e)}


@shared_task
def pause_enrollment(enrollment_id: str):
    """Pause a specific enrollment."""
    from apps.sequences.models import SequenceEnrollment, SequenceEvent

    try:
        enrollment = SequenceEnrollment.objects.get(id=enrollment_id)
        enrollment.pause()

        SequenceEvent.objects.create(
            enrollment=enrollment,
            event_type=SequenceEvent.EventType.PAUSED,
            message="Enrollment paused"
        )

        return {'success': True, 'enrollment_id': str(enrollment_id)}

    except SequenceEnrollment.DoesNotExist:
        return {'success': False, 'message': 'Enrollment not found'}


@shared_task
def resume_enrollment(enrollment_id: str):
    """Resume a paused enrollment."""
    from apps.sequences.models import SequenceEnrollment, SequenceEvent

    try:
        enrollment = SequenceEnrollment.objects.get(id=enrollment_id)
        enrollment.resume()

        SequenceEvent.objects.create(
            enrollment=enrollment,
            event_type=SequenceEvent.EventType.RESUMED,
            message="Enrollment resumed"
        )

        return {'success': True, 'enrollment_id': str(enrollment_id)}

    except SequenceEnrollment.DoesNotExist:
        return {'success': False, 'message': 'Enrollment not found'}


@shared_task
def stop_enrollment(enrollment_id: str, reason: str = 'manual', details: str = ''):
    """Stop an enrollment with a specific reason."""
    from apps.sequences.models import SequenceEnrollment, SequenceEvent, Sequence
    from apps.sequences.services.sequence_engine import SequenceEngine

    try:
        enrollment = SequenceEnrollment.objects.select_related('sequence').get(id=enrollment_id)
        enrollment.stop(reason, details)

        # Update sequence stats
        engine = SequenceEngine(enrollment.sequence)
        engine._update_sequence_stats_on_stop(enrollment)

        return {'success': True, 'enrollment_id': str(enrollment_id)}

    except SequenceEnrollment.DoesNotExist:
        return {'success': False, 'message': 'Enrollment not found'}


@shared_task
def handle_sequence_open_event(enrollment_id: str, step_id: str, metadata: dict = None):
    """Handle an email open event for a sequence."""
    from apps.sequences.models import SequenceEnrollment, SequenceStep
    from apps.sequences.services.sequence_engine import SequenceEngine

    try:
        enrollment = SequenceEnrollment.objects.select_related('sequence').get(id=enrollment_id)
        step = SequenceStep.objects.get(id=step_id)

        engine = SequenceEngine(enrollment.sequence)
        engine.record_open(enrollment, step, metadata)

        return {'success': True}

    except (SequenceEnrollment.DoesNotExist, SequenceStep.DoesNotExist) as e:
        logger.error(f"Enrollment or Step not found: {str(e)}")
        return {'success': False, 'message': str(e)}


@shared_task
def handle_sequence_click_event(
    enrollment_id: str,
    step_id: str,
    url: str,
    metadata: dict = None
):
    """Handle an email click event for a sequence."""
    from apps.sequences.models import SequenceEnrollment, SequenceStep
    from apps.sequences.services.sequence_engine import SequenceEngine

    try:
        enrollment = SequenceEnrollment.objects.select_related('sequence').get(id=enrollment_id)
        step = SequenceStep.objects.get(id=step_id)

        engine = SequenceEngine(enrollment.sequence)
        engine.record_click(enrollment, step, url, metadata)

        return {'success': True}

    except (SequenceEnrollment.DoesNotExist, SequenceStep.DoesNotExist) as e:
        logger.error(f"Enrollment or Step not found: {str(e)}")
        return {'success': False, 'message': str(e)}


@shared_task
def handle_sequence_reply_event(enrollment_id: str, step_id: str = None):
    """Handle a reply event for a sequence."""
    from apps.sequences.models import SequenceEnrollment, SequenceStep
    from apps.sequences.services.sequence_engine import SequenceEngine

    try:
        enrollment = SequenceEnrollment.objects.select_related('sequence').get(id=enrollment_id)
        step = SequenceStep.objects.get(id=step_id) if step_id else None

        engine = SequenceEngine(enrollment.sequence)
        engine.record_reply(enrollment, step)

        return {'success': True}

    except SequenceEnrollment.DoesNotExist:
        logger.error(f"Enrollment {enrollment_id} not found")
        return {'success': False, 'message': 'Enrollment not found'}


@shared_task
def handle_sequence_bounce_event(enrollment_id: str, step_id: str = None, reason: str = ''):
    """Handle a bounce event for a sequence."""
    from apps.sequences.models import SequenceEnrollment, SequenceStep
    from apps.sequences.services.sequence_engine import SequenceEngine

    try:
        enrollment = SequenceEnrollment.objects.select_related('sequence').get(id=enrollment_id)
        step = SequenceStep.objects.get(id=step_id) if step_id else None

        engine = SequenceEngine(enrollment.sequence)
        engine.record_bounce(enrollment, step, reason)

        return {'success': True}

    except SequenceEnrollment.DoesNotExist:
        logger.error(f"Enrollment {enrollment_id} not found")
        return {'success': False, 'message': 'Enrollment not found'}


@shared_task
def check_score_stop_conditions():
    """
    Periodically check score-based stop conditions for active enrollments.
    Should be run every hour or so.
    """
    from apps.sequences.models import Sequence, SequenceEnrollment
    from apps.sequences.services.sequence_engine import SequenceEngine

    stopped_count = 0

    # Get sequences with score-based stop conditions
    sequences = Sequence.objects.filter(
        status=Sequence.Status.ACTIVE
    ).filter(
        models.Q(stop_on_score_above__isnull=False) |
        models.Q(stop_on_score_below__isnull=False)
    )

    for sequence in sequences:
        engine = SequenceEngine(sequence)

        # Check active enrollments
        enrollments = SequenceEnrollment.objects.filter(
            sequence=sequence,
            status=SequenceEnrollment.Status.ACTIVE
        ).select_related('contact')

        for enrollment in enrollments:
            should_stop, reason = engine._check_stop_conditions(enrollment)
            if should_stop and reason in [
                SequenceEnrollment.StopReason.SCORE_HIGH,
                SequenceEnrollment.StopReason.SCORE_LOW
            ]:
                enrollment.stop(reason)
                engine._update_sequence_stats_on_stop(enrollment)
                stopped_count += 1

    logger.info(f"Stopped {stopped_count} enrollments due to score conditions")
    return {'stopped': stopped_count}


@shared_task
def cleanup_old_sequence_events(days: int = 90):
    """Clean up old sequence events to save storage."""
    from apps.sequences.models import SequenceEvent
    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)

    deleted_count, _ = SequenceEvent.objects.filter(
        created_at__lt=cutoff_date
    ).delete()

    logger.info(f"Deleted {deleted_count} old sequence events")
    return {'deleted': deleted_count}


@shared_task
def generate_sequence_stats_report(sequence_id: str):
    """Generate a detailed stats report for a sequence."""
    from apps.sequences.models import Sequence
    from apps.sequences.services.sequence_engine import SequenceEngine

    try:
        sequence = Sequence.objects.get(id=sequence_id)
        engine = SequenceEngine(sequence)

        stats = engine.get_stats()

        # Get step-level stats
        step_stats = []
        for step in sequence.steps.all():
            step_stats.append({
                'order': step.order,
                'type': step.step_type,
                'name': step.name or f"Step {step.order + 1}",
                'sent': step.sent_count,
                'opened': step.opened_count,
                'clicked': step.clicked_count,
                'replied': step.replied_count,
                'bounced': step.bounced_count,
                'open_rate': step.open_rate,
                'click_rate': step.click_rate,
            })

        return {
            'success': True,
            'sequence_id': str(sequence_id),
            'stats': stats,
            'step_stats': step_stats
        }

    except Sequence.DoesNotExist:
        return {'success': False, 'message': 'Sequence not found'}
