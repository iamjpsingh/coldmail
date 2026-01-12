# ColdMail Development Guidelines

> A comprehensive guide for AI-assisted full-stack development following Anthropic's best practices.

## Project Overview

**ColdMail** is an open-source, self-hosted cold email platform built with Django 5.2 LTS (backend) and React 19 + TypeScript (frontend).

### Tech Stack
- **Backend**: Django 5.2 LTS, Django REST Framework, Celery, PostgreSQL 16, Redis 7
- **Frontend**: React 19, TypeScript 5.x, TanStack Query, Tailwind CSS v4, shadcn/ui
- **Infrastructure**: Docker, Nginx, GitHub Actions

---

## Architecture Principles

### Clean Architecture (Backend)

Follow the **Service Layer Pattern** to separate concerns:

```
apps/
├── {app_name}/
│   ├── models.py       # Data layer - Django ORM models only
│   ├── serializers.py  # API layer - Request/Response serialization
│   ├── views.py        # API layer - HTTP handlers (thin controllers)
│   ├── services.py     # Business layer - All business logic here
│   ├── selectors.py    # Query layer - Complex read operations
│   ├── permissions.py  # Auth layer - Access control
│   ├── tasks.py        # Async layer - Celery background tasks
│   ├── signals.py      # Event layer - Django signals
│   ├── admin.py        # Admin interface
│   └── urls.py         # URL routing
```

**Rules:**
- **Models**: Only data structure, relationships, and simple properties. No business logic.
- **Services**: All create/update/delete operations. Validation, business rules, orchestration.
- **Selectors**: Complex queries, aggregations, filtering logic.
- **Views**: Parse request → Call service/selector → Return response. Keep thin.
- **Serializers**: Input validation and output formatting only.

### Component Architecture (Frontend)

Follow the **Container-Presentational Pattern**:

```
src/
├── api/                # API client functions
├── components/
│   ├── ui/             # Reusable UI primitives (shadcn/ui)
│   └── {feature}/      # Feature-specific components
├── hooks/              # Custom React hooks
├── pages/              # Route-level components (containers)
├── types/              # TypeScript type definitions
├── lib/                # Utilities and helpers
└── stores/             # Global state (Zustand)
```

**Rules:**
- **Pages**: Handle data fetching, state, routing. Compose from smaller components.
- **Components**: Receive props, render UI. Minimal internal state.
- **Hooks**: Encapsulate reusable logic, API calls, side effects.
- **Types**: Single source of truth for all TypeScript interfaces.

---

## Coding Standards

### Python (Django)

#### Naming Conventions
```python
# Classes: PascalCase
class EmailAccount(models.Model):
    pass

class EmailAccountSerializer(serializers.ModelSerializer):
    pass

# Functions/methods: snake_case
def send_campaign_emails(campaign_id: str) -> None:
    pass

# Constants: SCREAMING_SNAKE_CASE
MAX_EMAILS_PER_DAY = 500
DEFAULT_BATCH_SIZE = 50

# Private methods: leading underscore
def _calculate_score(self) -> int:
    pass
```

#### Type Hints (Required)
```python
from typing import Optional, List, Dict, Any
from uuid import UUID

def get_contacts_by_tags(
    workspace_id: UUID,
    tag_ids: List[UUID],
    limit: Optional[int] = None
) -> List[Contact]:
    """Fetch contacts that have any of the specified tags."""
    pass
```

#### Docstrings (Google Style)
```python
def process_campaign(campaign_id: str, batch_size: int = 50) -> dict:
    """
    Process a campaign by sending emails in batches.

    Args:
        campaign_id: The UUID of the campaign to process.
        batch_size: Number of emails per batch. Defaults to 50.

    Returns:
        A dict containing 'sent', 'failed', and 'remaining' counts.

    Raises:
        CampaignNotFoundError: If campaign doesn't exist.
        CampaignAlreadyCompleteError: If campaign is already finished.
    """
    pass
```

#### Service Layer Pattern
```python
# services.py - All business logic here
class CampaignService:
    @staticmethod
    def create_campaign(
        workspace: Workspace,
        name: str,
        template: EmailTemplate,
        recipients: List[Contact],
        **options
    ) -> Campaign:
        """Create a new campaign with validation."""
        # Validate
        if not recipients:
            raise ValidationError("At least one recipient required")

        # Create
        campaign = Campaign.objects.create(
            workspace=workspace,
            name=name,
            template=template,
            **options
        )

        # Side effects
        CampaignRecipient.objects.bulk_create([
            CampaignRecipient(campaign=campaign, contact=c)
            for c in recipients
        ])

        # Log activity
        WorkspaceActivity.objects.create(
            workspace=workspace,
            action='campaign_created',
            target_id=str(campaign.id),
            target_name=campaign.name
        )

        return campaign
```

#### Query Optimization
```python
# BAD: N+1 queries
for contact in Contact.objects.all():
    print(contact.tags.all())  # Query per contact!

# GOOD: Prefetch related
contacts = Contact.objects.prefetch_related('tags').all()
for contact in contacts:
    print(contact.tags.all())  # No additional queries

# GOOD: Select only needed fields
Contact.objects.only('id', 'email', 'first_name').filter(...)

# GOOD: Use values/values_list for simple data
emails = Contact.objects.values_list('email', flat=True)
```

### TypeScript (React)

#### Naming Conventions
```typescript
// Components: PascalCase
function ContactCard({ contact }: ContactCardProps) {}

// Hooks: camelCase with 'use' prefix
function useContacts(workspaceId: string) {}

// Types/Interfaces: PascalCase
interface Contact {
  id: string;
  email: string;
  firstName: string;
}

// Props interfaces: ComponentNameProps
interface ContactCardProps {
  contact: Contact;
  onSelect?: (id: string) => void;
}

// Constants: SCREAMING_SNAKE_CASE
const MAX_RETRIES = 3;
const API_BASE_URL = '/api/v1';

// Event handlers: handleEventName
const handleClick = () => {};
const handleSubmit = (data: FormData) => {};
```

#### Type Safety (Strict Mode)
```typescript
// Always use explicit types - never 'any'
// BAD
const data: any = response.data;

// GOOD
interface ApiResponse<T> {
  data: T;
  status: string;
}
const data: ApiResponse<Contact[]> = response.data;

// Use discriminated unions for state
type RequestState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

// Use 'unknown' instead of 'any' when type is truly unknown
function handleError(error: unknown) {
  if (error instanceof Error) {
    console.error(error.message);
  }
}
```

#### Component Patterns
```typescript
// Props interface with JSDoc
interface ButtonProps {
  /** Button label text */
  children: React.ReactNode;
  /** Visual style variant */
  variant?: 'primary' | 'secondary' | 'destructive';
  /** Disabled state */
  disabled?: boolean;
  /** Click handler */
  onClick?: () => void;
}

// Functional component with defaults
function Button({
  children,
  variant = 'primary',
  disabled = false,
  onClick,
}: ButtonProps) {
  return (
    <button
      className={cn('btn', `btn-${variant}`)}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

// Use React.memo for expensive renders
const ExpensiveList = React.memo(function ExpensiveList({ items }: Props) {
  return items.map(item => <Item key={item.id} {...item} />);
});
```

#### Custom Hooks Pattern
```typescript
// Encapsulate all data fetching in hooks
export function useContacts(options?: { search?: string }) {
  return useQuery({
    queryKey: ['contacts', options],
    queryFn: () => contactsApi.list(options),
  });
}

export function useCreateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: contactsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
    },
  });
}

// Compose hooks for complex logic
export function useContactWithTags(contactId: string) {
  const contact = useContact(contactId);
  const tags = useTags();

  const contactTags = useMemo(() => {
    if (!contact.data || !tags.data) return [];
    return tags.data.filter(t => contact.data.tagIds.includes(t.id));
  }, [contact.data, tags.data]);

  return { contact, tags: contactTags };
}
```

---

## Code Quality Rules

### DRY (Don't Repeat Yourself)

```typescript
// BAD: Repeated logic
function ContactPage() {
  const formatDate = (date: string) => new Date(date).toLocaleDateString();
  // ...
}

function CampaignPage() {
  const formatDate = (date: string) => new Date(date).toLocaleDateString();
  // ...
}

// GOOD: Extract to utility
// lib/utils.ts
export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString();
}

// Usage
import { formatDate } from '@/lib/utils';
```

### Single Responsibility

```python
# BAD: View doing too much
class CampaignViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # 50 lines of validation, creation, email sending, logging...
        pass

# GOOD: Delegate to service
class CampaignViewSet(viewsets.ModelViewSet):
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        campaign = CampaignService.create_campaign(
            workspace=request.user.current_workspace,
            **serializer.validated_data
        )

        return Response(
            CampaignSerializer(campaign).data,
            status=status.HTTP_201_CREATED
        )
```

### Error Handling

```python
# Backend: Custom exceptions
class CampaignError(Exception):
    """Base exception for campaign operations."""
    pass

class CampaignNotFoundError(CampaignError):
    """Campaign does not exist."""
    pass

class CampaignAlreadyStartedError(CampaignError):
    """Cannot modify a started campaign."""
    pass

# Service usage
def start_campaign(campaign_id: str) -> Campaign:
    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")

    if campaign.status != 'draft':
        raise CampaignAlreadyStartedError("Campaign already started")

    # ...
```

```typescript
// Frontend: Typed error handling
interface ApiError {
  detail?: string;
  errors?: Record<string, string[]>;
}

function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const apiError = error.response?.data as ApiError;
    return apiError?.detail || 'An unexpected error occurred';
  }
  return 'An unexpected error occurred';
}

// Usage in mutations
const createCampaign = useCreateCampaign();

const handleSubmit = async (data: FormData) => {
  try {
    await createCampaign.mutateAsync(data);
    toast({ title: 'Campaign created' });
  } catch (error) {
    toast({
      title: 'Error',
      description: handleApiError(error),
      variant: 'destructive'
    });
  }
};
```

---

## UI/UX Standards

### Design System (shadcn/ui + Tailwind)

#### Color Usage
```typescript
// Use semantic colors from design system
// Primary actions
<Button variant="default">Save</Button>

// Destructive actions
<Button variant="destructive">Delete</Button>

// Secondary/Cancel actions
<Button variant="outline">Cancel</Button>
<Button variant="ghost">Dismiss</Button>

// Status indicators
<Badge variant="default">Active</Badge>      // Primary
<Badge variant="secondary">Draft</Badge>     // Muted
<Badge variant="destructive">Failed</Badge>  // Error
<Badge className="bg-green-500">Success</Badge>
<Badge className="bg-yellow-500">Warning</Badge>
```

#### Spacing & Layout
```typescript
// Use consistent spacing scale
// space-y-{1,2,3,4,6,8} for vertical
// space-x-{1,2,3,4,6,8} for horizontal
// gap-{1,2,3,4,6,8} for grid/flex

// Page layout
<div className="space-y-6">
  <PageHeader />
  <StatsCards />
  <DataTable />
</div>

// Card layout
<Card>
  <CardHeader className="pb-3">
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent className="space-y-4">
    {/* Content */}
  </CardContent>
</Card>

// Form layout
<form className="space-y-4">
  <div className="grid gap-4 md:grid-cols-2">
    <FormField />
    <FormField />
  </div>
  <Button type="submit">Submit</Button>
</form>
```

#### Component Consistency
```typescript
// Page structure template
export default function FeaturePage() {
  return (
    <div className="space-y-6">
      {/* Header with title and actions */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Page Title</h1>
          <p className="text-muted-foreground">
            Brief description of this page.
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add New
        </Button>
      </div>

      {/* Stats cards (optional) */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard title="Total" value={100} />
        {/* ... */}
      </div>

      {/* Main content */}
      <Card>
        <CardHeader>
          <CardTitle>Content Title</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Table, form, or other content */}
        </CardContent>
      </Card>
    </div>
  );
}
```

#### Loading & Empty States
```typescript
// Loading state
{isLoading && (
  <div className="flex items-center justify-center h-64">
    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
  </div>
)}

// Empty state
{!isLoading && items.length === 0 && (
  <Card>
    <CardContent className="flex flex-col items-center justify-center py-12">
      <Inbox className="h-12 w-12 text-muted-foreground mb-4" />
      <h3 className="text-lg font-medium">No items yet</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Get started by creating your first item.
      </p>
      <Button>
        <Plus className="mr-2 h-4 w-4" />
        Create Item
      </Button>
    </CardContent>
  </Card>
)}

// Error state
{error && (
  <Alert variant="destructive">
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>Error</AlertTitle>
    <AlertDescription>{error.message}</AlertDescription>
  </Alert>
)}
```

#### Responsive Design
```typescript
// Mobile-first responsive classes
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Cards */}
</div>

// Hidden on mobile
<div className="hidden md:block">Desktop only</div>

// Show on mobile only
<div className="md:hidden">Mobile only</div>

// Responsive table
<div className="overflow-x-auto">
  <Table>...</Table>
</div>
```

---

## Testing Standards

