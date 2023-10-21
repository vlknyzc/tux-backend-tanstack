from rest_framework import viewsets, permissions

from . import serializers
from . import models

# filter
# from rest_framework import filters
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters


class DimensionViewSet(viewsets.ModelViewSet):
    """ViewSet for the Dimension class"""

    queryset = models.Dimension.objects.all()
    serializer_class = serializers.DimensionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workspace__id', 'id', 'dimension_type']


class JunkDimensionViewSet(viewsets.ModelViewSet):
    """ViewSet for the JunkDimension class"""

    queryset = models.JunkDimension.objects.all()
    serializer_class = serializers.JunkDimensionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['dimension__workspace__id']


class WorkspaceViewSet(viewsets.ModelViewSet):
    """ViewSet for the Workspace class"""

    queryset = models.Workspace.objects.all()
    serializer_class = serializers.WorkspaceSerializer
    # permission_classes = [permissions.IsAuthenticated]


class PlatformViewSet(viewsets.ModelViewSet):
    """ViewSet for the Platform class"""

    queryset = models.Platform.objects.all()
    serializer_class = serializers.PlatformSerializer
    # permission_classes = [permissions.IsAuthenticated]


class FieldViewSet(viewsets.ModelViewSet):
    """ViewSet for the Field class"""

    queryset = models.Field.objects.all()
    serializer_class = serializers.FieldSerializer
    # permission_classes = [permissions.IsAuthenticated]


class FieldViewSet(viewsets.ModelViewSet):
    """ViewSet for the Field class"""

    platform = filters.NumberFilter(method='filter_platform_id')

    queryset = models.Field.objects.all()
    serializer_class = serializers.FieldSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['platform', 'id']

    def filter_platform_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(platform__id=value)


class ConventionViewSet(viewsets.ModelViewSet):
    """ViewSet for the Convention class"""

    queryset = models.Convention.objects.all()
    serializer_class = serializers.ConventionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workspace__id',  'id']


# class ConventionSingleViewSet(viewsets.ModelViewSet):
#     """ViewSet for the Convention class"""

#     queryset = models.Convention.objects.all()
#     serializer_class = serializers.ConventionSingleSerializer
#     # permission_classes = [permissions.IsAuthenticated]
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['workspace__id', 'id']


class StructureFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    convention = filters.NumberFilter(method='filter_convention_id')
    platform = filters.NumberFilter(method='filter_platform_id')

    class Meta:
        model = models.Structure
        fields = ['id', 'workspace', 'convention',
                  'field__id', 'platform']

    def filter_workspace_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(convention__workspace__id=value)

    def filter_convention_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(convention__id=value)

    def filter_platform_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(field__platform__id=value)


class StructureViewSet(viewsets.ModelViewSet):
    """ViewSet for the Structure class"""

    queryset = models.Structure.objects.all()
    serializer_class = serializers.StructureSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StructureFilter


class PlatformTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for the Structure class"""

    queryset = models.Platform.objects.all()
    serializer_class = serializers.PlatformTemplateSerializer
    # permission_classes = [permissions.IsAuthenticated]
