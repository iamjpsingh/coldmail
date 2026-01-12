import csv
import json
from celery import shared_task
from django.db.models import Sum
from django.utils import timezone


@shared_task
def process_import_job(import_job_id: str):
    """Process a contact import job."""
    from .models import ImportJob, Contact, Tag

    try:
        import_job = ImportJob.objects.get(id=import_job_id)
    except ImportJob.DoesNotExist:
        return {'error': 'Import job not found'}

    if import_job.status == ImportJob.Status.CANCELLED:
        return {'status': 'cancelled'}

    import_job.status = ImportJob.Status.PROCESSING
    import_job.started_at = timezone.now()
    import_job.save(update_fields=['status', 'started_at'])

    try:
        if import_job.file_type == ImportJob.FileType.CSV:
            result = _process_csv_import(import_job)
        elif import_job.file_type == ImportJob.FileType.EXCEL:
            result = _process_excel_import(import_job)
        elif import_job.file_type == ImportJob.FileType.JSON:
            result = _process_json_import(import_job)
        else:
            raise ValueError(f'Unsupported file type: {import_job.file_type}')

        import_job.status = ImportJob.Status.COMPLETED
        import_job.completed_at = timezone.now()
        import_job.save(update_fields=[
            'status', 'completed_at', 'total_rows', 'processed_rows',
            'created_count', 'updated_count', 'skipped_count', 'error_count', 'errors'
        ])

        return result

    except Exception as e:
        import_job.status = ImportJob.Status.FAILED
        import_job.errors = [{'error': str(e)}]
        import_job.completed_at = timezone.now()
        import_job.save(update_fields=['status', 'errors', 'completed_at'])
        return {'error': str(e)}


def _process_csv_import(import_job):
    """Process CSV file import."""
    from .models import Contact

    with open(import_job.file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    import_job.total_rows = len(rows)
    import_job.save(update_fields=['total_rows'])

    return _process_rows(import_job, rows)


def _process_excel_import(import_job):
    """Process Excel file import."""
    import openpyxl
    from .models import Contact

    wb = openpyxl.load_workbook(import_job.file_path, read_only=True)
    sheet = wb.active

    all_rows = list(sheet.iter_rows(values_only=True))
    if not all_rows:
        return {'error': 'Empty file'}

    headers = [str(h).lower() if h else '' for h in all_rows[0]]
    rows = []
    for row in all_rows[1:]:
        rows.append(dict(zip(headers, row)))

    import_job.total_rows = len(rows)
    import_job.save(update_fields=['total_rows'])

    return _process_rows(import_job, rows)


def _process_json_import(import_job):
    """Process JSON file import."""
    from .models import Contact

    with open(import_job.file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        return {'error': 'JSON must be an array of objects'}

    import_job.total_rows = len(data)
    import_job.save(update_fields=['total_rows'])

    return _process_rows(import_job, data)


def _process_rows(import_job, rows):
    """Process rows and create/update contacts."""
    from .models import Contact, Tag

    field_mapping = import_job.field_mapping
    errors = []

    created_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for i, row in enumerate(rows):
        # Check if cancelled
        import_job.refresh_from_db()
        if import_job.status == ImportJob.Status.CANCELLED:
            break

        try:
            contact_data = _map_row_to_contact(row, field_mapping)

            if not contact_data.get('email'):
                skipped_count += 1
                errors.append({
                    'row': i + 2,
                    'error': 'Missing email address'
                })
                continue

            # Check for existing contact
            existing = Contact.objects.filter(
                workspace=import_job.workspace,
                email=contact_data['email']
            ).first()

            if existing:
                # Update existing contact
                for key, value in contact_data.items():
                    if key != 'email' and value:
                        setattr(existing, key, value)
                existing.save()
                updated_count += 1
            else:
                # Create new contact
                contact = Contact.objects.create(
                    workspace=import_job.workspace,
                    **contact_data
                )
                created_count += 1

                # Add default tags
                if import_job.default_tags.exists():
                    contact.tags.add(*import_job.default_tags.all())

                # Add to default list
                if import_job.default_list:
                    import_job.default_list.contacts.add(contact)

        except Exception as e:
            error_count += 1
            errors.append({
                'row': i + 2,
                'error': str(e)
            })

        # Update progress
        import_job.processed_rows = i + 1
        import_job.created_count = created_count
        import_job.updated_count = updated_count
        import_job.skipped_count = skipped_count
        import_job.error_count = error_count
        import_job.errors = errors[-100:]  # Keep last 100 errors
        import_job.save(update_fields=[
            'processed_rows', 'created_count', 'updated_count',
            'skipped_count', 'error_count', 'errors'
        ])

    return {
        'created': created_count,
        'updated': updated_count,
        'skipped': skipped_count,
        'errors': error_count
    }


def _map_row_to_contact(row, field_mapping):
    """Map a row to contact fields using field mapping."""
    contact_data = {}

    # Standard field mapping
    standard_fields = [
        'email', 'first_name', 'last_name', 'company', 'job_title',
        'phone', 'website', 'linkedin_url', 'twitter_handle',
        'city', 'state', 'country', 'timezone', 'source', 'notes'
    ]

    for field in standard_fields:
        source_field = field_mapping.get(field)
        if source_field and source_field in row:
            value = row[source_field]
            if value is not None:
                contact_data[field] = str(value).strip() if value else ''

    # Handle custom fields
    custom_fields = {}
    for key, source in field_mapping.items():
        if key.startswith('custom_') and source in row:
            custom_key = key.replace('custom_', '')
            value = row[source]
            if value is not None:
                custom_fields[custom_key] = value

    if custom_fields:
        contact_data['custom_fields'] = custom_fields

    return contact_data


@shared_task
def update_smart_list_counts():
    """Update contact counts for all smart lists."""
    from .models import ContactList

    smart_lists = ContactList.objects.filter(
        list_type=ContactList.ListType.SMART
    )

    for contact_list in smart_lists:
        contact_list.update_contact_count()

    return {'updated_lists': smart_lists.count()}


@shared_task
def run_score_decay_all_workspaces():
    """Run score decay for all workspaces with decay enabled."""
    from .models import ScoreDecayConfig
    from .services import ScoringEngine

    results = []
    configs = ScoreDecayConfig.objects.filter(is_enabled=True)

    for config in configs:
        engine = ScoringEngine(config.workspace)
        result = engine.run_score_decay()
        results.append({
            'workspace_id': str(config.workspace.id),
            'result': result
        })

    return {
        'processed_workspaces': len(results),
        'results': results
    }


@shared_task
def run_score_decay_for_workspace(workspace_id: str):
    """Run score decay for a specific workspace."""
    from apps.workspaces.models import Workspace
    from .services import ScoringEngine

    try:
        workspace = Workspace.objects.get(id=workspace_id)
    except Workspace.DoesNotExist:
        return {'error': 'Workspace not found'}

    engine = ScoringEngine(workspace)
    result = engine.run_score_decay()

    return result


@shared_task
def apply_scoring_event(contact_id: str, event_type: str, event_data: dict = None):
    """Apply a scoring event to a contact."""
    from .models import Contact
    from .services import ScoringEngine

    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        return {'error': 'Contact not found'}

    engine = ScoringEngine(contact.workspace)
    result = engine.apply_event(contact, event_type, event_data or {})

    return {
        'success': result.success,
        'contact_id': result.contact_id,
        'previous_score': result.previous_score,
        'new_score': result.new_score,
        'score_change': result.score_change,
        'rules_applied': result.rules_applied,
        'message': result.message
    }


@shared_task
def bulk_apply_scoring_event(contact_ids: list, event_type: str, event_data: dict = None):
    """Apply a scoring event to multiple contacts."""
    from .models import Contact
    from .services import ScoringEngine

    results = []
    contacts = Contact.objects.filter(id__in=contact_ids).select_related('workspace')

    # Group contacts by workspace for efficiency
    workspace_contacts = {}
    for contact in contacts:
        if contact.workspace_id not in workspace_contacts:
            workspace_contacts[contact.workspace_id] = []
        workspace_contacts[contact.workspace_id].append(contact)

    for workspace_id, ws_contacts in workspace_contacts.items():
        engine = ScoringEngine(ws_contacts[0].workspace)
        for contact in ws_contacts:
            result = engine.apply_event(contact, event_type, event_data or {})
            results.append({
                'contact_id': result.contact_id,
                'score_change': result.score_change,
                'new_score': result.new_score
            })

    return {
        'processed_count': len(results),
        'results': results
    }


@shared_task
def recalculate_all_scores(workspace_id: str):
    """Recalculate all contact scores for a workspace based on their history."""
    from apps.workspaces.models import Workspace
    from .models import Contact, ScoreHistory

    try:
        workspace = Workspace.objects.get(id=workspace_id)
    except Workspace.DoesNotExist:
        return {'error': 'Workspace not found'}

    contacts = Contact.objects.filter(workspace=workspace, status=Contact.Status.ACTIVE)
    updated_count = 0

    for contact in contacts:
        # Sum all score changes from history
        total_score = ScoreHistory.objects.filter(
            contact=contact
        ).aggregate(
            total=Sum('score_change')
        )['total'] or 0

        # Apply starting score (default 50) plus all changes
        new_score = max(0, min(100, 50 + total_score))

        if contact.score != new_score:
            contact.score = new_score
            contact.save(update_fields=['score'])
            updated_count += 1

    return {
        'total_contacts': contacts.count(),
        'updated_count': updated_count
    }
