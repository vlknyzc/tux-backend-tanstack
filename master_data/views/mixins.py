"""
Shared mixins for view classes.
"""

from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from master_data import models
from master_data.models.base import set_current_workspace, _thread_locals


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
            
            # Set workspace context for thread-local storage (used by custom managers)
            set_current_workspace(workspace_id)
            
            # Set superuser context for thread-local storage
            if hasattr(request, 'user') and request.user.is_authenticated:
                _thread_locals.is_superuser = request.user.is_superuser
            else:
                _thread_locals.is_superuser = False

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


class QueryParamMixin:
    """
    Mixin for consistent and standardized query parameter handling.

    This mixin provides helper methods to access query parameters with
    type conversion, validation, and default values. Use this to standardize
    parameter access across all views.

    DRF Request objects always have query_params attribute, so no defensive
    checks are needed.
    """

    def get_query_param(self, param_name, default=None, required=False):
        """
        Get query parameter with validation.

        Args:
            param_name: Name of query parameter
            default: Default value if not provided
            required: Raise ValidationError if not provided

        Returns:
            Parameter value or default

        Raises:
            ValidationError: If required parameter is missing
        """
        value = self.request.query_params.get(param_name, default)

        if required and value is None:
            raise ValidationError(
                {param_name: f"Required parameter '{param_name}' not provided"}
            )

        return value

    def get_int_query_param(self, param_name, default=None, required=False):
        """
        Get integer query parameter with type conversion.

        Args:
            param_name: Name of query parameter
            default: Default value if not provided
            required: Raise ValidationError if not provided

        Returns:
            Integer value or default

        Raises:
            ValidationError: If parameter cannot be converted to integer
        """
        value = self.get_query_param(param_name, default, required)

        if value is not None and value != default:
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValidationError(
                    {param_name: f"Parameter '{param_name}' must be an integer"}
                )

        return value

    def get_bool_query_param(self, param_name, default=False):
        """
        Get boolean query parameter with smart conversion.

        Converts common boolean representations:
        - true, 1, yes, on → True
        - false, 0, no, off → False

        Args:
            param_name: Name of query parameter
            default: Default value if not provided (defaults to False)

        Returns:
            Boolean value
        """
        value = self.get_query_param(param_name)

        if value is None:
            return default

        # Handle string boolean values
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')

        # Handle actual boolean values (shouldn't happen with query params but just in case)
        return bool(value)

    def get_list_query_param(self, param_name, default=None, separator=','):
        """
        Get list query parameter split by separator.

        Useful for comma-separated lists like: ?ids=1,2,3

        Args:
            param_name: Name of query parameter
            default: Default value if not provided
            separator: Character to split on (default: comma)

        Returns:
            List of values or default
        """
        value = self.get_query_param(param_name)

        if value is None:
            return default if default is not None else []

        # Split and strip whitespace
        return [item.strip() for item in value.split(separator) if item.strip()]