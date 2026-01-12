---
name: django-clean-architecture
description: Build modular, scalable Django backends using service layer pattern. Use when creating Django models, views, APIs, Celery tasks, or any backend feature. Enforces clean separation between data, business logic, and API layers.
---

# Django Clean Architecture Skill

Build production-grade Django applications with clear separation of concerns, type safety, and scalability in mind.

---

## Architecture Overview

```
apps/
├── {app_name}/
│   ├── models.py       # Data layer - ORM models only
│   ├── services.py     # Business layer - ALL logic here
│   ├── selectors.py    # Query layer - Complex reads
│   ├── serializers.py  # API layer - Validation/formatting
│   ├── views.py        # API layer - Thin HTTP handlers
│   ├── permissions.py  # Auth layer - Access control
│   ├── tasks.py        # Async layer - Celery tasks
│   ├── signals.py      # Event layer - Django signals
│   ├── exceptions.py   # Custom exceptions
│   └── urls.py         # URL routing
```

---

## Layer Rules

### Models (Data Layer)

**DO:**
- Define fields, relationships, Meta options
- Add simple computed properties
- Create database indexes for filtered fields
- Use UUIDs as primary keys
- Add created_at/updated_at timestamps

**DON'T:**
- Add business logic methods
- Perform validation beyond field constraints
- Send emails, create related objects
- Import services or other layers

```python
import uuid
from django.db import models

class Campaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='campaigns'
    )
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('sending', 'Sending'),
            ('completed', 'Completed'),
            ('paused', 'Paused'),
        ],
        default='draft'
    )
    template = models.ForeignKey(
        'templates.EmailTemplate',
        on_delete=models.PROTECT
    )
    schedule_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['schedule_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'name'],
                name='unique_campaign_name_per_workspace'
            )
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_editable(self) -> bool:
        """Campaign can only be edited in draft status."""
        return self.status == 'draft'
```

---

### Services (Business Layer)

**DO:**
- Handle ALL create/update/delete operations
- Validate business rules
- Orchestrate multi-step operations
- Trigger side effects (emails, notifications)
- Use type hints and docstrings
- Raise custom exceptions

**DON'T:**
- Access request objects directly
- Return HTTP responses
- Handle serialization

```python
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from django.db import transaction

from .models import Campaign, CampaignRecipient
from .exceptions import (
    CampaignNotFoundError,
    CampaignNotEditableError,
    NoRecipientsError,
    DuplicateCampaignNameError,
)


class CampaignService:
    """Service for campaign business logic."""

    @staticmethod
    def create_campaign(
        workspace: 'Workspace',
        name: str,
        template: 'EmailTemplate',
        recipients: List['Contact'],
        schedule_at: Optional[datetime] = None,
    ) -> Campaign:
        """
        Create a new email campaign.

        Args:
            workspace: The workspace owning this campaign.
            name: Unique campaign name within workspace.
            template: Email template to use for sending.
            recipients: List of contacts to receive the campaign.
            schedule_at: Optional datetime for scheduled sending.

        Returns:
            The created Campaign instance.

        Raises:
            NoRecipientsError: If recipients list is empty.
            DuplicateCampaignNameError: If name already exists in workspace.
        """
        if not recipients:
            raise NoRecipientsError("At least one recipient is required")

        if Campaign.objects.filter(workspace=workspace, name=name).exists():
            raise DuplicateCampaignNameError(
                f"Campaign '{name}' already exists in this workspace"
            )

        with transaction.atomic():
            campaign = Campaign.objects.create(
                workspace=workspace,
                name=name,
                template=template,
                schedule_at=schedule_at,
                status='scheduled' if schedule_at else 'draft',
            )

            CampaignRecipient.objects.bulk_create([
                CampaignRecipient(campaign=campaign, contact=contact)
                for contact in recipients
            ])

            # Log activity
            WorkspaceActivity.log(
                workspace=workspace,
                action='campaign_created',
                target=campaign,
            )

        return campaign

    @staticmethod
    def update_campaign(
        campaign_id: UUID,
        **updates,
    ) -> Campaign:
        """
        Update an existing campaign.

        Args:
            campaign_id: UUID of campaign to update.
            **updates: Fields to update (name, template, schedule_at).

        Returns:
            Updated Campaign instance.

        Raises:
            CampaignNotFoundError: If campaign doesn't exist.
            CampaignNotEditableError: If campaign is not in draft status.
        """
        try:
            campaign = Campaign.objects.get(id=campaign_id)
        except Campaign.DoesNotExist:
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found")

        if not campaign.is_editable:
            raise CampaignNotEditableError(
                f"Campaign cannot be edited in '{campaign.status}' status"
            )

        for field, value in updates.items():
            if hasattr(campaign, field):
                setattr(campaign, field, value)

        campaign.save()
        return campaign

    @staticmethod
    def start_campaign(campaign_id: UUID) -> Campaign:
        """
        Start sending a campaign.

        Args:
            campaign_id: UUID of campaign to start.

        Returns:
            Updated Campaign instance.

        Raises:
            CampaignNotFoundError: If campaign doesn't exist.
            CampaignNotEditableError: If campaign already started.
        """
        try:
            campaign = Campaign.objects.select_related('template').get(
                id=campaign_id
            )
        except Campaign.DoesNotExist:
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found")

        if campaign.status != 'draft':
            raise CampaignNotEditableError(
                f"Cannot start campaign in '{campaign.status}' status"
            )

        campaign.status = 'sending'
        campaign.save(update_fields=['status', 'updated_at'])

        # Trigger async processing
        from .tasks import process_campaign_batch
        process_campaign_batch.delay(str(campaign.id))

        return campaign

    @staticmethod
    def pause_campaign(campaign_id: UUID) -> Campaign:
        """Pause an active campaign."""
        campaign = Campaign.objects.get(id=campaign_id)

        if campaign.status != 'sending':
            raise CampaignNotEditableError("Can only pause sending campaigns")

        campaign.status = 'paused'
        campaign.save(update_fields=['status', 'updated_at'])
        return campaign
```

