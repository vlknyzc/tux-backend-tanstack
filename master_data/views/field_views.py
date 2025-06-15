from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.core.exceptions import PermissionDenied

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .. import serializers
from .. import models


class FieldFilter(filters.FilterSet):
    platform = filters.NumberFilter(method='filter_platform_id')

    class Meta:
        model = models.Field
        fields = ['platform', 'id', 'field_level']

    def filter_platform_id(self, queryset, name, value):
        return queryset.filter(platform__id=value)


class FieldViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.FieldSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = FieldFilter

    def get_queryset(self):
        """Get all fields - they are global and not workspace-specific"""
        return models.Field.objects.all()

    def perform_create(self, serializer):
        """Set created_by when creating a new field"""
        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)
