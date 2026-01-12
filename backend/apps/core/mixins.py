"""Reusable mixins for views and viewsets."""


class WorkspaceViewSetMixin:
    """
    Mixin for ViewSets that automatically filters by workspace.

    Expects the user to have a `current_workspace` property.
    The model should have a `workspace` ForeignKey field.
    """

    def get_queryset(self):
        """Filter queryset by current workspace."""
        queryset = super().get_queryset()

        # Get workspace from request headers or user's current workspace
        workspace = getattr(self.request.user, 'current_workspace', None)

        if workspace is None:
            # Try to get from header
            workspace_id = self.request.headers.get('X-Workspace-ID')
            if workspace_id:
                from apps.workspaces.models import Workspace
                try:
                    workspace = Workspace.objects.get(id=workspace_id)
                except Workspace.DoesNotExist:
                    pass

        if workspace:
            return queryset.filter(workspace=workspace)

        return queryset.none()

    def perform_create(self, serializer):
        """Automatically set workspace on create."""
        workspace = getattr(self.request.user, 'current_workspace', None)

        if workspace is None:
            workspace_id = self.request.headers.get('X-Workspace-ID')
            if workspace_id:
                from apps.workspaces.models import Workspace
                try:
                    workspace = Workspace.objects.get(id=workspace_id)
                except Workspace.DoesNotExist:
                    pass

        if workspace:
            serializer.save(workspace=workspace)
        else:
            serializer.save()
