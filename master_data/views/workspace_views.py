from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.core.exceptions import PermissionDenied

from typing import Optional, Dict, List, Any

from .. import serializers
from .. import models


class WorkspaceFilter(filters.FilterSet):
    # Remove workspace filter since workspaces are handled differently
    class Meta:
        model = models.Workspace
        fields = ['id', 'status']


class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = WorkspaceFilter

    def get_queryset(self):
        """Get workspaces the user has access to"""
        user = self.request.user

        if user.is_superuser:
            # Superusers can see all workspaces
            return models.Workspace.objects.all()
        else:
            # Regular users can only see workspaces they're assigned to
            return user.get_accessible_workspaces()

    def perform_create(self, serializer: serializers.WorkspaceSerializer):
        """Set created_by when creating a new workspace"""
        if not self.request.user.is_superuser:
            raise PermissionDenied("Only superusers can create workspaces")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)


class PlatformViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.PlatformSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        """Get all platforms - they are global and not workspace-specific"""
        return models.Platform.objects.all()

    def perform_create(self, serializer: serializers.PlatformSerializer) -> None:
        """Set created_by when creating a new platform"""
        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)
