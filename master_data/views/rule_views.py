from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from .. import serializers
from .. import models


class RuleFilter(filters.FilterSet):
    # convention = filters.NumberFilter(method='filter_convention_id')
    platform = filters.NumberFilter(method='filter_platform_id')
    field = filters.NumberFilter(method='filter_field_id')

    class Meta:
        model = models.Rule
        fields = [
            'id',
            # 'convention',
            'field',
            'platform'
        ]

    # def filter_convention_id(self, queryset, name, value):
    #     return queryset.filter(convention__id=value)

    def filter_platform_id(self, queryset, name, value):
        return queryset.filter(field__platform__id=value)

    def filter_field_id(self, queryset, name, value):
        return queryset.filter(field__id=value)


class RuleViewSet(viewsets.ModelViewSet):
    queryset = models.Rule.objects.all()
    serializer_class = serializers.RuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleFilter


class RuleDetailFilter(filters.FilterSet):
    # convention = filters.NumberFilter(method='filter_convention_id')
    platform = filters.NumberFilter(method='filter_platform_id')
    field = filters.NumberFilter(method='filter_field_id')

    class Meta:
        model = models.RuleDetail
        fields = [
            'id',
            # 'convention',
            'field',
            'platform'
        ]

    # def filter_convention_id(self, queryset, name, value):
    #     return queryset.filter(convention__id=value)

    def filter_platform_id(self, queryset, name, value):
        return queryset.filter(field__platform__id=value)

    def filter_field_id(self, queryset, name, value):
        return queryset.filter(field__id=value)


class RuleDetailViewSet(viewsets.ModelViewSet):
    queryset = models.RuleDetail.objects.all()
    serializer_class = serializers.RuleDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleDetailFilter


class RuleNestedViewSet(viewsets.ModelViewSet):
    queryset = models.Rule.objects.all()
    serializer_class = serializers.RuleNestedSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleFilter
