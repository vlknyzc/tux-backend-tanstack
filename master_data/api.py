from rest_framework import viewsets, permissions

from . import serializers
from . import models


class DimensionViewSet(viewsets.ModelViewSet):
    """ViewSet for the Dimension class"""

    queryset = models.Dimension.objects.all()
    serializer_class = serializers.DimensionSerializer
    # permission_classes = [permissions.IsAuthenticated]


class JunkDimensionViewSet(viewsets.ModelViewSet):
    """ViewSet for the JunkDimension class"""

    queryset = models.JunkDimension.objects.all()
    serializer_class = serializers.JunkDimensionSerializer
    # permission_classes = [permissions.IsAuthenticated]


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