### Backend Testing
```python
# tests/test_services.py
import pytest
from apps.campaigns.services import CampaignService

@pytest.mark.django_db
class TestCampaignService:
    def test_create_campaign_success(self, workspace, template, contacts):
        campaign = CampaignService.create_campaign(
            workspace=workspace,
            name="Test Campaign",
            template=template,
            recipients=contacts,
        )

        assert campaign.name == "Test Campaign"
        assert campaign.recipients.count() == len(contacts)

    def test_create_campaign_no_recipients_fails(self, workspace, template):
        with pytest.raises(ValidationError) as exc:
            CampaignService.create_campaign(
                workspace=workspace,
                name="Test",
                template=template,
                recipients=[],
            )

        assert "at least one recipient" in str(exc.value).lower()
```

### Frontend Testing
```typescript
// components/__tests__/ContactCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ContactCard } from '../ContactCard';

describe('ContactCard', () => {
  const mockContact = {
    id: '1',
    email: 'test@example.com',
    firstName: 'John',
    lastName: 'Doe',
  };

  it('renders contact information', () => {
    render(<ContactCard contact={mockContact} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    const onSelect = jest.fn();
    render(<ContactCard contact={mockContact} onSelect={onSelect} />);

    fireEvent.click(screen.getByRole('button'));

    expect(onSelect).toHaveBeenCalledWith('1');
  });
});
```

---

## Git & Workflow

### Branch Naming
```
feature/add-campaign-scheduling
bugfix/fix-email-tracking-pixel
hotfix/security-patch-auth
refactor/cleanup-contact-service
docs/update-api-documentation
```

### Commit Messages
```
feat(campaigns): add scheduled sending support

- Add schedule_at field to Campaign model
- Create Celery task for scheduled sending
- Add scheduling UI in campaign dialog

Closes #123
```

```
fix(tracking): prevent duplicate open events

The tracking pixel was being triggered multiple times
when email clients prefetched images. Added deduplication
based on recipient + timestamp window.

Fixes #456
```

### PR Description Template
```markdown
## Summary
Brief description of changes (1-3 bullet points)

## Changes
- Detailed change 1
- Detailed change 2

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] API documentation updated

## Screenshots (if UI changes)
```

---

## Commands

### Backend
```bash
# Start development server
cd backend && source venv/bin/activate
DATABASE_URL="postgres://coldmail:coldmail_dev_password@localhost:5432/coldmail" \
python manage.py runserver

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
pytest

# Run specific test
pytest apps/campaigns/tests/test_services.py -v

# Celery worker
celery -A coldmail worker -l info

# Celery beat
celery -A coldmail beat -l info
```

### Frontend
```bash
# Start development server
cd frontend && pnpm dev

# Build for production
pnpm build

# Type check
pnpm tsc --noEmit

# Lint
pnpm lint

# Run tests
pnpm test
```

### Docker
```bash
# Start databases (PostgreSQL + Redis)
docker-compose -f docker-compose.dev.yml up -d

# Stop databases
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Production build
docker-compose up -d --build
```

---

## Security Checklist

- [ ] Never commit secrets (.env, API keys, passwords)
- [ ] Use environment variables for all sensitive config
- [ ] Validate all user input (backend AND frontend)
- [ ] Use parameterized queries (Django ORM handles this)
- [ ] Implement rate limiting on sensitive endpoints
- [ ] Use HTTPS in production
- [ ] Set secure cookie flags
- [ ] Implement CSRF protection
- [ ] Sanitize HTML output to prevent XSS
- [ ] Keep dependencies updated

---

## Performance Checklist

### Backend
- [ ] Use `select_related()` and `prefetch_related()` to avoid N+1
- [ ] Use `only()` and `defer()` for large models
- [ ] Index frequently queried fields
- [ ] Use database-level pagination
- [ ] Cache expensive computations with Redis
- [ ] Use Celery for heavy background tasks

### Frontend
- [ ] Use React.memo() for expensive components
- [ ] Use useMemo() and useCallback() appropriately
- [ ] Implement code splitting with React.lazy()
- [ ] Use virtualization for long lists (react-window)
- [ ] Optimize images (WebP, lazy loading)
- [ ] Minimize bundle size (tree shaking, dynamic imports)

---

## File Templates

When creating new features, use these patterns:

### New Django App
```bash
python manage.py startapp new_feature
# Then add to apps/ directory and INSTALLED_APPS
```

### New React Page
```typescript
// pages/new-feature/index.tsx
import { useState } from 'react';
import { useNewFeature } from '@/hooks/use-new-feature';
// ... standard page template
```

### New API Endpoint
```python
# views.py
class NewFeatureViewSet(viewsets.ModelViewSet):
    # ... standard viewset pattern

# urls.py
router.register('new-features', NewFeatureViewSet)
```

---

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Documentation](https://react.dev/)
- [TanStack Query](https://tanstack.com/query)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
