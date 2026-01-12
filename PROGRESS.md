# ColdMail Development Progress

## Overview
Open source, self-hosted cold email platform

## Tech Stack
- **Backend**: Django 5.2 LTS + DRF + Celery + Redis + PostgreSQL
- **Frontend**: React 19 + TypeScript + TanStack Query + Tailwind v4 + shadcn/ui
- **Package Manager**: pnpm (frontend), pip (backend)
- **Database**: PostgreSQL 16 + Redis 7
- **Deploy**: Docker Compose

---

## Development Phases

### Phase 1: Foundation (COMPLETED)
- [x] Project setup (Django, React, Docker)
- [x] Python virtual environment setup
- [x] Django 5.2 LTS installed with DRF, Celery, allauth
- [x] Custom User model with UUID
- [x] Basic React setup with Vite + TypeScript
- [x] TanStack Query, axios, react-router-dom, zustand installed
- [x] Tailwind CSS v4 configured
- [x] shadcn/ui component library (Button, Card, Input, Label)
- [x] Docker development environment (docker-compose.dev.yml)
- [x] Docker production environment (docker-compose.yml)
- [x] Nginx configuration
- [x] Makefile with common commands
- [x] Environment files (.env, .env.example)
- [ ] CI/CD pipeline setup

### Phase 2: Email Infrastructure (COMPLETED)
- [x] Email account model (SMTP, OAuth)
- [x] Workspace model for team collaboration
- [x] SMTP provider support
- [x] Connection testing (SMTP/IMAP)
- [x] Account health monitoring
- [x] Daily/hourly limit tracking
- [x] Email warmup system
- [x] Email sending service
- [x] Email account API endpoints
- [x] Gmail OAuth integration
- [x] Microsoft OAuth integration
- [x] Email account UI (page, cards, add dialog, test email)

### Phase 3: Contacts System (COMPLETED)
- [x] Contact model with custom fields
- [x] Tags system
- [x] Contact lists (static and smart)
- [x] Import from CSV/Excel/JSON
- [x] Export functionality
- [x] Advanced search and filtering
- [x] Bulk operations (delete, add tags, add to list)
- [x] Contacts UI (table, add dialog, import wizard)
- [x] Custom fields model
- [x] Contact activity tracking
- [x] Celery task for import processing

### Phase 4: Contact Scoring (COMPLETED)
- [x] Scoring engine
- [x] Scoring rules configuration
- [x] Score history tracking
- [x] Hot/Warm/Cold classification
- [x] Score decay job
- [x] Hot leads dashboard
- [x] Scoring settings UI

### Phase 5: Templates & Composer (COMPLETED)
- [x] Email template model
- [x] Rich text editor (TipTap)
- [x] Variable system {{firstName}}
- [x] Spintax support
- [x] Template preview
- [x] Signature management
- [x] Templates UI

### Phase 6: Campaigns (COMPLETED)
- [x] Campaign model
- [x] Recipient selection
- [x] Sending queue (Celery)
- [x] Random delay between emails
- [x] Batch sending with delays
- [x] Schedule sending
- [x] Spread across time window
- [x] Respect limits
- [x] Pause/resume/cancel
- [x] A/B testing
- [x] Campaign UI

### Phase 7: Tracking (COMPLETED)
- [x] Open tracking (pixel)
- [x] Click tracking (redirect)
- [x] Event storage
- [x] Device/location detection
- [x] Bot filtering
- [x] Score awarding on events
- [x] Real-time updates
- [x] Unsubscribe handling
- [x] Bounce handling

### Phase 8: Reports & Dashboard (COMPLETED)
- [x] Dashboard statistics
- [x] Campaign reports
- [x] Activity timeline
- [x] Performance charts
- [x] Hot leads report
- [x] Score distribution
- [x] Export to CSV/Excel/PDF
- [x] Reports UI

### Phase 9: Sequences (COMPLETED)
- [x] Sequence model
- [x] Step builder (email, delay, tag, webhook, condition, task)
- [x] Delay configuration (minutes, hours, days, weeks)
- [x] Stop conditions (reply, click, open, unsubscribe, bounce, score threshold)
- [x] Enrollment management
- [x] Sequence engine (Celery)
- [x] Sequence analytics
- [x] Sequences UI

