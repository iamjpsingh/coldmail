import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.core.models import BaseModel


class Workspace(BaseModel):
    """Workspace for team collaboration."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True, null=True)

    # Owner
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_workspaces'
    )

    # Settings
    default_timezone = models.CharField(max_length=50, default='UTC')
    default_from_name = models.CharField(max_length=255, blank=True)
    default_reply_to = models.EmailField(blank=True)

    # Branding
    primary_color = models.CharField(max_length=7, default='#3B82F6')
    company_name = models.CharField(max_length=255, blank=True)
    company_website = models.URLField(blank=True)

    # Limits
    max_members = models.IntegerField(default=5)
    max_contacts = models.IntegerField(default=10000)
    max_emails_per_day = models.IntegerField(default=1000)

    # Tracking
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'workspaces'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_member(self, user):
        """Get the membership for a user."""
        try:
            return self.members.get(user=user)
        except WorkspaceMember.DoesNotExist:
            return None

    def has_permission(self, user, permission):
        """Check if a user has a specific permission in this workspace."""
        member = self.get_member(user)
        if not member:
            return False
        return member.has_permission(permission)

    def add_member(self, user, role='member', invited_by=None):
        """Add a member to the workspace."""
        return WorkspaceMember.objects.create(
            workspace=self,
            user=user,
            role=role,
            invited_by=invited_by,
            accepted_at=timezone.now()
        )

    def remove_member(self, user):
        """Remove a member from the workspace."""
        self.members.filter(user=user).delete()

    @property
    def member_count(self):
        """Get the number of members."""
        return self.members.count()

    @property
    def can_add_members(self):
        """Check if more members can be added."""
        return self.member_count < self.max_members


class WorkspaceMember(BaseModel):
    """Membership in a workspace."""

    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
        VIEWER = 'viewer', 'Viewer'

    # Permission definitions by role
    ROLE_PERMISSIONS = {
        'owner': [
            'manage_workspace', 'manage_members', 'manage_billing',
            'manage_integrations', 'manage_api_keys',
            'create_campaigns', 'edit_campaigns', 'delete_campaigns', 'send_campaigns',
            'create_sequences', 'edit_sequences', 'delete_sequences',
            'create_contacts', 'edit_contacts', 'delete_contacts', 'import_contacts', 'export_contacts',
            'create_templates', 'edit_templates', 'delete_templates',
            'view_reports', 'export_reports',
            'view_tracking', 'manage_tracking',
        ],
        'admin': [
            'manage_members', 'manage_integrations', 'manage_api_keys',
            'create_campaigns', 'edit_campaigns', 'delete_campaigns', 'send_campaigns',
            'create_sequences', 'edit_sequences', 'delete_sequences',
            'create_contacts', 'edit_contacts', 'delete_contacts', 'import_contacts', 'export_contacts',
            'create_templates', 'edit_templates', 'delete_templates',
            'view_reports', 'export_reports',
            'view_tracking', 'manage_tracking',
        ],
        'member': [
            'create_campaigns', 'edit_campaigns', 'send_campaigns',
            'create_sequences', 'edit_sequences',
            'create_contacts', 'edit_contacts', 'import_contacts', 'export_contacts',
            'create_templates', 'edit_templates',
            'view_reports',
            'view_tracking',
        ],
        'viewer': [
            'view_reports',
            'view_tracking',
        ],
    }

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_memberships'
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_invitations'
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    daily_digest = models.BooleanField(default=False)

    class Meta:
        db_table = 'workspace_members'
        unique_together = ['workspace', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"

    @property
    def is_admin(self):
        return self.role in [self.Role.OWNER, self.Role.ADMIN]

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    def has_permission(self, permission):
        """Check if this member has a specific permission."""
        return permission in self.ROLE_PERMISSIONS.get(self.role, [])

    def get_permissions(self):
        """Get all permissions for this member."""
        return self.ROLE_PERMISSIONS.get(self.role, [])


class WorkspaceInvitation(BaseModel):
    """Pending invitation to join a workspace."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        EXPIRED = 'expired', 'Expired'
        REVOKED = 'revoked', 'Revoked'

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20,
        choices=WorkspaceMember.Role.choices,
        default=WorkspaceMember.Role.MEMBER
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_invitations_sent'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    message = models.TextField(blank=True, help_text="Personal message to include in invitation email")

    class Meta:
        db_table = 'workspace_invitations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation to {self.email} for {self.workspace.name}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return self.status == self.Status.PENDING and not self.is_expired

    def accept(self, user):
        """Accept the invitation and create membership."""
        if not self.is_valid:
            return None

        member = self.workspace.add_member(
            user=user,
            role=self.role,
            invited_by=self.invited_by
        )

        self.status = self.Status.ACCEPTED
        self.save(update_fields=['status', 'updated_at'])

        return member

    def decline(self):
        """Decline the invitation."""
        self.status = self.Status.DECLINED
        self.save(update_fields=['status', 'updated_at'])

    def revoke(self):
        """Revoke the invitation."""
        self.status = self.Status.REVOKED
        self.save(update_fields=['status', 'updated_at'])


