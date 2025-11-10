from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.conf import settings
from django.db import transaction
from django.core.exceptions import PermissionDenied

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .. import serializers
from .. import models
from ..permissions import IsAuthenticatedOrDebugReadOnly


class EntityFilter(filters.FilterSet):
    platform = filters.NumberFilter(field_name='platform__id')

    class Meta:
        model = models.Entity
        fields = ['platform', 'id', 'entity_level']


@extend_schema(tags=['Entities'])
class EntityViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.EntitySerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EntityFilter

    @extend_schema(tags=["Entities"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Entities"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Entities"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Entities"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Entities"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Entities"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Get all entities - they are global and not workspace-specific"""
        return models.Entity.objects.all()

    def perform_create(self, serializer):
        """Set created_by when creating a new entity"""
        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)
