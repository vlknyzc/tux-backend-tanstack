from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from .. import serializers
from .. import models


class DimensionFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')

    class Meta:
        model = models.Dimension
        fields = ['id', 'workspace', 'dimension_type']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(workspace__id=value)


class DimensionViewSet(viewsets.ModelViewSet):
    queryset = models.Dimension.objects.all()
    serializer_class = serializers.DimensionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionFilter


class DimensionValueFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    dimension = filters.NumberFilter(method='filter_dimension_id')

    class Meta:
        model = models.DimensionValue
        fields = ['workspace']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(dimension__workspace__id=value)

    def filter_dimension_id(self, queryset, name, value):
        return queryset.filter(dimension__id=value)


class DimensionValueViewSet(viewsets.ModelViewSet):
    queryset = models.DimensionValue.objects.all()
    serializer_class = serializers.DimensionValueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionValueFilter
