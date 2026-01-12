"""Permissions for workspaces."""
from rest_framework import permissions


class WorkspacePermission(permissions.BasePermission):
    """Permission for workspace operations."""

    def has_permission(self, request, view):
        """Check if user has permission to access workspace endpoints."""
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access a specific workspace."""
        # Check if user is a member of this workspace
        member = obj.get_member(request.user)
        if not member:
            return False

        # Read operations allowed for all members
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write operations need appropriate permissions
        if view.action in ['update', 'partial_update']:
            return member.has_permission('manage_workspace')

        if view.action == 'destroy':
            return member.is_owner

        return member.is_admin


class WorkspaceMemberPermission(permissions.BasePermission):
    """Permission for workspace member operations."""

    def has_permission(self, request, view):
        """Check if user has permission to access member endpoints."""
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to manage a specific member."""
        workspace = obj.workspace
        member = workspace.get_member(request.user)

        if not member:
            return False

        # Can view own membership
        if request.method in permissions.SAFE_METHODS:
            return True

        # Can update own notification preferences
        if view.action in ['update', 'partial_update'] and obj.user == request.user:
            return True

        # Need manage_members permission to modify others
        if not member.has_permission('manage_members'):
            return False

        # Can't modify owner unless you are the owner
        if obj.is_owner and not member.is_owner:
            return False

        # Owner can modify anyone, admin can modify members and viewers
        if member.is_owner:
            return True

        # Admin can modify members and viewers but not other admins
        if member.role == 'admin' and obj.role in ['member', 'viewer']:
            return True

        return False


class HasWorkspacePermission:
    """Mixin to check workspace permissions in views."""

    permission_required = None

    def has_workspace_permission(self, permission=None):
        """Check if current user has a permission in the current workspace."""
        workspace = self.request.user.current_workspace
        if not workspace:
            return False

        perm = permission or self.permission_required
        if not perm:
            return True

        return workspace.has_permission(self.request.user, perm)

    def check_workspace_permission(self, permission=None):
        """Check permission and raise PermissionDenied if not allowed."""
        from rest_framework.exceptions import PermissionDenied

        if not self.has_workspace_permission(permission):
            raise PermissionDenied(
                f"You do not have permission to perform this action."
            )
