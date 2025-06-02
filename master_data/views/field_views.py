from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from .. import serializers
from .. import models


class FieldViewSet(viewsets.ModelViewSet):
    platform = filters.NumberFilter(method='filter_platform_id')

    queryset = models.Field.objects.all()
    serializer_class = serializers.FieldSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['platform', 'id']

    def filter_platform_id(self, queryset, name, value):
        return queryset.filter(platform__id=value)

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new field"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