---

### Selectors (Query Layer)

**DO:**
- Handle complex queries and aggregations
- Use select_related/prefetch_related
- Accept typed filter parameters
- Return QuerySets or typed results

**DON'T:**
- Modify data
- Contain business logic decisions

```python
from typing import Optional, List
from uuid import UUID
from django.db.models import QuerySet, Count, Q, F

from .models import Campaign


class CampaignSelector:
    """Selectors for campaign queries."""

    @staticmethod
    def get_workspace_campaigns(
        workspace_id: UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
        ordering: str = '-created_at',
    ) -> QuerySet[Campaign]:
        """
        Fetch campaigns for a workspace with filters.

        Args:
            workspace_id: UUID of the workspace.
            status: Filter by campaign status.
            search: Search in campaign name.
            ordering: Field to order by (prefix with - for descending).

        Returns:
            Annotated QuerySet with recipient and progress counts.
        """
        qs = Campaign.objects.filter(
            workspace_id=workspace_id
        ).select_related(
            'template',
            'workspace',
        ).annotate(
            recipient_count=Count('recipients'),
            sent_count=Count(
                'recipients',
                filter=Q(recipients__status='sent')
            ),
            failed_count=Count(
                'recipients',
                filter=Q(recipients__status='failed')
            ),
            progress=Case(
                When(recipient_count=0, then=0),
                default=F('sent_count') * 100 / F('recipient_count'),
                output_field=IntegerField(),
            ),
        )

        if status:
            qs = qs.filter(status=status)

        if search:
            qs = qs.filter(name__icontains=search)

        return qs.order_by(ordering)

    @staticmethod
    def get_campaign_with_stats(campaign_id: UUID) -> Optional[Campaign]:
        """
        Get single campaign with full statistics.

        Returns:
            Campaign with annotated stats, or None if not found.
        """
        return Campaign.objects.filter(
            id=campaign_id
        ).select_related(
            'template',
            'workspace',
        ).prefetch_related(
            'recipients__contact',
        ).annotate(
            recipient_count=Count('recipients'),
            sent_count=Count('recipients', filter=Q(recipients__status='sent')),
            opened_count=Count('recipients', filter=Q(recipients__opened_at__isnull=False)),
            clicked_count=Count('recipients', filter=Q(recipients__clicked_at__isnull=False)),
        ).first()

    @staticmethod
    def get_pending_scheduled_campaigns() -> QuerySet[Campaign]:
        """Get campaigns ready for scheduled sending."""
        from django.utils import timezone

        return Campaign.objects.filter(
            status='scheduled',
            schedule_at__lte=timezone.now(),
        ).select_related('template')
```

---

### Views (API Layer)

**DO:**
- Parse and validate request data
- Call appropriate service/selector
- Return serialized response
- Handle permissions

**DON'T:**
- Contain business logic
- Make multiple service calls for one action
- Access models directly for writes

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Campaign
from .services import CampaignService
from .selectors import CampaignSelector
from .serializers import (
    CampaignSerializer,
    CampaignCreateSerializer,
    CampaignUpdateSerializer,
)
from .permissions import HasWorkspaceAccess
from .exceptions import CampaignNotFoundError, CampaignNotEditableError


