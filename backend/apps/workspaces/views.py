"""Views for workspaces."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count

from .models import Workspace, WorkspaceMember, WorkspaceInvitation, WorkspaceActivity
from .serializers import (
    WorkspaceSerializer,
    WorkspaceCreateSerializer,
    WorkspaceUpdateSerializer,
    WorkspaceMemberSerializer,
    WorkspaceMemberUpdateSerializer,
    WorkspaceInvitationSerializer,
    WorkspaceInvitationCreateSerializer,
    WorkspaceActivitySerializer,
    SwitchWorkspaceSerializer,
)
from .permissions import WorkspacePermission, WorkspaceMemberPermission


class WorkspaceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing workspaces."""

    permission_classes = [IsAuthenticated, WorkspacePermission]
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        """Return workspaces the user is a member of."""
        return Workspace.objects.filter(
            members__user=self.request.user
        ).annotate(
            member_count=Count('members')
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'create':
            return WorkspaceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return WorkspaceUpdateSerializer
        return WorkspaceSerializer

    def perform_create(self, serializer):
        workspace = serializer.save()

        # Log activity
        WorkspaceActivity.log(
            workspace=workspace,
            user=self.request.user,
            action=WorkspaceActivity.ActionType.WORKSPACE_CREATED,
            description=f"Created workspace '{workspace.name}'",
            ip_address=self.get_client_ip(),
        )

    def perform_update(self, serializer):
        workspace = serializer.save()

        # Log activity
        WorkspaceActivity.log(
            workspace=workspace,
            user=self.request.user,
            action=WorkspaceActivity.ActionType.WORKSPACE_UPDATED,
            description=f"Updated workspace settings",
            ip_address=self.get_client_ip(),
        )

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the user's current workspace."""
        workspace = request.user.current_workspace
        if not workspace:
            # Try to get the first workspace the user is a member of
            membership = WorkspaceMember.objects.filter(user=request.user).first()
            if membership:
                workspace = membership.workspace
                request.user.current_workspace = workspace
                request.user.save(update_fields=['current_workspace'])

        if not workspace:
            return Response(
                {'error': 'No workspace found. Please create or join a workspace.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(workspace)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def switch(self, request):
        """Switch to a different workspace."""
        serializer = SwitchWorkspaceSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        workspace = Workspace.objects.get(id=serializer.validated_data['workspace_id'])
        request.user.current_workspace = workspace
        request.user.save(update_fields=['current_workspace'])

        return Response(WorkspaceSerializer(workspace, context={'request': request}).data)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all members of a workspace."""
        workspace = self.get_object()
        members = workspace.members.select_related('user', 'invited_by').all()
        serializer = WorkspaceMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def invitations(self, request, pk=None):
        """Get pending invitations for a workspace."""
        workspace = self.get_object()
        invitations = workspace.invitations.filter(
            status=WorkspaceInvitation.Status.PENDING
        ).select_related('invited_by')
        serializer = WorkspaceInvitationSerializer(invitations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        """Invite a user to the workspace."""
        workspace = self.get_object()

        # Check permission
        member = workspace.get_member(request.user)
        if not member or not member.has_permission('manage_members'):
            return Response(
                {'error': 'You do not have permission to invite members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = WorkspaceInvitationCreateSerializer(
            data=request.data,
            context={'workspace': workspace, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        invitation = WorkspaceInvitation.objects.create(
            workspace=workspace,
            email=serializer.validated_data['email'],
            role=serializer.validated_data['role'],
            message=serializer.validated_data.get('message', ''),
            invited_by=request.user,
        )

        # Log activity
        WorkspaceActivity.log(
            workspace=workspace,
            user=request.user,
            action=WorkspaceActivity.ActionType.MEMBER_INVITED,
            description=f"Invited {invitation.email} as {invitation.get_role_display()}",
            metadata={'email': invitation.email, 'role': invitation.role},
            ip_address=self.get_client_ip(),
        )

        # TODO: Send invitation email

        return Response(
            WorkspaceInvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """Get activity log for the workspace."""
        workspace = self.get_object()
        activities = workspace.activities.select_related('user', 'target_user')[:100]
        serializer = WorkspaceActivitySerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get workspace statistics."""
        workspace = self.get_object()

        from apps.contacts.models import Contact
        from apps.campaigns.models import Campaign
        from apps.sequences.models import Sequence

        stats = {
            'member_count': workspace.member_count,
            'max_members': workspace.max_members,
            'contact_count': Contact.objects.filter(workspace=workspace).count(),
            'max_contacts': workspace.max_contacts,
            'campaign_count': Campaign.objects.filter(workspace=workspace).count(),
            'sequence_count': Sequence.objects.filter(workspace=workspace).count(),
            'emails_sent_today': 0,  # TODO: Calculate from email logs
            'max_emails_per_day': workspace.max_emails_per_day,
        }

        return Response(stats)

    def get_client_ip(self):
        """Get client IP address from request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')


class WorkspaceMemberViewSet(viewsets.ModelViewSet):
    """ViewSet for managing workspace members."""

    permission_classes = [IsAuthenticated, WorkspaceMemberPermission]
    serializer_class = WorkspaceMemberSerializer

    def get_queryset(self):
        """Return members of the current workspace."""
        workspace = self.request.user.current_workspace
        if not workspace:
            return WorkspaceMember.objects.none()
        return workspace.members.select_related('user', 'invited_by')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return WorkspaceMemberUpdateSerializer
        return WorkspaceMemberSerializer

    def perform_update(self, serializer):
        member = serializer.save()
        workspace = member.workspace

        # Log role change if role was updated
        if 'role' in serializer.validated_data:
            WorkspaceActivity.log(
                workspace=workspace,
                user=self.request.user,
                action=WorkspaceActivity.ActionType.MEMBER_ROLE_CHANGED,
                description=f"Changed {member.user.email}'s role to {member.get_role_display()}",
                target_user=member.user,
                metadata={'new_role': member.role},
            )

    def destroy(self, request, *args, **kwargs):
        """Remove a member from the workspace."""
        member = self.get_object()
        workspace = member.workspace

        # Can't remove the owner
        if member.is_owner:
            return Response(
                {'error': 'Cannot remove the workspace owner.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Log activity
        WorkspaceActivity.log(
            workspace=workspace,
            user=request.user,
            action=WorkspaceActivity.ActionType.MEMBER_REMOVED,
            description=f"Removed {member.user.email} from the workspace",
            target_user=member.user,
        )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def leave(self, request):
        """Leave the current workspace."""
        workspace = request.user.current_workspace
        if not workspace:
            return Response(
                {'error': 'No current workspace.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        member = workspace.get_member(request.user)
        if not member:
            return Response(
                {'error': 'You are not a member of this workspace.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if member.is_owner:
            return Response(
                {'error': 'The owner cannot leave. Transfer ownership first or delete the workspace.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Log activity
        WorkspaceActivity.log(
            workspace=workspace,
            user=request.user,
            action=WorkspaceActivity.ActionType.MEMBER_LEFT,
            description=f"{request.user.email} left the workspace",
        )

        member.delete()

        # Switch to another workspace
        other_membership = WorkspaceMember.objects.filter(user=request.user).first()
        if other_membership:
            request.user.current_workspace = other_membership.workspace
        else:
            request.user.current_workspace = None
        request.user.save(update_fields=['current_workspace'])

        return Response({'status': 'success'})


class WorkspaceInvitationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing workspace invitations."""

    permission_classes = [IsAuthenticated]
    serializer_class = WorkspaceInvitationSerializer

    def get_queryset(self):
        """Return invitations for the current workspace."""
        workspace = self.request.user.current_workspace
        if not workspace:
            return WorkspaceInvitation.objects.none()
        return workspace.invitations.select_related('invited_by')

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke an invitation."""
        invitation = self.get_object()
        workspace = invitation.workspace

        # Check permission
        member = workspace.get_member(request.user)
        if not member or not member.has_permission('manage_members'):
            return Response(
                {'error': 'You do not have permission to revoke invitations.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if invitation.status != WorkspaceInvitation.Status.PENDING:
            return Response(
                {'error': 'This invitation cannot be revoked.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.revoke()

        # Log activity
        WorkspaceActivity.log(
            workspace=workspace,
            user=request.user,
            action=WorkspaceActivity.ActionType.INVITATION_REVOKED,
            description=f"Revoked invitation to {invitation.email}",
            metadata={'email': invitation.email},
        )

        return Response({'status': 'revoked'})

    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend an invitation email."""
        invitation = self.get_object()
        workspace = invitation.workspace

        # Check permission
        member = workspace.get_member(request.user)
        if not member or not member.has_permission('manage_members'):
            return Response(
                {'error': 'You do not have permission to resend invitations.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if invitation.status != WorkspaceInvitation.Status.PENDING:
            return Response(
                {'error': 'This invitation is not pending.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extend expiration
        invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
        invitation.save(update_fields=['expires_at', 'updated_at'])

        # TODO: Send invitation email

        return Response({'status': 'sent'})


class InvitationAcceptViewSet(viewsets.ViewSet):
    """ViewSet for accepting invitations (public endpoint)."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='(?P<token>[^/.]+)')
    def get_invitation(self, request, token=None):
        """Get invitation details by token."""
        try:
            invitation = WorkspaceInvitation.objects.select_related(
                'workspace', 'invited_by'
            ).get(token=token)
        except WorkspaceInvitation.DoesNotExist:
            return Response(
                {'error': 'Invalid invitation token.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not invitation.is_valid:
            return Response(
                {'error': 'This invitation has expired or is no longer valid.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'workspace': {
                'id': str(invitation.workspace.id),
                'name': invitation.workspace.name,
            },
            'role': invitation.role,
            'role_display': invitation.get_role_display(),
            'invited_by': {
                'email': invitation.invited_by.email,
                'name': invitation.invited_by.name,
            },
            'message': invitation.message,
            'expires_at': invitation.expires_at,
        })

    @action(detail=False, methods=['post'], url_path='(?P<token>[^/.]+)/accept')
    def accept(self, request, token=None):
        """Accept an invitation."""
        try:
            invitation = WorkspaceInvitation.objects.select_related(
                'workspace'
            ).get(token=token)
        except WorkspaceInvitation.DoesNotExist:
            return Response(
                {'error': 'Invalid invitation token.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not invitation.is_valid:
            return Response(
                {'error': 'This invitation has expired or is no longer valid.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check email matches
        if invitation.email.lower() != request.user.email.lower():
            return Response(
                {'error': 'This invitation was sent to a different email address.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Accept invitation
        member = invitation.accept(request.user)

        # Log activity
        WorkspaceActivity.log(
            workspace=invitation.workspace,
            user=request.user,
            action=WorkspaceActivity.ActionType.MEMBER_JOINED,
            description=f"{request.user.email} joined the workspace",
        )

        # Switch to the new workspace
        request.user.current_workspace = invitation.workspace
        request.user.save(update_fields=['current_workspace'])

        return Response({
            'status': 'accepted',
            'workspace': WorkspaceSerializer(invitation.workspace, context={'request': request}).data,
        })

    @action(detail=False, methods=['post'], url_path='(?P<token>[^/.]+)/decline')
    def decline(self, request, token=None):
        """Decline an invitation."""
        try:
            invitation = WorkspaceInvitation.objects.get(token=token)
        except WorkspaceInvitation.DoesNotExist:
            return Response(
                {'error': 'Invalid invitation token.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.status != WorkspaceInvitation.Status.PENDING:
            return Response(
                {'error': 'This invitation is not pending.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.decline()

        return Response({'status': 'declined'})


class WorkspaceActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing workspace activity."""

    permission_classes = [IsAuthenticated]
    serializer_class = WorkspaceActivitySerializer

    def get_queryset(self):
        """Return activities for the current workspace with optional filtering."""
        workspace = self.request.user.current_workspace
        if not workspace:
            return WorkspaceActivity.objects.none()

        queryset = workspace.activities.select_related('user', 'target_user')

        # Filter by action type
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset
