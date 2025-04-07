from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from .. import serializers
from .. import models


class StringFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    field = filters.NumberFilter(method='filter_field_id')
    # convention = filters.NumberFilter(method='filter_convention_id')

    class Meta:
        model = models.String
        fields = ['id', 'workspace', 'field', 'parent']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(workspace__id=value)

    def filter_field_id(self, queryset, name, value):
        return queryset.filter(field__id=value)

    # def filter_convention_id(self, queryset, name, value):
    #     return queryset.filter(convention__id=value)


class StringViewSet(viewsets.ModelViewSet):
    queryset = models.String.objects.all()
    serializer_class = serializers.StringSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringFilter


class StringDetailFilter(filters.FilterSet):
    string = filters.NumberFilter(method='filter_string_id')

    class Meta:
        model = models.StringDetail
        fields = ['id', 'string', 'dimension_value',
                  'dimension_value_freetext']

    def filter_string_id(self, queryset, name, value):
        return queryset.filter(string__id=value)


class StringDetailViewSet(viewsets.ModelViewSet):
    queryset = models.StringDetail.objects.all()
    serializer_class = serializers.StringDetailSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringDetailFilter

    def create(self, request, *args, **kwargs):
        print("\n=== StringDetail POST Request Debug ===")
        print("Headers:", request.headers)
        print("Data:", request.data)
        print("Content Type:", request.content_type)
        try:
            response = super().create(request, *args, **kwargs)
            print("Success Response:", response.data)
            return response
        except Exception as e:
            print("Error occurred:", str(e))
            raise