### Phase 10: Website Tracking (COMPLETED)
- [x] Tracking domain setup
- [x] JavaScript snippet generator
- [x] Visitor tracking models
- [x] Page view recording
- [x] Session management
- [x] IP-to-contact matching
- [x] Score awarding for visits
- [x] Company enrichment fields
- [x] Visitors UI

### Phase 11: API & Webhooks (COMPLETED)
- [x] REST API (all endpoints)
- [x] API key authentication
- [x] Rate limiting
- [x] Webhook system
- [x] Event dispatching
- [x] HMAC signing
- [x] Delivery logs
- [x] Retry logic
- [x] API documentation (Swagger)

### Phase 12: Integrations (COMPLETED)
- [x] Integration framework
- [x] Slack notifications
- [x] Discord notifications
- [x] HubSpot sync
- [x] Salesforce sync
- [x] Google Sheets export
- [x] n8n compatibility (via webhooks)
- [x] Zapier webhooks (via webhooks)

### Phase 13: Teams & Polish (COMPLETED)
- [x] Workspace/team model extensions
- [x] Role-based access control (RBAC)
- [x] Member invitations system
- [x] Activity logging (audit trail)
- [x] Team settings page
- [x] Workspace settings page
- [ ] Documentation
- [ ] Performance optimization

---

## Current Status

### Phase 1: Foundation - COMPLETED

**Backend:**
- [x] Django 5.2 LTS with all dependencies
- [x] Project structure with 9 apps (core, users, workspaces, email_accounts, contacts, campaigns, sequences, tracking, webhooks)
- [x] Custom User model with UUID primary key
- [x] Settings split into base/development/production/testing
- [x] Celery configuration for background tasks
- [x] Database migrations applied (SQLite for dev)
- [x] API documentation endpoints (/api/docs/, /api/redoc/)
- [x] Health check endpoint (/health/)

**Frontend:**
- [x] React 19 with Vite + TypeScript
- [x] pnpm package manager
- [x] TanStack Query for data fetching
- [x] axios for HTTP requests
- [x] react-router-dom for routing
- [x] zustand for state management
- [x] Tailwind CSS v4 with custom theme
- [x] shadcn/ui components (Button, Card, Input, Label)
- [x] Radix UI primitives installed
- [x] Path aliases configured (@/)

**Infrastructure:**
- [x] docker-compose.dev.yml (PostgreSQL + Redis)
- [x] docker-compose.yml (production stack)
- [x] Dockerfile for backend (dev + prod)
- [x] nginx.conf with SSL, rate limiting
- [x] Makefile with development commands
- [x] .env and .env.example files
- [x] .gitignore configured

### Phase 2: Email Infrastructure - COMPLETED

**Backend:**
- [x] EmailAccount model with SMTP/OAuth configuration
- [x] EmailAccountLog model for activity tracking
- [x] Workspace and WorkspaceMember models
- [x] EmailService for SMTP operations (send, test connection)
- [x] GoogleOAuthService (authorization, token exchange, refresh, send)
- [x] MicrosoftOAuthService (authorization, token exchange, refresh, send)
- [x] EmailAccountViewSet with actions (test_connection, send_test_email, pause, resume, start_warmup, stop_warmup, logs, stats)
- [x] OAuth endpoints (Google, Microsoft)
- [x] Email account serializers
- [x] OAuth dependencies installed (google-auth, msal, requests)

**Frontend:**
- [x] API client with axios (token refresh, auth interceptor)
- [x] Email accounts API client
- [x] React Query hooks for email accounts
- [x] Email accounts page with stats cards
- [x] Email account card component (pause/resume, warmup, test)
- [x] Add email account dialog (OAuth + SMTP tabs)
- [x] Test email dialog
- [x] Dashboard layout with sidebar navigation
- [x] Additional UI components (Dialog, DropdownMenu, Badge, Textarea, Tabs)
- [x] TypeScript types for email accounts

### Phase 3: Contacts System - COMPLETED

**Backend:**
- [x] Contact model with custom fields, scoring, engagement metrics
- [x] Tag model with workspace scoping
- [x] ContactList model (static and smart lists with filter criteria)
- [x] ContactActivity model for activity tracking
- [x] CustomField model for user-defined fields
- [x] ImportJob model for tracking imports
- [x] Contact serializers with nested tags
- [x] ContactViewSet with search, bulk operations, export
- [x] TagViewSet, ContactListViewSet, CustomFieldViewSet
- [x] ImportJobViewSet with file upload, preview, field mapping
- [x] Celery task for async import processing (CSV, Excel, JSON)
- [x] Database migrations applied

**Frontend:**
- [x] Contact TypeScript types
- [x] Contacts API client (contacts, tags, lists, imports)
- [x] React Query hooks for all contact operations
- [x] Contacts page with stats cards
- [x] Contacts table with selection, actions
- [x] Add contact dialog
- [x] Import contacts wizard (upload, mapping, progress, complete)
- [x] Search and filtering

### Phase 4: Contact Scoring - COMPLETED

**Backend:**
- [x] ScoringRule model with event types, conditions, cooldown, max applications
- [x] ScoreHistory model for tracking all score changes
- [x] ScoreThreshold model for hot/warm/cold classification
- [x] ScoreDecayConfig model for automatic score decay
- [x] ScoringEngine service with full scoring logic
- [x] apply_event method for rule-based scoring
- [x] set_score and adjust_score methods for manual adjustments
- [x] get_classification method for hot/warm/cold determination
- [x] get_hot_leads method for retrieving top leads
- [x] run_score_decay method for automatic decay processing
- [x] get_score_stats method for scoring statistics
- [x] Scoring serializers (ScoringRule, ScoreHistory, ScoreThreshold, ScoreDecayConfig)
- [x] ScoringRuleViewSet with toggle_active action
- [x] ScoreThresholdViewSet for threshold management
- [x] ScoreDecayConfigViewSet with run_now action
- [x] ScoringViewSet with stats, hot_leads, adjust_score, apply_event, score_history endpoints
- [x] Celery tasks for scoring (run_score_decay_all_workspaces, apply_scoring_event, bulk_apply_scoring_event, recalculate_all_scores)

**Frontend:**
- [x] Scoring TypeScript types (ScoringRule, ScoreHistory, ScoreThreshold, ScoreDecayConfig, ScoringStats)
- [x] Scoring API client (scoringRulesApi, scoreThresholdsApi, scoreDecayApi, scoringApi)
- [x] React Query hooks for all scoring operations
- [x] Scoring settings page with stats cards
- [x] Scoring rules table with enable/disable and delete actions
- [x] Add scoring rule dialog with conditions
- [x] Thresholds settings component
- [x] Decay settings component
- [x] Switch, Select, and Table UI components

### Phase 5: Templates & Composer - COMPLETED

**Backend:**
- [x] EmailTemplate model with categories, variables tracking, spintax detection
- [x] EmailSignature model with default signature support
- [x] TemplateFolder model for organizing templates
- [x] TemplateVersion model for version history
- [x] SnippetLibrary model for reusable text snippets
- [x] TemplateEngine service with variable and spintax processing
- [x] Variable extraction ({{variable}} syntax with fallback support)
- [x] Spintax processing ({option1|option2|option3} syntax)
- [x] Template preview with sample data
- [x] Template validation
- [x] HTML to plain text conversion
- [x] EmailTemplateViewSet with preview, validate, duplicate, versions actions
- [x] EmailSignatureViewSet with set_default action
- [x] TemplateFolderViewSet with template management actions
- [x] SnippetLibraryViewSet with categories and usage tracking
- [x] Database migrations applied

**Frontend:**
- [x] Template TypeScript types (EmailTemplate, EmailSignature, TemplateFolder, Snippet, etc.)
- [x] Templates API client (templates, signatures, folders, snippets)
- [x] React Query hooks for all template operations
- [x] TipTap rich text editor with toolbar
- [x] Variable insertion support in editor
- [x] Templates page with stats cards and category filtering
- [x] Add template dialog with TipTap editor
- [x] Template preview dialog with spintax shuffling
- [x] Popover UI component

### Phase 6: Campaigns - COMPLETED

**Backend:**
- [x] Campaign model with full configuration (sending mode, delays, scheduling, A/B testing)
- [x] ABTestVariant model for A/B test variants
- [x] CampaignRecipient model for tracking individual recipients
- [x] CampaignEvent model for tracking opens, clicks, etc.
- [x] CampaignLog model for audit logging
- [x] CampaignService for campaign operations (prepare, schedule, send, pause, resume, cancel)
- [x] Recipient preparation from lists/tags with exclusion support
- [x] Personalized content rendering per recipient
- [x] Spread sending across time windows
- [x] Random delays between emails
- [x] Batch sending with configurable batch size and delay
- [x] A/B variant assignment and winner selection
- [x] Integration with EmailService for actual sending
- [x] Celery tasks for async campaign processing
- [x] CampaignViewSet with all actions (prepare, schedule, start, pause, resume, cancel, duplicate, stats, recipients, logs, events)
- [x] Full REST API for campaigns

**Frontend:**
- [x] Campaign TypeScript types
- [x] Campaigns API client
- [x] React Query hooks for all campaign operations
- [x] Campaigns page with summary stats
- [x] Campaign list with status badges and progress indicators
- [x] Add campaign dialog with 3-step wizard (basics, content, options)
- [x] Campaign detail dialog with overview, recipients, content, and activity tabs
- [x] A/B test variant display with winner indicator
- [x] Campaign actions (start, pause, resume, cancel, duplicate, delete)
- [x] Progress UI component
- [x] Updated sidebar navigation with Campaigns at top

### Phase 7: Tracking - COMPLETED

**Backend:**
- [x] TrackingDomain model for custom tracking domains
- [x] TrackingLink model for click tracking
- [x] TrackingPixel model for open tracking
- [x] UnsubscribeToken model for unsubscribe handling
- [x] TrackingEvent model with full device/geo information
- [x] BounceRecord model for bounce tracking
- [x] ComplaintRecord model for spam complaint tracking
- [x] SuppressionList model for blocking emails
- [x] TrackingService with comprehensive tracking operations
- [x] Pixel generation and email injection
- [x] Link rewriting for click tracking
- [x] User agent parsing for device detection
- [x] Bot detection with 70+ bot patterns
- [x] Geo IP lookup placeholder (integrate MaxMind in production)
- [x] Score awarding on open/click events
- [x] List-Unsubscribe header generation (RFC 8058)
- [x] Public tracking endpoints (no auth required)
- [x] Unsubscribe page templates
- [x] Webhook handlers for bounces and complaints
- [x] TrackingDomainViewSet with verify, set_default, dns_records actions
- [x] TrackingEventViewSet with stats, device/location/browser breakdowns
- [x] BounceRecordViewSet and ComplaintRecordViewSet
- [x] SuppressionListViewSet with bulk_add, check, stats
- [x] Database migrations

**Frontend:**
- [x] Tracking TypeScript types
- [x] Tracking API client (domains, events, bounces, complaints, suppression)
- [x] React Query hooks for all tracking operations
- [x] Analytics page with tracking statistics
- [x] Device/browser/location breakdown charts
- [x] Recent events table
- [x] Bounce and suppression breakdown cards
- [x] Campaign filter for analytics

### Phase 8: Reports & Dashboard - COMPLETED

**Backend:**
- [x] ReportsService with comprehensive analytics
- [x] Dashboard statistics endpoint (contacts, campaigns, emails, rates)
- [x] Email stats over time (hourly, daily, weekly, monthly granularity)
- [x] Campaign report endpoint with detailed stats
- [x] Campaign comparison endpoint
- [x] Activity timeline endpoint with filtering
- [x] Hot leads report with score trends
- [x] Score distribution endpoint
- [x] Performance summary with period comparison
- [x] CSV export for campaign reports
- [x] CSV export for contacts
- [x] CSV export for hot leads
- [x] All report endpoints registered under /api/v1/reports/

**Frontend:**
- [x] Report TypeScript types
- [x] Reports API client
- [x] React Query hooks for all report operations
- [x] Dashboard page with key metrics
- [x] Performance trend indicators
- [x] Recent activity feed
- [x] Hot leads table with score trends
- [x] Contact distribution (hot/warm/cold)
- [x] Reports page with tabs (Overview, Campaign Comparison, Score Distribution)
- [x] Email activity chart visualization
- [x] Score distribution histogram
- [x] Campaign comparison table
- [x] Export functionality for contacts and hot leads
- [x] Updated sidebar navigation with Dashboard and Reports

### Phase 9: Sequences - COMPLETED

**Backend:**
- [x] Sequence model with sending windows, throttling, and stop conditions
- [x] SequenceStep model with multiple step types (email, delay, condition, tag, webhook, task)
- [x] SequenceEnrollment model for tracking contact progress through sequences
- [x] SequenceStepExecution model for individual step execution records
- [x] SequenceEvent model for activity logging
- [x] SequenceEngine service with full step processing logic
- [x] Email step execution with template rendering
- [x] Delay step with configurable units (minutes, hours, days, weeks)
- [x] Tag step for adding/removing tags from contacts
- [x] Webhook step for triggering external services
- [x] Condition step for branching logic
- [x] Task step for creating tasks/reminders
- [x] Stop condition checking (reply, click, open, unsubscribe, bounce, score thresholds)
- [x] Sending window support with timezone and day-of-week configuration
- [x] Celery tasks for async sequence processing
- [x] Sequence API endpoints with full CRUD operations
- [x] Enrollment management endpoints (enroll, bulk enroll, pause, resume, stop)
- [x] Sequence statistics endpoint
- [x] Database migrations

**Frontend:**
- [x] Sequence TypeScript types
- [x] Sequences API client
- [x] React Query hooks for all sequence operations
- [x] Sequences page with summary stats
- [x] Sequence cards with status, enrollment count, and engagement metrics
- [x] Create sequence dialog with stop conditions and tracking options
- [x] Sequence actions (activate, pause, resume, archive, duplicate, delete)
- [x] Updated App.tsx with sequences route

### Phase 10: Website Tracking - COMPLETED

**Backend:**
- [x] WebsiteTrackingScript model for workspace JavaScript configuration
- [x] WebsiteVisitor model with visitor ID, contact matching, UTM, device, geo, and company fields
- [x] VisitorSession model for browsing session tracking
- [x] PageView model for individual page view events
- [x] WebsiteEvent model for custom events (clicks, forms, scroll, etc.)
- [x] VisitorIdentification model for tracking how visitors are identified
- [x] WebsiteTrackingService with full visitor tracking logic
- [x] JavaScript snippet generator with configurable tracking options
- [x] Public tracking endpoints (POST /t/w/track, GET /t/w/script/<id>.js)
- [x] Visitor-to-contact matching via email links, form submissions, IP matching
- [x] Score awarding for website visits and page views
- [x] WebsiteTrackingScriptViewSet with snippet, regenerate actions
- [x] WebsiteVisitorViewSet with sessions, page_views, events, identify, stats, top_pages, recent actions
- [x] VisitorSessionViewSet with page_views, events actions
- [x] Website tracking serializers
- [x] Admin registrations for all website tracking models
- [x] Database migrations

**Frontend:**
- [x] Website tracking TypeScript types (WebsiteTrackingScript, WebsiteVisitor, VisitorSession, PageView, WebsiteEvent, etc.)
- [x] Website tracking API client (websiteTrackingScriptApi, websiteVisitorsApi, visitorSessionsApi)
- [x] React Query hooks for all website tracking operations
- [x] Visitors page with stats cards (total, identified, anonymous, page views, avg duration)
- [x] Visitors table with search and filtering (all/identified/anonymous)
- [x] Top pages widget
- [x] Tracking setup dialog with embed code, settings configuration
- [x] Script regeneration functionality
- [x] Updated App.tsx with visitors route

### Phase 11: API & Webhooks - COMPLETED

**Backend:**
- [x] APIKey model with hashed keys, permissions, IP restrictions, rate limits
- [x] Webhook model with 25+ event types, HMAC signing, retry settings
- [x] WebhookDelivery model for delivery attempt tracking
- [x] WebhookEventLog model for event audit trail
- [x] APIKeyAuthentication for DRF (Bearer token, X-API-Key header)
- [x] Rate limiting with per-minute and per-day limits (Redis-backed)
- [x] API key permission levels (read, write, admin)
- [x] WebhookDispatcher service for event dispatching
- [x] WebhookDeliveryService for HTTP delivery with signature
- [x] HMAC-SHA256 payload signing with X-Webhook-Signature header
- [x] Exponential backoff retry logic (delay * 2^attempt)
- [x] Auto-disable webhooks after 10 consecutive failures
- [x] Celery tasks for async webhook delivery
- [x] Event dispatcher helpers for common events (contact, email, campaign, sequence, visitor)
- [x] APIKeyViewSet with revoke/activate actions
- [x] WebhookViewSet with test, secret, regenerate_secret, activate, deliveries, event_types actions
- [x] WebhookDeliveryViewSet with retry action
- [x] WebhookEventLogViewSet for viewing event history
- [x] URL routes registered under /api/v1/
- [x] Database migrations

**Frontend:**
- [x] Webhook TypeScript types (APIKey, Webhook, WebhookDelivery, WebhookEventLog, etc.)
- [x] Webhooks API client (apiKeysApi, webhooksApi, webhookDeliveriesApi, webhookEventLogsApi)
- [x] React Query hooks for all webhook and API key operations
- [x] API Keys settings page with create/revoke/delete actions
- [x] Webhooks settings page with create/test/pause/delete actions
- [x] One-time API key display with copy functionality
- [x] Webhook secret dialog with reveal and regenerate
- [x] Event type selection with grouped categories
- [x] Updated App.tsx with settings routes

### Phase 12: Integrations - COMPLETED

**Backend:**
- [x] Integration model with support for multiple integration types (Slack, Discord, HubSpot, Salesforce, Google Sheets, Zapier, n8n)
- [x] SlackIntegration model with channel config, notification settings
- [x] DiscordIntegration model with webhook URL, bot settings
- [x] HubSpotIntegration model with sync direction, field mapping
- [x] SalesforceIntegration model with sync options, Lead/Contact creation
- [x] GoogleSheetsIntegration model with export settings
- [x] IntegrationLog model for tracking sync operations
- [x] IntegrationFieldMapping model for CRM field mappings
- [x] SlackNotificationService (hot leads, email replies, campaign complete, form submit)
- [x] DiscordNotificationService (same events with Discord embeds)
- [x] HubSpotService (contact sync, token refresh, field mapping)
- [x] SalesforceService (contact sync, SOQL queries, Lead/Contact support)
- [x] GoogleSheetsService (contact export, hot leads export, campaign stats export)
- [x] OAuth helper functions for Slack, HubSpot, Salesforce, Google Sheets
- [x] IntegrationViewSet with test, sync, activate, deactivate, logs, settings actions
- [x] DiscordIntegrationViewSet for webhook-based creation (no OAuth)
- [x] IntegrationLogViewSet for viewing integration logs
- [x] WorkspaceViewSetMixin for workspace scoping
- [x] Database migrations
- [x] n8n and Zapier compatibility via existing webhook system

**Frontend:**
- [x] Integration TypeScript types (Integration, SlackIntegrationSettings, DiscordIntegrationSettings, HubSpotIntegrationSettings, SalesforceIntegrationSettings, GoogleSheetsIntegrationSettings, IntegrationLog, etc.)
- [x] Integrations API client (integrationsApi, discordIntegrationApi, integrationLogsApi)
- [x] React Query hooks for all integration operations
- [x] Integrations settings page with stats cards
- [x] Integration cards with status, success rate, sync button
- [x] Add integration dialog with OAuth/webhook type detection
- [x] Discord integration creation with webhook URL
- [x] Integration settings dialogs for each integration type
- [x] Slack settings (notifications, hot lead threshold)
- [x] Discord settings (webhook URL, bot settings, notifications)
- [x] HubSpot settings (sync direction, sync options, auto-sync interval)
- [x] Salesforce settings (sync direction, Lead/Contact creation, sync options)
- [x] Google Sheets settings (export options, sheet names, auto-export interval)
- [x] New UI components (Slider, ScrollArea, Separator, Checkbox, Alert)
- [x] Updated sidebar navigation with collapsible Settings section
- [x] Updated App.tsx with integrations route

### Phase 13: Teams & Polish - COMPLETED

**Backend:**
- [x] Extended User model with current_workspace field
- [x] Extended Workspace model with branding fields (logo_url, primary_color, company_name, company_website)
- [x] Extended Workspace with helper methods (add_member, remove_member, can_add_members, is_member, get_member_role)
- [x] Extended WorkspaceMember model with ROLE_PERMISSIONS dictionary for granular RBAC
- [x] WorkspaceMember.has_permission() method for permission checking
- [x] Extended WorkspaceInvitation with accept(), decline(), revoke() methods
- [x] WorkspaceActivity model for audit logging with 30+ action types
- [x] WorkspaceActivitySerializer with user details
- [x] WorkspaceSerializer with current user role/permissions
- [x] WorkspaceMemberSerializer with role_display and permissions
- [x] WorkspaceInvitationSerializer with status_display
- [x] WorkspacePermission and WorkspaceMemberPermission classes
- [x] HasWorkspacePermission mixin for permission-based access control
- [x] WorkspaceViewSet with current, switch, members, invitations, invite, activity, stats actions
- [x] WorkspaceMemberViewSet with leave action
- [x] WorkspaceInvitationViewSet with revoke, resend actions
- [x] InvitationAcceptViewSet for token-based invitation acceptance (public endpoints)
- [x] WorkspaceActivityViewSet for activity log viewing
- [x] Database migrations for all model changes

**Frontend:**
- [x] Workspace TypeScript types (Workspace, WorkspaceMember, WorkspaceInvitation, WorkspaceActivity, WorkspaceStats)
- [x] WorkspaceMemberRole type with owner/admin/member/viewer
- [x] Workspaces API client (workspacesApi, workspaceMembersApi, workspaceInvitationsApi, workspaceActivityApi)
- [x] React Query hooks for all workspace operations (useWorkspaces, useCurrentWorkspace, useWorkspaceMembers, etc.)
- [x] Team settings page with members/invitations/activity tabs
- [x] Members table with role badges and actions
- [x] Role change functionality (admin/member/viewer)
- [x] Member removal with confirmation dialog
- [x] Invitation sending dialog with role selection
- [x] Pending invitations table with resend/revoke actions
- [x] Activity log with user attribution and timestamps
- [x] Workspace settings page with general/company/email/branding sections
- [x] Workspace name, description, company information editing
- [x] Email defaults (from name, reply-to, timezone)
- [x] Primary color picker for branding
- [x] Usage limits display (members, contacts, emails/day)
- [x] API client setup (axios with auth interceptor)
- [x] Common API types (PaginatedResponse, APIError)
- [x] Toast notifications hook
- [x] Updated sidebar with Team and Workspace settings links
- [x] Form dependencies (react-hook-form, zod, @hookform/resolvers)

**RBAC Permissions:**
- Owner: Full access (manage_workspace, manage_members, manage_billing, manage_integrations, manage_api_keys, all campaign/sequence/contact operations)
- Admin: Same as owner except manage_billing
- Member: Create/edit/view campaigns, sequences, contacts, templates
- Viewer: View-only access (view_reports, view_tracking)

### Next Up
- Performance optimization
- Documentation

---

## Quick Commands

```bash
# Start development databases
make dev-db

# Run backend
make dev-backend

# Run frontend
make dev-frontend

# Run Celery worker
make dev-celery

# Database migrations
make migrate
make makemigrations

# Create superuser
make createsuperuser
```

Or manually:

```bash
# Backend
cd backend
source venv/bin/activate
python manage.py runserver

# Frontend
cd frontend
pnpm dev

# Docker databases
docker-compose -f docker-compose.dev.yml up -d
```

---

## Project Structure

```
coldmail/
├── backend/
│   ├── apps/
│   │   ├── core/           # Base models, utilities
│   │   ├── users/          # Custom User model
│   │   ├── workspaces/     # Team management
│   │   ├── email_accounts/ # SMTP/OAuth configs
│   │   ├── contacts/       # Contact management
│   │   ├── campaigns/      # Email campaigns
│   │   ├── sequences/      # Email sequences
│   │   ├── tracking/       # Open/click tracking
│   │   ├── webhooks/       # Webhook system
│   │   └── integrations/   # Third-party integrations
│   ├── coldmail/
│   │   ├── settings/       # Django settings (base, dev, prod, test)
│   │   ├── celery.py       # Celery config
│   │   └── urls.py         # URL routing
│   ├── venv/               # Python virtual env
│   ├── Dockerfile          # Production Dockerfile
│   ├── Dockerfile.dev      # Development Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/ui/  # shadcn/ui components
│   │   ├── lib/            # Utilities (cn function)
│   │   ├── hooks/          # React hooks
│   │   ├── api/            # API client
│   │   ├── stores/         # Zustand stores
│   │   ├── pages/          # Page components
│   │   └── types/          # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── nginx/
│   └── nginx.conf          # Nginx configuration
├── docker-compose.yml      # Production stack
├── docker-compose.dev.yml  # Development databases
├── Makefile                # Common commands
├── .env                    # Environment variables
├── .env.example            # Environment template
├── .gitignore
├── PROGRESS.md             # This file
└── coldmail.txt            # Project blueprint
```

---

## Environment Setup

1. **Start Docker Desktop** (for PostgreSQL + Redis)
2. **Start databases**: `make dev-db`
3. **Run backend**: `make dev-backend`
4. **Run frontend**: `make dev-frontend`

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs/
- Django Admin: http://localhost:8000/admin/

---

## Notes
- Python 3.12+
- Node.js 23+ with pnpm
- Django 5.2 LTS (Long Term Support)
- React 19 with TypeScript
- Tailwind CSS v4
- PostgreSQL 16
- Redis 7
