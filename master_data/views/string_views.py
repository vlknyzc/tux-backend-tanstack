from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from .. import serializers
from .. import models


class StringFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    field = filters.NumberFilter(method='filter_field_id')
    field_level = filters.NumberFilter(method='filter_field_level')

    class Meta:
        model = models.String
        fields = ['id', 'workspace', 'field', 'parent', 'field_level']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(workspace__id=value)

    def filter_field_id(self, queryset, name, value):
        return queryset.filter(field__id=value)

    def filter_field_level(self, queryset, name, value):
        return queryset.filter(field__field_level=value)


class StringViewSet(viewsets.ModelViewSet):
    queryset = models.String.objects.all()
    serializer_class = serializers.StringSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringFilter


class StringDetailFilter(filters.FilterSet):
    string = filters.NumberFilter(method='filter_string_id')
    dimension = filters.NumberFilter(method='filter_dimension_id')

    class Meta:
        model = models.StringDetail
        fields = ['id', 'string', 'dimension', 'dimension_value',
                  'dimension_value_freetext']

    def filter_string_id(self, queryset, name, value):
        return queryset.filter(string__id=value)

    def filter_dimension_id(self, queryset, name, value):
        return queryset.filter(dimension__id=value)


class StringDetailViewSet(viewsets.ModelViewSet):
    queryset = models.StringDetail.objects.all()
    serializer_class = serializers.StringDetailSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringDetailFilter
