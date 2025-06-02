from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db import transaction

from .. import serializers
from .. import models
from ..services import StringGenerationService, NamingConventionError


class StringFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    field = filters.NumberFilter(method='filter_field_id')
    field_level = filters.NumberFilter(method='filter_field_level')
    platform_id = filters.NumberFilter(method='filter_platform_id')
    rule_id = filters.NumberFilter(method='filter_rule_id')
    is_auto_generated = filters.BooleanFilter()
    has_conflicts = filters.BooleanFilter(method='filter_has_conflicts')

    class Meta:
        model = models.String
        fields = ['id', 'workspace', 'field', 'parent',
                  'field_level', 'rule_id', 'is_auto_generated']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(workspace__id=value)

    def filter_field_id(self, queryset, name, value):
        return queryset.filter(field__id=value)

    def filter_field_level(self, queryset, name, value):
        return queryset.filter(field__field_level=value)

    def filter_platform_id(self, queryset, name, value):
        return queryset.filter(field__platform__id=value)

    def filter_rule_id(self, queryset, name, value):
        return queryset.filter(rule__id=value)

    def filter_has_conflicts(self, queryset, name, value):
        if value:
            return queryset.with_conflicts()
        return queryset


class StringViewSet(viewsets.ModelViewSet):
    queryset = models.String.objects.all().select_related(
        'field', 'submission', 'rule', 'field__platform'
    ).prefetch_related('string_details__dimension', 'string_details__dimension_value')
    serializer_class = serializers.StringSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringFilter

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new string"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new string using business logic."""
        serializer = serializers.StringGenerationRequestSerializer(
            data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    submission = models.Submission.objects.get(
                        id=serializer.validated_data['submission_id']
                    )
                    field = models.Field.objects.get(
                        id=serializer.validated_data['field_id']
                    )
                    dimension_values = serializer.validated_data['dimension_values']

                    # Create string with auto-generation
                    string = models.String.generate_from_submission(
                        submission, field, dimension_values
                    )

                    # Set parent if provided
                    parent_string_id = serializer.validated_data.get(
                        'parent_string_id')
                    if parent_string_id:
                        parent_string = models.String.objects.get(
                            id=parent_string_id)
                        string.parent = parent_string
                        string.save()

                    response_serializer = self.get_serializer(string)
                    return Response(response_serializer.data, status=status.HTTP_201_CREATED)

            except NamingConventionError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'String generation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate an existing string with new dimension values."""
        string = self.get_object()
        serializer = serializers.StringRegenerationSerializer(
            data=request.data)

        if serializer.is_valid():
            try:
                dimension_values = serializer.validated_data['dimension_values']
                new_value = string.regenerate_value(dimension_values)

                response_serializer = self.get_serializer(string)
                return Response({
                    'message': 'String regenerated successfully',
                    'old_value': string.generation_metadata.get('regenerated_from'),
                    'new_value': new_value,
                    'string': response_serializer.data
                })

            except Exception as e:
                return Response(
                    {'error': f'Regeneration failed: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def check_conflicts(self, request):
        """Check for naming conflicts before string creation."""
        serializer = serializers.StringConflictCheckSerializer(
            data=request.data)

        if serializer.is_valid():
            try:
                rule = models.Rule.objects.get(
                    id=serializer.validated_data['rule_id'])
                field = models.Field.objects.get(
                    id=serializer.validated_data['field_id'])
                proposed_value = serializer.validated_data['proposed_value']
                exclude_string_id = serializer.validated_data.get(
                    'exclude_string_id')

                conflicts = StringGenerationService.check_naming_conflicts(
                    rule, field, proposed_value, exclude_string_id
                )

                return Response({
                    'has_conflicts': bool(conflicts),
                    'conflicts': conflicts,
                    'proposed_value': proposed_value
                })

            except models.Rule.DoesNotExist:
                return Response(
                    {'error': 'Rule not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except models.Field.DoesNotExist:
                return Response(
                    {'error': 'Field not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_generate(self, request):
        """Generate multiple strings in a single request."""
        serializer = serializers.StringBulkGenerationRequestSerializer(
            data=request.data)

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    submission = models.Submission.objects.get(
                        id=serializer.validated_data['submission_id']
                    )

                    results = []
                    errors = []

                    for req in serializer.validated_data['generation_requests']:
                        try:
                            field = models.Field.objects.get(
                                id=req['field_id'])
                            dimension_values = req['dimension_values']

                            string = models.String.generate_from_submission(
                                submission, field, dimension_values
                            )

                            string_serializer = self.get_serializer(string)
                            results.append(string_serializer.data)

                        except Exception as e:
                            errors.append({
                                'field_id': req['field_id'],
                                'error': str(e)
                            })

                    return Response({
                        'success_count': len(results),
                        'error_count': len(errors),
                        'results': results,
                        'errors': errors
                    })

            except models.Submission.DoesNotExist:
                return Response(
                    {'error': 'Submission not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': f'Bulk generation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """Get the full hierarchy for a string."""
        string = self.get_object()
        hierarchy_path = string.get_hierarchy_path()
        child_strings = string.get_child_strings()

        hierarchy_serializer = self.get_serializer(hierarchy_path, many=True)
        children_serializer = self.get_serializer(child_strings, many=True)

        return Response({
            'string_id': string.id,
            'hierarchy_path': hierarchy_serializer.data,
            'child_strings': children_serializer.data,
            'can_have_children': string.can_have_children(),
            'suggested_child_field': string.suggest_child_field().name if string.suggest_child_field() else None
        })

    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """Get all strings with naming conflicts."""
        conflicted_strings = models.String.objects.with_conflicts()
        serializer = self.get_serializer(conflicted_strings, many=True)
        return Response(serializer.data)


class StringDetailFilter(filters.FilterSet):
    string = filters.NumberFilter(method='filter_string_id')
    dimension = filters.NumberFilter(method='filter_dimension_id')
    dimension_type = filters.CharFilter(method='filter_dimension_type')

    class Meta:
        model = models.StringDetail
        fields = ['id', 'string', 'dimension', 'dimension_value',
                  'dimension_value_freetext', 'dimension_type']

    def filter_string_id(self, queryset, name, value):
        return queryset.filter(string__id=value)

    def filter_dimension_id(self, queryset, name, value):
        return queryset.filter(dimension__id=value)

    def filter_dimension_type(self, queryset, name, value):
        return queryset.filter(dimension__type=value)


class StringDetailViewSet(viewsets.ModelViewSet):
    queryset = models.StringDetail.objects.all().select_related(
        'string', 'dimension', 'dimension_value'
    )
    serializer_class = serializers.StringDetailSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringDetailFilter

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new string detail"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