class CampaignViewSet(viewsets.ModelViewSet):
    """API endpoints for campaign management."""

    permission_classes = [IsAuthenticated, HasWorkspaceAccess]
    serializer_class = CampaignSerializer

    def get_queryset(self):
        return CampaignSelector.get_workspace_campaigns(
            workspace_id=self.request.user.current_workspace_id,
            status=self.request.query_params.get('status'),
            search=self.request.query_params.get('search'),
        )

    def create(self, request):
        serializer = CampaignCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            campaign = CampaignService.create_campaign(
                workspace=request.user.current_workspace,
                **serializer.validated_data
            )
        except (NoRecipientsError, DuplicateCampaignNameError) as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            CampaignSerializer(campaign).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None):
        serializer = CampaignUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            campaign = CampaignService.update_campaign(
                campaign_id=pk,
                **serializer.validated_data
            )
        except CampaignNotFoundError:
            return Response(
                {'detail': 'Campaign not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except CampaignNotEditableError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start sending a campaign."""
        try:
            campaign = CampaignService.start_campaign(campaign_id=pk)
        except CampaignNotFoundError:
            return Response(
                {'detail': 'Campaign not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except CampaignNotEditableError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause an active campaign."""
        try:
            campaign = CampaignService.pause_campaign(campaign_id=pk)
        except CampaignNotEditableError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(CampaignSerializer(campaign).data)
```

---

### Exceptions (Custom Errors)

```python
class CampaignError(Exception):
    """Base exception for campaign operations."""
    pass


class CampaignNotFoundError(CampaignError):
    """Campaign does not exist."""
    pass


class CampaignNotEditableError(CampaignError):
    """Campaign cannot be modified in current state."""
    pass


class NoRecipientsError(CampaignError):
    """Campaign requires at least one recipient."""
    pass


class DuplicateCampaignNameError(CampaignError):
    """Campaign name already exists in workspace."""
    pass
```

---

### Tasks (Celery Async Layer)

```python
from celery import shared_task
from django.db import transaction

from .models import Campaign, CampaignRecipient
from .services import CampaignService


@shared_task(bind=True, max_retries=3)
def process_campaign_batch(self, campaign_id: str, batch_size: int = 50):
    """
    Process a batch of campaign recipients.

    Args:
        campaign_id: UUID string of the campaign.
        batch_size: Number of emails to send per batch.
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return {'error': 'Campaign not found'}

    if campaign.status != 'sending':
        return {'status': 'skipped', 'reason': f'Campaign is {campaign.status}'}

    pending = CampaignRecipient.objects.filter(
        campaign_id=campaign_id,
        status='pending',
    ).select_related('contact')[:batch_size]

    sent = 0
    failed = 0

    for recipient in pending:
        try:
            send_campaign_email(campaign, recipient)
            recipient.status = 'sent'
            recipient.sent_at = timezone.now()
            sent += 1
        except Exception as e:
            recipient.status = 'failed'
            recipient.error_message = str(e)
            failed += 1

        recipient.save()

    # Check if more to process
    remaining = CampaignRecipient.objects.filter(
        campaign_id=campaign_id,
        status='pending',
    ).count()

    if remaining > 0:
        # Schedule next batch
        process_campaign_batch.apply_async(
            args=[campaign_id, batch_size],
            countdown=10,  # Wait 10 seconds
        )
    else:
        # Mark campaign complete
        campaign.status = 'completed'
        campaign.save(update_fields=['status', 'updated_at'])

    return {'sent': sent, 'failed': failed, 'remaining': remaining}
```

---

## Performance Patterns

### Query Optimization

```python
# BAD: N+1 queries
for campaign in Campaign.objects.all():
    print(campaign.workspace.name)  # Query per campaign!
    print(campaign.recipients.count())  # Another query per campaign!

# GOOD: Eager loading
campaigns = Campaign.objects.select_related(
    'workspace', 'template'
).prefetch_related(
    'recipients'
).annotate(
    recipient_count=Count('recipients')
)

for campaign in campaigns:
    print(campaign.workspace.name)  # No additional query
    print(campaign.recipient_count)  # Uses annotation

# GOOD: Only needed fields
Campaign.objects.only('id', 'name', 'status').filter(...)

# GOOD: values for simple data structures
Campaign.objects.values('id', 'name').filter(...)
```

### Bulk Operations

```python
# BAD: Individual creates
for contact in contacts:
    CampaignRecipient.objects.create(campaign=campaign, contact=contact)

# GOOD: Bulk create
CampaignRecipient.objects.bulk_create([
    CampaignRecipient(campaign=campaign, contact=contact)
    for contact in contacts
], batch_size=1000)

# GOOD: Bulk update
CampaignRecipient.objects.filter(
    campaign_id=campaign_id,
    status='pending'
).update(status='cancelled')
```

---

## Checklist

### Code Quality
- [ ] Type hints on all functions
- [ ] Docstrings (Google style) with Args/Returns/Raises
- [ ] Custom exceptions with clear messages
- [ ] No bare except clauses
- [ ] Transactions for multi-step operations

### Architecture
- [ ] Business logic only in services
- [ ] Complex queries in selectors
- [ ] Views are thin (< 20 lines typically)
- [ ] Models have no business logic methods

### Performance
- [ ] select_related for ForeignKey
- [ ] prefetch_related for reverse/M2M
- [ ] Indexes on filtered/ordered fields
- [ ] Bulk operations for batch creates/updates
- [ ] Pagination for list endpoints

### Testing
- [ ] Unit tests for services
- [ ] Integration tests for views
- [ ] Factories for test data (factory_boy)
- [ ] pytest-django fixtures
