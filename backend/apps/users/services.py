"""
User service layer for authentication and user management.
"""

from typing import Optional, Dict, Any
from uuid import UUID

from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from apps.workspaces.models import Workspace, WorkspaceMember


class UserService:
    """Service class for user operations."""

    @staticmethod
    def create_user(
        email: str,
        password: str,
        name: str = '',
        **extra_fields
    ) -> User:
        """
        Create a new user account.

        Args:
            email: User's email address
            password: User's password
            name: User's display name
            **extra_fields: Additional user fields

        Returns:
            Created User instance
        """
        with transaction.atomic():
            user = User.objects.create_user(
                email=email.lower().strip(),
                password=password,
                name=name,
                **extra_fields
            )
            return user

    @staticmethod
    def get_tokens_for_user(user: User) -> Dict[str, str]:
        """
        Generate JWT tokens for a user.

        Args:
            user: User instance

        Returns:
            Dictionary with 'access' and 'refresh' tokens
        """
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    @staticmethod
    def blacklist_token(refresh_token: str) -> bool:
        """
        Blacklist a refresh token (logout).

        Args:
            refresh_token: The refresh token to blacklist

        Returns:
            True if successful, False otherwise
        """
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return True
        except Exception:
            return False

    @staticmethod
    def get_user_with_workspaces(user: User) -> Dict[str, Any]:
        """
        Get user data with their workspaces.

        Args:
            user: User instance

        Returns:
            Dictionary with user data and workspaces
        """
        memberships = WorkspaceMember.objects.filter(
            user=user
        ).select_related('workspace').order_by('-workspace__created_at')

        workspaces = []
        for membership in memberships:
            workspaces.append({
                'id': str(membership.workspace.id),
                'name': membership.workspace.name,
                'slug': membership.workspace.slug,
                'role': membership.role,
                'is_current': (
                    user.current_workspace_id == membership.workspace.id
                    if user.current_workspace_id else False
                ),
            })

        return {
            'id': str(user.id),
            'email': user.email,
            'name': user.name,
            'avatar_url': user.avatar_url,
            'timezone': user.timezone,
            'is_verified': user.is_verified,
            'created_at': user.created_at.isoformat(),
            'workspaces': workspaces,
            'current_workspace_id': (
                str(user.current_workspace_id)
                if user.current_workspace_id else None
            ),
        }

    @staticmethod
    def update_last_login(user: User) -> None:
        """Update user's last login timestamp."""
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

    @staticmethod
    def set_current_workspace(user: User, workspace_id: UUID) -> bool:
        """
        Set user's current workspace.

        Args:
            user: User instance
            workspace_id: Workspace UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify user is a member of the workspace
            membership = WorkspaceMember.objects.get(
                user=user,
                workspace_id=workspace_id
            )
            user.current_workspace = membership.workspace
            user.save(update_fields=['current_workspace'])
            return True
        except WorkspaceMember.DoesNotExist:
            return False
