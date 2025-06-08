from rest_framework import viewsets, permissions, filters
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.core.exceptions import PermissionDenied

from .. import models
from ..serializers.submission import SubmissionSerializer


class SubmissionFilter(filters.FilterSet):
    # Remove workspace filter as it's handled by middleware
    class Meta:
        model = models.Submission
        fields = ['id', 'status', 'rule', 'starting_field']


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubmissionFilter

    def get_queryset(self):
        """Get submissions filtered by workspace context"""
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.Submission.objects.all_workspaces()

        # For regular users, automatic workspace filtering is applied by managers
        return models.Submission.objects.all()

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new submission"""
        workspace_id = getattr(self.request, 'workspace_id', None)
        if not workspace_id:
            raise PermissionDenied("No workspace context available")

        # Validate user has access to this workspace
        if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace_id):
            raise PermissionDenied("Access denied to this workspace")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Workspace is auto-set by WorkspaceMixin.save()
        serializer.save(**kwargs)
