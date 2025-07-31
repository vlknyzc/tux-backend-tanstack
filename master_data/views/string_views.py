from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.conf import settings
from django.db import transaction
from django.core.exceptions import PermissionDenied

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .. import serializers
from .. import models
from ..services import StringGenerationService, NamingConventionError
from ..services.batch_update_service import BatchUpdateService, BatchUpdateError
from ..services.inheritance_service import InheritanceService, InheritanceError
from ..services.conflict_resolution_service import ConflictResolutionService, ConflictResolutionError
from ..permissions import IsAuthenticatedOrDebugReadOnly


class StringFilter(filters.FilterSet):
    field = filters.NumberFilter(method='filter_field')
    field_level = filters.NumberFilter(method='filter_field_level')
    platform = filters.NumberFilter(method='filter_platform')
    rule = filters.NumberFilter(method='filter_rule')
    is_auto_generated = filters.BooleanFilter()
    has_conflicts = filters.BooleanFilter(method='filter_has_conflicts')
    workspace = filters.NumberFilter(field_name='workspace')

    class Meta:
        model = models.String
        fields = ['id', 'field', 'parent',
                  'field_level', 'rule', 'is_auto_generated', 'workspace']

    def filter_field(self, queryset, name, value):
        return queryset.filter(field__id=value)

    def filter_field_level(self, queryset, name, value):
        return queryset.filter(field__field_level=value)

    def filter_platform(self, queryset, name, value):
        return queryset.filter(field__platform__id=value)

    def filter_rule(self, queryset, name, value):
        return queryset.filter(rule__id=value)

    def filter_has_conflicts(self, queryset, name, value):
        if value:
            return queryset.with_conflicts()
        return queryset


class StringViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.StringSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringFilter

    @extend_schema(tags=["Strings"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Get strings filtered by workspace context"""
        # Check if workspace_id is explicitly provided in query params
        workspace = self.request.query_params.get('workspace')

        if workspace:
            # If workspace_id is explicitly provided, filter by it (for both superusers and regular users)
            try:
                workspace = int(workspace)
                # Validate user has access to this workspace (unless superuser)
                if hasattr(self.request, 'user') and not self.request.user.is_superuser:
                    if not self.request.user.has_workspace_access(workspace):
                        # Return empty queryset for unauthorized access
                        return models.String.objects.none()

                # Return queryset filtered by the specified workspace
                return models.String.objects.all_workspaces().filter(
                    workspace=workspace
                ).select_related(
                    'field', 'submission', 'submission__created_by', 'rule', 'field__platform'
                ).prefetch_related('string_details__dimension', 'string_details__dimension_value')

            except (ValueError, TypeError):
                # Invalid workspace_id parameter, return empty queryset
                return models.String.objects.none()

        # Default behavior when no workspace_id is specified
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.String.objects.all_workspaces().select_related(
                'field', 'submission', 'submission__created_by', 'rule', 'field__platform'
            ).prefetch_related('string_details__dimension', 'string_details__dimension_value')

        # For regular users, automatic workspace filtering is applied by managers
        return models.String.objects.all().select_related(
            'field', 'submission', 'submission__created_by', 'rule', 'field__platform'
        ).prefetch_related('string_details__dimension', 'string_details__dimension_value')

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new string"""
        workspace = getattr(self.request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        # Validate user has access to this workspace
        if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace):
            raise PermissionDenied("Access denied to this workspace")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Workspace is auto-set by WorkspaceMixin.save()
        serializer.save(**kwargs)

    @extend_schema(tags=["Strings"])
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new string using business logic."""
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        serializer = serializers.StringGenerationRequestSerializer(
            data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    submission = models.Submission.objects.get(
                        id=serializer.validated_data['submission']
                    )
                    field = models.Field.objects.get(
                        id=serializer.validated_data['field']
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

    @extend_schema(tags=["Strings"])
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

    @extend_schema(tags=["Strings"])
    @action(detail=False, methods=['post'])
    def check_conflicts(self, request):
        """Check for naming conflicts before string creation."""
        serializer = serializers.StringConflictCheckSerializer(
            data=request.data)

        if serializer.is_valid():
            try:
                rule = models.Rule.objects.get(
                    id=serializer.validated_data['rule'])
                field = models.Field.objects.get(
                    id=serializer.validated_data['field'])
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

    @extend_schema(tags=["Strings"])
    @action(detail=False, methods=['post'])
    def bulk_generate(self, request):
        """Generate multiple strings in a single request."""
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

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
                                id=req['field'])
                            dimension_values = req['dimension_values']

                            string = models.String.generate_from_submission(
                                submission, field, dimension_values
                            )

                            string_data = serializers.StringSerializer(
                                string).data
                            results.append({
                                'field': field.id,
                                'string_id': string.id,
                                'string': string_data
                            })

                        except Exception as e:
                            errors.append({
                                'field': req['field'],
                                'error': str(e)
                            })

                    return Response({
                        'total_requested': len(serializer.validated_data['generation_requests']),
                        'successful': len(results),
                        'failed': len(errors),
                        'results': results,
                        'errors': errors
                    }, status=status.HTTP_201_CREATED if results else status.HTTP_400_BAD_REQUEST)

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

    @extend_schema(tags=["Strings"])
    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """Get the complete hierarchy for a string (parents and children)."""
        string = self.get_object()

        # Get all parent hierarchy
        parents = []
        current = string.parent
        while current:
            parents.insert(0, serializers.StringSerializer(current).data)
            current = current.parent

        # Get all children hierarchy
        children = []
        for child in string.children.all():
            children.append(serializers.StringSerializer(child).data)

        return Response({
            'string': serializers.StringSerializer(string).data,
            'parents': parents,
            'children': children,
            'depth_level': len(parents),
            'has_children': bool(children)
        })

    @extend_schema(tags=["Strings"])
    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """Get all strings that have naming conflicts in current workspace."""
        conflicts = models.String.objects.with_conflicts()
        serializer = self.get_serializer(conflicts, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["Strings"])
    @action(detail=True, methods=['get'])
    def expanded(self, request, pk=None, **kwargs):
        """Get expanded string data combining string and string-details."""
        string = self.get_object()
        serializer = serializers.StringExpandedSerializer(
            string, context={'request': request})
        return Response(serializer.data)

    # Phase 4 endpoints
    @extend_schema(tags=["Strings"])
    @action(detail=False, methods=['put'])
    @extend_schema(
        request=serializers.StringBatchUpdateRequestSerializer,
        responses={200: serializers.StringBatchUpdateResponseSerializer}
    )
    def batch_update(self, request, **kwargs):
        """Batch update multiple strings with inheritance management."""
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        serializer = serializers.StringBatchUpdateRequestSerializer(
            data=request.data, context={'request': request}
        )

        if serializer.is_valid():
            try:
                updates = serializer.validated_data['updates']
                options = serializer.validated_data.get('options', {})

                result = BatchUpdateService.batch_update_strings(
                    workspace, updates, request.user, options
                )

                response_serializer = serializers.StringBatchUpdateResponseSerializer(
                    data=result)
                response_serializer.is_valid(raise_exception=True)

                return Response(response_serializer.data, status=status.HTTP_200_OK)

            except BatchUpdateError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Batch update failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["Strings"])
    @action(detail=False, methods=['post'])
    @extend_schema(
        request=serializers.InheritanceImpactRequestSerializer,
        responses={200: serializers.InheritanceImpactResponseSerializer}
    )
    def analyze_impact(self, request, **kwargs):
        """Analyze inheritance impact of proposed string updates."""
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        serializer = serializers.InheritanceImpactRequestSerializer(
            data=request.data, context={'request': request}
        )

        if serializer.is_valid():
            try:
                updates = serializer.validated_data['updates']
                depth = serializer.validated_data.get('depth', 10)

                result = BatchUpdateService.analyze_impact(
                    workspace, updates, depth)

                response_serializer = serializers.InheritanceImpactResponseSerializer(
                    data=result)
                response_serializer.is_valid(raise_exception=True)

                return Response(response_serializer.data, status=status.HTTP_200_OK)

            except (BatchUpdateError, InheritanceError) as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Impact analysis failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["Strings"])
    @action(detail=True, methods=['get'])
    @extend_schema(
        responses={200: serializers.StringHistoryResponseSerializer}
    )
    def history(self, request, pk=None, **kwargs):
        """Get modification history for a string."""
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        try:
            result = BatchUpdateService.get_string_history(int(pk), workspace)

            response_serializer = serializers.StringHistoryResponseSerializer(
                data=result)
            response_serializer.is_valid(raise_exception=True)

            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except BatchUpdateError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'History retrieval failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(tags=["Strings"])
    @action(detail=False, methods=['post'])
    @extend_schema(
        request=serializers.RollbackRequestSerializer,
        responses={200: serializers.RollbackResponseSerializer}
    )
    def rollback(self, request, **kwargs):
        """Rollback strings to previous versions."""
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        serializer = serializers.RollbackRequestSerializer(
            data=request.data, context={'request': request}
        )

        if serializer.is_valid():
            try:
                rollback_type = serializer.validated_data['rollback_type']
                target = serializer.validated_data['target']
                options = serializer.validated_data.get('options', {})

                result = BatchUpdateService.rollback_changes(
                    workspace, rollback_type, target, request.user, options
                )

                response_serializer = serializers.RollbackResponseSerializer(
                    data=result)
                response_serializer.is_valid(raise_exception=True)

                return Response(response_serializer.data, status=status.HTTP_200_OK)

            except BatchUpdateError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Rollback failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StringDetailFilter(filters.FilterSet):
    string = filters.NumberFilter(method='filter_string_id')
    dimension = filters.NumberFilter(method='filter_dimension_id')
    dimension_type = filters.CharFilter(method='filter_dimension_type')
    workspace = filters.NumberFilter(field_name='workspace')

    class Meta:
        model = models.StringDetail
        fields = ['id', 'string', 'dimension', 'dimension_value',
                  'dimension_value_freetext', 'workspace']

    def filter_string_id(self, queryset, name, value):
        return queryset.filter(string__id=value)

    def filter_dimension_id(self, queryset, name, value):
        return queryset.filter(dimension__id=value)

    def filter_dimension_type(self, queryset, name, value):
        return queryset.filter(dimension__dimension_type=value)


class StringDetailViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.StringDetailSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringDetailFilter

    @extend_schema(tags=["Strings"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Get string details filtered by workspace context"""
        # Check if workspace_id is explicitly provided in query params
        workspace = self.request.query_params.get('workspace')

        if workspace:
            # If workspace_id is explicitly provided, filter by it (for both superusers and regular users)
            try:
                workspace_id = int(workspace)
                # Validate user has access to this workspace (unless superuser)
                if hasattr(self.request, 'user') and not self.request.user.is_superuser:
                    if not self.request.user.has_workspace_access(workspace):
                        # Return empty queryset for unauthorized access
                        return models.StringDetail.objects.none()

                # Return queryset filtered by the specified workspace
                return models.StringDetail.objects.all_workspaces().filter(
                    workspace=workspace
                ).select_related(
                    'string', 'dimension', 'dimension_value'
                )

            except (ValueError, TypeError):
                # Invalid workspace_id parameter, return empty queryset
                return models.StringDetail.objects.none()

        # Default behavior when no workspace_id is specified
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.StringDetail.objects.all_workspaces().select_related(
                'string', 'dimension', 'dimension_value'
            )

        # For regular users, automatic workspace filtering is applied by managers
        return models.StringDetail.objects.all().select_related(
            'string', 'dimension', 'dimension_value'
        )

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new string detail"""
        workspace = getattr(self.request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        # Validate user has access to this workspace
        if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace):
            raise PermissionDenied("Access denied to this workspace")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Workspace is auto-set by WorkspaceMixin.save()
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        """Ensure workspace is preserved during updates"""
        # Get the existing instance to preserve its workspace
        instance = self.get_object()

        # Validate user has access to this workspace
        if not self.request.user.is_superuser and not self.request.user.has_workspace_access(instance.workspace):
            raise PermissionDenied("Access denied to this workspace")

        # Ensure workspace is preserved during update
        serializer.save(workspace=instance.workspace)
