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


class PlatformViewSet(viewsets.ModelViewSet):
    queryset = models.Platform.objects.all()
    serializer_class = serializers.PlatformSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