class WorkspaceActivity(BaseModel):
    """Activity log for workspace actions."""

    class ActionType(models.TextChoices):
        # Workspace actions
        WORKSPACE_CREATED = 'workspace_created', 'Workspace Created'
        WORKSPACE_UPDATED = 'workspace_updated', 'Workspace Updated'
        WORKSPACE_DELETED = 'workspace_deleted', 'Workspace Deleted'

        # Member actions
        MEMBER_INVITED = 'member_invited', 'Member Invited'
        MEMBER_JOINED = 'member_joined', 'Member Joined'
        MEMBER_LEFT = 'member_left', 'Member Left'
        MEMBER_REMOVED = 'member_removed', 'Member Removed'
        MEMBER_ROLE_CHANGED = 'member_role_changed', 'Member Role Changed'
        INVITATION_REVOKED = 'invitation_revoked', 'Invitation Revoked'

        # Campaign actions
        CAMPAIGN_CREATED = 'campaign_created', 'Campaign Created'
        CAMPAIGN_STARTED = 'campaign_started', 'Campaign Started'
        CAMPAIGN_PAUSED = 'campaign_paused', 'Campaign Paused'
        CAMPAIGN_COMPLETED = 'campaign_completed', 'Campaign Completed'
        CAMPAIGN_DELETED = 'campaign_deleted', 'Campaign Deleted'

        # Sequence actions
        SEQUENCE_CREATED = 'sequence_created', 'Sequence Created'
        SEQUENCE_ACTIVATED = 'sequence_activated', 'Sequence Activated'
        SEQUENCE_PAUSED = 'sequence_paused', 'Sequence Paused'
        SEQUENCE_DELETED = 'sequence_deleted', 'Sequence Deleted'

        # Contact actions
        CONTACTS_IMPORTED = 'contacts_imported', 'Contacts Imported'
        CONTACTS_EXPORTED = 'contacts_exported', 'Contacts Exported'
        CONTACTS_DELETED = 'contacts_deleted', 'Contacts Deleted'

        # Integration actions
        INTEGRATION_CONNECTED = 'integration_connected', 'Integration Connected'
        INTEGRATION_DISCONNECTED = 'integration_disconnected', 'Integration Disconnected'

        # Settings actions
        SETTINGS_UPDATED = 'settings_updated', 'Settings Updated'
        API_KEY_CREATED = 'api_key_created', 'API Key Created'
        API_KEY_REVOKED = 'api_key_revoked', 'API Key Revoked'
        WEBHOOK_CREATED = 'webhook_created', 'Webhook Created'
        WEBHOOK_DELETED = 'webhook_deleted', 'Webhook Deleted'

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='workspace_activities'
    )
    action = models.CharField(max_length=50, choices=ActionType.choices)
    description = models.TextField()

    # Optional references to related objects
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='targeted_activities'
    )
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.CharField(max_length=36, blank=True)
    target_name = models.CharField(max_length=255, blank=True)

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'workspace_activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} in {self.workspace}"

    @classmethod
    def log(cls, workspace, user, action, description, **kwargs):
        """Create an activity log entry."""
        return cls.objects.create(
            workspace=workspace,
            user=user,
            action=action,
            description=description,
            **kwargs
        )
