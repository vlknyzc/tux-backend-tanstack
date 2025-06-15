from rest_framework import viewsets, permissions, filters
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.conf import settings
from django.core.exceptions import PermissionDenied

from .. import models
from ..serializers.submission import SubmissionSerializer


from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter


class SubmissionFilter(filters.FilterSet):
    workspace = filters.NumberFilter(field_name='workspace')

    class Meta:
        model = models.Submission
        fields = ['id', 'status', 'rule',
                  'starting_field', 'workspace']


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubmissionFilter

    def get_queryset(self):
        """Get submissions filtered by workspace context"""
        # Check if workspace is explicitly provided in query params
        workspace = self.request.query_params.get('workspace')

        if workspace:
            # If workspace is explicitly provided, filter by it (for both superusers and regular users)
            try:
                workspace = int(workspace)
                # Validate user has access to this workspace (unless superuser)
                if hasattr(self.request, 'user') and not self.request.user.is_superuser:
                    if not self.request.user.has_workspace_access(workspace):
                        # Return empty queryset for unauthorized access
                        return models.Submission.objects.none()

                # Return queryset filtered by the specified workspace
                return models.Submission.objects.all_workspaces().filter(
                    workspace=workspace
                ).select_related(
                    'workspace', 'rule', 'created_by', 'starting_field', 'selected_parent_string'
                )

            except (ValueError, TypeError):
                # Invalid workspace parameter, return empty queryset
                return models.Submission.objects.none()

        # Default behavior when no workspace is specified
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.Submission.objects.all_workspaces().select_related(
                'workspace', 'rule', 'created_by', 'starting_field', 'selected_parent_string'
            )

        # For regular users, automatic workspace filtering is applied by managers
        return models.Submission.objects.all().select_related(
            'workspace', 'rule', 'created_by', 'starting_field', 'selected_parent_string'
        )

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new submission"""
        workspace = getattr(self.request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        # Validate user has access to this workspace
        if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace):
            raise PermissionDenied("Access denied to this workspace")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Workspace is auto-set by WorkspaceMixin.save()
        serializer.save(**kwargs)
