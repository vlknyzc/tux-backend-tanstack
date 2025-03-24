from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

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
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionFilter

### DimensionValue ###


class DimensionValueFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    dimension = filters.NumberFilter(method='filter_dimension_id')

    class Meta:
        model = models.DimensionValue
        fields = ['workspace']

    def filter_workspace_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(dimension__workspace__id=value)

    def filter_dimension_id(self, queryset, name, value):
        # Filter based on the workspace id through the related models
        return queryset.filter(dimension__id=value)


class DimensionValueViewSet(viewsets.ModelViewSet):
    """ViewSet for the DimensionValue class"""

    queryset = models.DimensionValue.objects.all()
    serializer_class = serializers.DimensionValueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionValueFilter


### Workspace ###


class WorkspaceFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')

    class Meta:
        model = models.Workspace
        fields = ['id']


class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = models.Workspace.objects.all()
    serializer_class = serializers.WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = WorkspaceFilter

    # def list(self, request, *args, **kwargs):
    #     print(f"Authenticated User: {request.user}")
    #     print(f"Is Authenticated: {request.user.is_authenticated}")
    #     print(f"Queryset: {self.queryset}")
    #     return super().list(request, *args, **kwargs)

### Platform ###


class PlatformViewSet(viewsets.ModelViewSet):
    """ViewSet for the Platform class"""

    queryset = models.Platform.objects.all()
    serializer_class = serializers.PlatformSerializer
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ConventionPlatformFilter


### Rule ###
class RuleFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    convention = filters.NumberFilter(method='filter_convention_id')
    platform = filters.NumberFilter(method='filter_platform_id')
    field = filters.NumberFilter(method='filter_field_id')

    class Meta:
        model = models.Rule
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


class RuleViewSet(viewsets.ModelViewSet):
    """ViewSet for the Rule class"""

    queryset = models.Rule.objects.all()
    serializer_class = serializers.RuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleFilter

    @action(detail=False, methods=['get'])
    def grouped_by_field_level(self, request):
        platform_id = request.query_params.get('platform_id')
        convention_id = request.query_params.get('convention_id')

        if not platform_id or not convention_id:
            return Response(
                {"error": "Both platform_id and convention_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get all structures for the given platform and convention
        structures = models.Structure.objects.filter(
            field__platform_id=platform_id,
            convention_id=convention_id
        ).select_related('field', 'dimension', 'convention', 'field__platform').order_by('field__field_level', 'dimension_order')

        # Group structures by field level
        grouped_data = {}
        for structure in structures:
            field_level = structure.field.field_level
            field_name = structure.field.name

            if field_level not in grouped_data:
                next_field = None
                if structure.field.next_field:
                    next_field = structure.field.next_field.name

                grouped_data[field_level] = {
                    'field_level': field_level,
                    'field_name': field_name,
                    'workspace': structure.dimension.workspace_id,
                    'convention': structure.convention_id,
                    'convention_name': structure.convention.name,
                    'platform': structure.field.platform_id,
                    'platform_name': structure.field.platform.name,
                    'field': structure.field_id,
                    'next_field': next_field,
                    'structures': []
                }

            grouped_data[field_level]['structures'].append(structure)

        # Convert to list and sort by field level
        result = sorted(grouped_data.values(), key=lambda x: x['field_level'])

        serializer = serializers.GroupedStructureSerializer(result, many=True)
        return Response(serializer.data)


### PlatformTemplate ###
class PlatformTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for the Structure class"""

    queryset = models.Platform.objects.all()
    serializer_class = serializers.PlatformTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]


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
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringFilter

### StringItem ###


class StringDetailFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    string = filters.NumberFilter(method='filter_string_id')
    rule = filters.NumberFilter(method='filter_rule_id')

    class Meta:
        model = models.StringDetail
        fields = ['id', 'workspace', 'string', 'rule', 'dimension_value']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(string__workspace__id=value)

    def filter_string_id(self, queryset, name, value):
        return queryset.filter(string__id=value)

    def filter_rule_id(self, queryset, name, value):
        return queryset.filter(rule__id=value)


class StringDetailViewSet(viewsets.ModelViewSet):
    """ViewSet for the StringDetail class"""

    queryset = models.StringDetail.objects.all()
    serializer_class = serializers.StringDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
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

### ConventionPlatformDetail ###


class ConventionPlatformDetailFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')

    class Meta:
        model = models.ConventionPlatform
        fields = ['convention', 'platform', 'workspace']

    def filter_workspace_id(self, queryset, name, value):
        # Filter based on the workspace id through the convention relationship
        return queryset.filter(convention__workspace__id=value)


class ConventionPlatformDetailViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for detailed Convention Platform information including fields"""

    queryset = models.ConventionPlatform.objects.all()
    serializer_class = serializers.ConventionPlatformDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ConventionPlatformDetailFilter


### RuleDetail ###
class RuleDetailFilter(filters.FilterSet):
    rule = filters.NumberFilter(method='filter_rule_id')

    class Meta:
        model = models.RuleDetail
        fields = ['id', 'rule', 'dimension']

    def filter_rule_id(self, queryset, name, value):
        return queryset.filter(rule__id=value)


### Submission ###
class SubmissionFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')

    class Meta:
        model = models.Submission
        fields = ['id', 'workspace']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(workspace__id=value)


class SubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet for the Submission class"""

    queryset = models.Submission.objects.all()
    serializer_class = serializers.SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubmissionFilter


class RuleDetailViewSet(viewsets.ModelViewSet):
    """ViewSet for the RuleDetail class"""

    queryset = models.RuleDetail.objects.all()
    serializer_class = serializers.RuleDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleDetailFilter
