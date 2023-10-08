from rest_framework import viewsets, permissions

from . import serializers
from . import models

# filter
from rest_framework import filters
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


class RuleViewSet(viewsets.ModelViewSet):
    """ViewSet for the Rule class"""

    queryset = models.Rule.objects.all()
    serializer_class = serializers.RuleSerializer
    # permission_classes = [permissions.IsAuthenticated]


class StructureViewSet(viewsets.ModelViewSet):
    """ViewSet for the Structure class"""

    queryset = models.Structure.objects.all()
    serializer_class = serializers.StructureSerializer
    # permission_classes = [permissions.IsAuthenticated]
