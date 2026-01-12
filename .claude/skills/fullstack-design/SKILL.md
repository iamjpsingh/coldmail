---
name: fullstack-design
description: Create distinctive, production-grade full-stack applications with Django backend (service layer pattern, clean architecture) and React/TypeScript frontend (high design quality, no AI slop). Use when building web apps, APIs, components, or any full-stack feature requiring both backend logic and polished UI.
---

# Full-Stack Design Skill

Create production-grade full-stack applications combining Django's clean architecture with distinctive React/TypeScript interfaces. Every component—from database models to UI pixels—should demonstrate intentionality and craftsmanship.

---

## Design Thinking (Before Coding)

### Backend Context
- **Domain**: What business problem does this solve? What entities and relationships exist?
- **Boundaries**: Where does validation happen? What are the service boundaries?
- **Scale**: Expected data volume, query patterns, background processing needs?

### Frontend Context
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick a BOLD aesthetic: brutally minimal, maximalist, retro-futuristic, organic, luxury, playful, editorial, brutalist, art deco, soft/pastel, industrial, etc.
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose clear directions for both backend architecture and frontend aesthetics. Execute with precision.

---

## Backend Architecture (Django)

### Clean Architecture - Service Layer Pattern

```
apps/
├── {app_name}/
│   ├── models.py       # Data layer - Django ORM models only
│   ├── serializers.py  # API layer - Request/Response serialization
│   ├── views.py        # API layer - HTTP handlers (thin controllers)
│   ├── services.py     # Business layer - ALL business logic here
│   ├── selectors.py    # Query layer - Complex read operations
│   ├── permissions.py  # Auth layer - Access control
│   ├── tasks.py        # Async layer - Celery background tasks
│   ├── signals.py      # Event layer - Django signals
│   └── urls.py         # URL routing
```

### Layer Responsibilities

**Models (Data Layer)**
- ONLY data structure, relationships, properties
- NO business logic, NO validation beyond field constraints
- Use UUIDs for primary keys, timestamps for audit

```python
class Campaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'status']),
        ]
```

**Services (Business Layer)**
- ALL create/update/delete operations
- Validation, business rules, orchestration
- Side effects (emails, notifications, logging)
- Always use type hints and docstrings

```python
from typing import List, Optional
from uuid import UUID

class CampaignService:
    @staticmethod
    def create_campaign(
        workspace: Workspace,
        name: str,
        template: EmailTemplate,
        recipients: List[Contact],
        schedule_at: Optional[datetime] = None,
    ) -> Campaign:
        """
        Create a new campaign with validation.

        Args:
            workspace: The workspace owning this campaign.
            name: Campaign name (must be unique per workspace).
            template: Email template to use.
            recipients: List of contacts to receive emails.
            schedule_at: Optional scheduled send time.

        Returns:
            The created Campaign instance.

        Raises:
            ValidationError: If no recipients provided.
            DuplicateNameError: If campaign name exists in workspace.
        """
        if not recipients:
            raise ValidationError("At least one recipient required")

        if Campaign.objects.filter(workspace=workspace, name=name).exists():
            raise DuplicateNameError(f"Campaign '{name}' already exists")

        campaign = Campaign.objects.create(
            workspace=workspace,
            name=name,
            template=template,
            schedule_at=schedule_at,
        )

        CampaignRecipient.objects.bulk_create([
            CampaignRecipient(campaign=campaign, contact=c)
            for c in recipients
        ])

        return campaign
```

**Selectors (Query Layer)**
- Complex queries, aggregations, filtering
- Optimize with select_related/prefetch_related
- Return querysets or typed results

```python
class CampaignSelector:
    @staticmethod
    def get_workspace_campaigns(
        workspace_id: UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> QuerySet[Campaign]:
        """Fetch campaigns with optimized related data."""
        qs = Campaign.objects.filter(
            workspace_id=workspace_id
        ).select_related(
            'template', 'workspace'
        ).prefetch_related(
            'recipients__contact'
        ).annotate(
            recipient_count=Count('recipients'),
            sent_count=Count('recipients', filter=Q(recipients__status='sent')),
        )

        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(name__icontains=search)

        return qs
```

**Views (API Layer)**
- Parse request → Call service/selector → Return response
- Keep THIN - no business logic
- Use serializers for validation

```python
class CampaignViewSet(viewsets.ModelViewSet):
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

        campaign = CampaignService.create_campaign(
            workspace=request.user.current_workspace,
            **serializer.validated_data
        )

        return Response(
            CampaignSerializer(campaign).data,
            status=status.HTTP_201_CREATED
        )
```

### Backend Anti-Patterns

