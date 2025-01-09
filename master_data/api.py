from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated

from . import serializers
from . import models

# filter
# from rest_framework import filters
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

### Dimension ###


class DimensionFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')

    class Meta:
        model = models.Dimension
        fields = ['id', 'workspace', 'dimension_type']

    def filter_workspace_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(workspace__id=value)


class DimensionViewSet(viewsets.ModelViewSet):
    """ViewSet for the Dimension class"""

    queryset = models.Dimension.objects.all()
    serializer_class = serializers.DimensionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionFilter

### JunkDimension ###


class JunkDimensionFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    dimension = filters.NumberFilter(method='filter_dimension_id')

    class Meta:
        model = models.JunkDimension
        fields = ['workspace']

    def filter_workspace_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(dimension__workspace__id=value)

    def filter_dimension_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(dimension__id=value)


class JunkDimensionViewSet(viewsets.ModelViewSet):
    """ViewSet for the JunkDimension class"""

    queryset = models.JunkDimension.objects.all()
    serializer_class = serializers.JunkDimensionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = JunkDimensionFilter


### Workspace ###
class WorkspaceViewSet(viewsets.ModelViewSet):
    """ViewSet for the Workspace class"""

    queryset = models.Workspace.objects.all()
    serializer_class = serializers.WorkspaceSerializer
    # permission_classes = [permissions.IsAuthenticated]

### Platform ###


class PlatformViewSet(viewsets.ModelViewSet):
    """ViewSet for the Platform class"""

    queryset = models.Platform.objects.all()
    serializer_class = serializers.PlatformSerializer
    # permission_classes = [permissions.IsAuthenticated]

### Field ###
# class FieldViewSet(viewsets.ModelViewSet):
#     """ViewSet for the Field class"""

#     queryset = models.Field.objects.all()
#     serializer_class = serializers.FieldSerializer
#     # permission_classes = [permissions.IsAuthenticated]


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

### Convention ###


class ConventionFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')

    class Meta:
        model = models.Convention
        fields = ['workspace', 'id']

    def filter_workspace_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(workspace__id=value)


class ConventionViewSet(viewsets.ModelViewSet):
    """ViewSet for the Convention class"""

    queryset = models.Convention.objects.all()
    serializer_class = serializers.ConventionSerializer
    # permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ConventionFilter

    def get_queryset(self):
        """
        Filter conventions by workspace if workspace_id is provided in query params
        """
        queryset = models.Convention.objects.all()
        workspace_id = self.request.query_params.get('workspace_id', None)
        if workspace_id is not None:
            queryset = queryset.filter(workspace_id=workspace_id)
        return queryset


class ConventionPlatformFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    convention = filters.NumberFilter(method='filter_convention_id')

    class Meta:
        model = models.ConventionPlatform
        fields = ['workspace', 'convention']

    def filter_workspace_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(workspace__id=value)

    def filter_convention_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(convention__id=value)


class ConventionPlatformViewSet(viewsets.ModelViewSet):
    """ViewSet for the Convention class"""

    queryset = models.ConventionPlatform.objects.all()
    serializer_class = serializers.ConventionPlatformSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ConventionPlatformFilter

### Structure ###


class StructureFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    convention = filters.NumberFilter(method='filter_convention_id')
    platform = filters.NumberFilter(method='filter_platform_id')
    field = filters.NumberFilter(method='filter_field_id')

    class Meta:
        model = models.Structure
        fields = ['id', 'workspace', 'convention',
                  'field', 'platform']

    def filter_workspace_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(convention__workspace__id=value)

    def filter_convention_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(convention__id=value)

    def filter_platform_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(field__platform__id=value)

    def filter_field_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(field__id=value)


class StructureViewSet(viewsets.ModelViewSet):
    """ViewSet for the Structure class"""

    queryset = models.Structure.objects.all()
    serializer_class = serializers.StructureSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StructureFilter


### PlatformTemplate ###
class PlatformTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for the Structure class"""

    queryset = models.Platform.objects.all()
    serializer_class = serializers.PlatformTemplateSerializer
    # permission_classes = [permissions.IsAuthenticated]


### String ###
class StringFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    field = filters.NumberFilter(method='filter_field_id')
    convention = filters.NumberFilter(method='filter_convention_id')

    class Meta:
        model = models.String
        fields = ['id', 'workspace', 'field', 'parent']

    def filter_workspace_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(workspace__id=value)

    def filter_field_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(field__id=value)

    def filter_convention_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(convention__id=value)


class StringViewSet(viewsets.ModelViewSet):
    """ViewSet for the String class"""

    queryset = models.String.objects.all()
    serializer_class = serializers.StringSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['id', 'workspace', 'field', 'parent']
    filterset_class = StringFilter

### StringItem ###


class StringItemFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    string = filters.NumberFilter(method='filter_string_id')
    structure = filters.NumberFilter(method='filter_structure_id')

    class Meta:
        model = models.StringItem
        fields = ['id', 'workspace', 'string', 'structure', 'dimension_value']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(string__workspace__id=value)

    def filter_string_id(self, queryset, name, value):
        return queryset.filter(string__id=value)

    def filter_structure_id(self, queryset, name, value):
        return queryset.filter(structure__id=value)


class StringItemViewSet(viewsets.ModelViewSet):
    """ViewSet for the StringItem class"""

    queryset = models.StringItem.objects.all()
    serializer_class = serializers.StringItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringItemFilter

    def create(self, request, *args, **kwargs):
        print("\n=== StringItem POST Request Debug ===")
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
