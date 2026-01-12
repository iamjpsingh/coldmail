"""Serializers for workspaces."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Workspace, WorkspaceMember, WorkspaceInvitation, WorkspaceActivity

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested representations."""

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'avatar_url']
        read_only_fields = fields


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    """Serializer for workspace members."""

    user = UserBasicSerializer(read_only=True)
    invited_by = UserBasicSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = WorkspaceMember
        fields = [
            'id',
            'user',
            'role',
            'role_display',
            'permissions',
            'invited_by',
            'invited_at',
            'accepted_at',
            'email_notifications',
            'daily_digest',
            'is_admin',
            'is_owner',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'invited_by', 'invited_at', 'accepted_at', 'created_at']

    def get_permissions(self, obj):
        return obj.get_permissions()


class WorkspaceMemberUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating workspace member."""

    class Meta:
        model = WorkspaceMember
        fields = ['role', 'email_notifications', 'daily_digest']


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for workspace."""

    owner = UserBasicSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    can_add_members = serializers.BooleanField(read_only=True)
    current_user_role = serializers.SerializerMethodField()
    current_user_permissions = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'logo_url',
            'owner',
            'default_timezone',
            'default_from_name',
            'default_reply_to',
            'primary_color',
            'company_name',
            'company_website',
            'max_members',
            'max_contacts',
            'max_emails_per_day',
            'member_count',
            'can_add_members',
            'current_user_role',
            'current_user_permissions',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'slug', 'owner', 'max_members', 'max_contacts',
            'max_emails_per_day', 'created_at', 'updated_at'
        ]

    def get_current_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            member = obj.get_member(request.user)
            if member:
                return member.role
        return None

    def get_current_user_permissions(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            member = obj.get_member(request.user)
            if member:
                return member.get_permissions()
        return []


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a workspace."""

    class Meta:
        model = Workspace
        fields = ['name', 'description', 'default_timezone', 'company_name']

    def create(self, validated_data):
        from django.utils.text import slugify
        import secrets

        user = self.context['request'].user
        name = validated_data['name']

        # Generate unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        workspace = Workspace.objects.create(
            owner=user,
            slug=slug,
            **validated_data
        )

        # Add owner as a member
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=user,
            role=WorkspaceMember.Role.OWNER,
            accepted_at=timezone.now()
        )

        # Set as current workspace
        user.current_workspace = workspace
        user.save(update_fields=['current_workspace'])

        return workspace


class WorkspaceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating workspace settings."""

    class Meta:
        model = Workspace
        fields = [
            'name',
            'description',
            'logo_url',
            'default_timezone',
            'default_from_name',
            'default_reply_to',
            'primary_color',
            'company_name',
            'company_website',
        ]


class WorkspaceInvitationSerializer(serializers.ModelSerializer):
    """Serializer for workspace invitations."""

    invited_by = UserBasicSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = WorkspaceInvitation
        fields = [
            'id',
            'email',
            'role',
            'role_display',
            'invited_by',
            'status',
            'status_display',
            'message',
            'expires_at',
            'is_expired',
            'is_valid',
            'created_at',
        ]
        read_only_fields = ['id', 'invited_by', 'status', 'expires_at', 'created_at']


class WorkspaceInvitationCreateSerializer(serializers.Serializer):
    """Serializer for creating workspace invitations."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=WorkspaceMember.Role.choices, default='member')
    message = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        workspace = self.context['workspace']

        # Check if user is already a member
        if WorkspaceMember.objects.filter(
            workspace=workspace,
            user__email=value
        ).exists():
            raise serializers.ValidationError("This user is already a member of this workspace.")

        # Check if there's a pending invitation
        if WorkspaceInvitation.objects.filter(
            workspace=workspace,
            email=value,
            status=WorkspaceInvitation.Status.PENDING
        ).exists():
            raise serializers.ValidationError("An invitation has already been sent to this email.")

        return value.lower()

    def validate(self, attrs):
        workspace = self.context['workspace']

        # Check if workspace can add more members
        if not workspace.can_add_members:
            raise serializers.ValidationError(
                f"This workspace has reached its member limit ({workspace.max_members})."
            )

        return attrs


class WorkspaceActivitySerializer(serializers.ModelSerializer):
    """Serializer for workspace activity log."""

    user = UserBasicSerializer(read_only=True)
    target_user = UserBasicSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = WorkspaceActivity
        fields = [
            'id',
            'user',
            'action',
            'action_display',
            'description',
            'target_user',
            'target_type',
            'target_id',
            'target_name',
            'metadata',
            'created_at',
        ]


class SwitchWorkspaceSerializer(serializers.Serializer):
    """Serializer for switching current workspace."""

    workspace_id = serializers.UUIDField()

    def validate_workspace_id(self, value):
        user = self.context['request'].user

        # Check if user is a member of this workspace
        if not WorkspaceMember.objects.filter(
            workspace_id=value,
            user=user
        ).exists():
            raise serializers.ValidationError("You are not a member of this workspace.")

        return value


# Import timezone for WorkspaceCreateSerializer
from django.utils import timezone