NEVER do these:
- Business logic in models or views
- N+1 queries (always use select_related/prefetch_related)
- Bare except clauses
- Missing type hints
- Validation in serializers that belongs in services
- Fat views with 50+ lines of logic

---

## Frontend Architecture (React/TypeScript)

### Component Structure

```
src/
├── api/                # API client functions
├── components/
│   ├── ui/             # Reusable UI primitives (shadcn/ui)
│   └── {feature}/      # Feature-specific components
├── hooks/              # Custom React hooks (data fetching)
├── pages/              # Route-level containers
├── types/              # TypeScript interfaces
├── lib/                # Utilities
└── stores/             # Global state (Zustand)
```

### Type Safety (Strict Mode)

```typescript
// ALWAYS explicit types - NEVER 'any'
interface Campaign {
  id: string;
  name: string;
  status: 'draft' | 'scheduled' | 'sending' | 'completed';
  recipientCount: number;
  sentCount: number;
  createdAt: string;
}

// Discriminated unions for state
type RequestState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

// Props with JSDoc
interface CampaignCardProps {
  /** The campaign to display */
  campaign: Campaign;
  /** Called when campaign is selected */
  onSelect?: (id: string) => void;
}
```

### Custom Hooks Pattern

```typescript
// Encapsulate ALL data fetching in hooks
export function useCampaigns(options?: { status?: string }) {
  return useQuery({
    queryKey: ['campaigns', options],
    queryFn: () => campaignsApi.list(options),
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: campaignsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      toast({ title: 'Campaign created successfully' });
    },
    onError: (error) => {
      toast({
        title: 'Error creating campaign',
        description: handleApiError(error),
        variant: 'destructive',
      });
    },
  });
}
```

---

## Frontend Aesthetics

### Typography
- Choose DISTINCTIVE fonts - avoid Inter, Roboto, Arial, system fonts
- Pair a bold display font with refined body text
- Examples: Space Grotesk + Söhne, Clash Display + Satoshi, Cabinet Grotesk + General Sans

### Color & Theme
- Commit to a cohesive aesthetic using CSS variables
- Dominant colors with sharp accents > timid, evenly-distributed palettes
- AVOID: purple gradients on white (overused AI aesthetic)

### Motion & Animation
- CSS-only for HTML, Motion library for React
- Focus on high-impact moments: page load with staggered reveals
- Scroll-triggered animations and surprising hover states

### Spatial Composition
- Unexpected layouts, asymmetry, overlap, diagonal flow
- Grid-breaking elements
- Generous negative space OR controlled density

### Visual Details
- Gradient meshes, noise textures, geometric patterns
- Layered transparencies, dramatic shadows
- Custom cursors, decorative borders, grain overlays

### Anti-Patterns to Avoid
NEVER use generic AI aesthetics:
- Overused fonts (Inter, Roboto, Arial)
- Cliched purple gradients
- Predictable layouts
- Cookie-cutter components lacking context-specific character

---

## Page Template

```typescript
export default function CampaignsPage() {
  const { data: campaigns, isLoading, error } = useCampaigns();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error loading campaigns</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Campaigns</h1>
          <p className="text-muted-foreground">
            Create and manage your email campaigns.
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Campaign
        </Button>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : campaigns?.length === 0 ? (
        <EmptyState
          icon={<Mail className="h-12 w-12" />}
          title="No campaigns yet"
          description="Create your first campaign to start reaching your audience."
          action={
            <Button onClick={() => setIsCreateOpen(true)}>
              Create Campaign
            </Button>
          }
        />
      ) : (
        <CampaignList campaigns={campaigns} />
      )}

      <CreateCampaignDialog
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
      />
    </div>
  );
}
```

---

## Quality Checklist

### Backend
- [ ] All business logic in services.py
- [ ] Type hints on all functions
- [ ] Docstrings with Args/Returns/Raises
- [ ] No N+1 queries (use select_related/prefetch_related)
- [ ] Custom exceptions with clear messages
- [ ] Database indexes on filtered fields

### Frontend
- [ ] Strict TypeScript (no `any`)
- [ ] Data fetching in custom hooks
- [ ] Loading, error, and empty states
- [ ] Accessible (proper ARIA, keyboard nav)
- [ ] Distinctive design (not generic AI aesthetic)
- [ ] Responsive (mobile-first)

### Integration
- [ ] API types match between frontend/backend
- [ ] Error handling end-to-end
- [ ] Optimistic updates where appropriate
- [ ] Proper loading states during mutations

---

## Remember

**Backend**: Clean architecture is about separation of concerns. Models hold data. Services hold logic. Views are thin adapters. Every layer has one job.

**Frontend**: Claude is capable of extraordinary creative work. Don't hold back—show what can be created when thinking outside the box and committing fully to a distinctive vision.

Both layers should feel intentional, crafted, and production-ready.
