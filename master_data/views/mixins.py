"""
Shared mixins for view classes.
"""

from django.core.exceptions import PermissionDenied
from master_data import models


class WorkspaceValidationMixin:
    """
    Mixin for workspace validation in viewsets.
    Implements the workspace URL validation from the design document.
    """

    def dispatch(self, request, *args, **kwargs):
        """Validate workspace access before processing request."""
        workspace_id = kwargs.get('workspace_id')

        if workspace_id:
            # Convert to int and validate
            try:
                workspace_id = int(workspace_id)
            except (ValueError, TypeError):
                raise PermissionDenied("Invalid workspace ID")

            # Validate user has access to this workspace
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not request.user.is_superuser and not request.user.has_workspace_access(workspace_id):
                    raise PermissionDenied(
                        f"Access denied to workspace {workspace_id}")

            # Set workspace context for the request
            request.workspace_id = workspace_id

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Filter queryset by workspace."""
        queryset = super().get_queryset()
        workspace_id = getattr(self.request, 'workspace_id', None)

        if workspace_id:
            # Filter by workspace
            if hasattr(queryset.model, 'workspace'):
                queryset = queryset.filter(workspace_id=workspace_id)

        return queryset

    def perform_create(self, serializer):
        """Set workspace when creating objects."""
        workspace_id = getattr(self.request, 'workspace_id', None)
        kwargs = {}

        if workspace_id:
            try:
                workspace = models.Workspace.objects.get(id=workspace_id)
                kwargs['workspace'] = workspace
            except models.Workspace.DoesNotExist:
                raise PermissionDenied(
                    f"Workspace {workspace_id} does not exist")

        # Set created_by if user is authenticated
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)