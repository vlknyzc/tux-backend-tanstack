from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from .. import serializers
from .. import models


class WorkspaceFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')

    class Meta:
        model = models.Workspace
        fields = ['id']


class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = models.Workspace.objects.all()
    serializer_class = serializers.WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = WorkspaceFilter

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new workspace"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()


class PlatformViewSet(viewsets.ModelViewSet):
    queryset = models.Platform.objects.all()
    serializer_class = serializers.PlatformSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new platform"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
