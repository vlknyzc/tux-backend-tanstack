# myapp/api/views.py

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
from ..permissions import IsAuthenticatedOrDebugReadOnly
from .mixins import WorkspaceValidationMixin


class WorkspaceMixin:
    """
    Mixin to parse `?workspace=` from the querystring (or request attribute)
    and to check access in one place.
    """

    def get_workspace_param(self, param_name='workspace'):
        """
        Get a parameter from request, handling both DRF and Django requests.
        This is a defensive method to handle production issues where DRF request
        wrapper might not be applied properly.
        """
        # Handle both DRF Request (has query_params) and Django WSGIRequest (has GET)
        if hasattr(self.request, 'query_params'):
            return self.request.query_params.get(param_name)
        else:
            return self.request.GET.get(param_name)

    def get_workspace_id(self):
        raw = getattr(self.request, 'workspace', None)
        if not raw:
            raw = self.get_workspace_param('workspace')
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def check_workspace_access(self, workspace_id):
        # Handle both DRF Request and Django WSGIRequest
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        # Check workspace access for non-superusers
        if not user.is_superuser:
            # Some user models might not have has_workspace_access method
            if hasattr(user, 'has_workspace_access'):
                if not user.has_workspace_access(workspace_id):
                    raise PermissionDenied(
                        f"Access denied to workspace {workspace_id}")
            else:
                # Fallback: if method doesn't exist, only allow superusers
                raise PermissionDenied("Workspace access method not available")


#
# ─── DIMENSIONS ─────────────────────────────────────────────────────────────────
#

class DimensionFilter(filters.FilterSet):
    dimension = filters.NumberFilter(field_name='dimension__id')
    workspace = filters.NumberFilter(field_name='workspace__id')

    class Meta:
        model = models.Dimension
        fields = ['id', 'type', 'status', 'workspace', 'dimension']


@extend_schema(tags=['Dimensions'])
class DimensionViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    CRUD + bulk_create for Dimension, scoped per-workspace.
    
    URL: /api/v1/workspaces/{workspace_id}/dimensions/
    """
    queryset = models.Dimension.objects.all()
    serializer_class = serializers.DimensionSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionFilter

    @extend_schema(tags=["Dimensions"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Get dimensions filtered by workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        # WorkspaceValidationMixin already validated access in dispatch()
        if workspace_id:
            return models.Dimension.objects.filter(workspace_id=workspace_id)
        return models.Dimension.objects.none()

    def perform_create(self, serializer):
        """Set workspace from URL path when creating objects."""
        # WorkspaceValidationMixin.perform_create() handles workspace assignment
        # But we still need to check if serializer has workspace field
        workspace_id = self.kwargs.get('workspace_id')
        if workspace_id:
            workspace = models.Workspace.objects.get(id=workspace_id)
            serializer.save(workspace=workspace)
        else:
            super().perform_create(serializer)

    @extend_schema(tags=["Dimensions"])
    @action(detail=False, methods=['post'])
    def bulk_create(self, request, version=None):
        """
        POST /api/v1/workspaces/{workspace_id}/dimensions/bulk_create/
        with body { "dimensions": [ {name, type, …}, … ] }
        
        Workspace ID comes from URL path.
        """
        workspace_id = self.kwargs.get('workspace_id')
        # WorkspaceValidationMixin already validated access in dispatch()
        
        if not workspace_id:
            return Response(
                {'error': 'Workspace ID is required in URL path'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # fetch the Workspace instance once
        workspace_obj = models.Workspace.objects.get(pk=workspace_id)

        serializer = serializers.DimensionBulkCreateSerializer(
            data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        dimensions_data = serializer.validated_data['dimensions']
        # inject workspace into each item
        for d in dimensions_data:
            d['workspace'] = workspace_obj

        results, errors = self._create_dimensions_with_dependencies(
            dimensions_data,
            request.user
        )
        return Response({
            'success_count': len(results),
            'error_count': len(errors),
            'results': results,
            'errors': errors
        })

    def _create_dimensions_with_dependencies(self, dimensions_data, user):
        """
        Two-pass create for handling parent → child in the same batch.
        Each dimension creation is wrapped in its own atomic transaction to allow partial success.
        """
        results = []
        errors = []
        created = {}

        no_parents = [d for d in dimensions_data if '_parent_name' not in d]
        with_parents = [d for d in dimensions_data if '_parent_name' in d]

        # 1) create root dims
        for dim in no_parents:
            try:
                with transaction.atomic():
                    if user.is_authenticated:
                        dim['created_by'] = user
                    obj = models.Dimension.objects.create(**dim)
                    created[obj.name] = obj
                    results.append(self.get_serializer(obj).data)
            except Exception as e:
                errors.append({
                    'dimension_name': dim.get('name', 'Unknown'),
                    'error': str(e)
                })

        # 2) create children
        for dim in with_parents:
            try:
                with transaction.atomic():
                    parent_name = dim.pop('_parent_name')
                    if parent_name not in created:
                        raise ValueError(f"Parent '{parent_name}' not in batch")
                    dim['parent'] = created[parent_name]

                    if user.is_authenticated:
                        dim['created_by'] = user
                    obj = models.Dimension.objects.create(**dim)
                    created[obj.name] = obj
                    results.append(self.get_serializer(obj).data)
            except Exception as e:
                errors.append({
                    'dimension_name': dim.get('name', 'Unknown'),
                    'error': str(e)
                })

        return results, errors


#
# ─── DIMENSION VALUES ────────────────────────────────────────────────────────────
#

class DimensionValueFilter(filters.FilterSet):
    dimension = filters.NumberFilter(field_name='dimension__id')
    workspace = filters.NumberFilter(field_name='workspace__id')

    class Meta:
        model = models.DimensionValue
        fields = ['id', 'dimension', 'workspace', 'value']


@extend_schema(tags=['Dimensions'])
class DimensionValueViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    CRUD + bulk_create for DimensionValue, scoped per-workspace.
    
    URL: /api/v1/workspaces/{workspace_id}/dimension-values/
    """
    queryset = models.DimensionValue.objects.all()
    serializer_class = serializers.DimensionValueSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionValueFilter

    @extend_schema(tags=["Dimensions"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Dimensions"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Get dimension values filtered by workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        # WorkspaceValidationMixin already validated access in dispatch()
        
        if workspace_id:
            queryset = models.DimensionValue.objects.filter(workspace_id=workspace_id)
        else:
            queryset = models.DimensionValue.objects.none()
        
        # Apply select_related optimizations
        return queryset.select_related(
            'dimension__parent',  # For dimension_parent_name
            'parent',             # For parent_name and parent_value
            'created_by',         # For created_by_name
            'workspace'           # For workspace_name
        )

    def perform_create(self, serializer):
        from ..services.constraint_validator import ConstraintValidatorService

        # Get workspace from URL path
        workspace_id = self.kwargs.get('workspace_id')
        if not workspace_id:
            raise PermissionDenied("No workspace context available")
        
        workspace = models.Workspace.objects.get(id=workspace_id)
        # WorkspaceValidationMixin already validated access in dispatch()

        # Validate against dimension constraints
        dimension = serializer.validated_data.get('dimension')
        value = serializer.validated_data.get('value')

        if dimension and value:
            validation_result = ConstraintValidatorService.validate_all_constraints(
                value,
                dimension.id
            )

            if not validation_result['is_valid']:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'error': 'Constraint validation failed',
                    'validation_errors': validation_result['errors']
                })

        kwargs = {'workspace': workspace}
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            kwargs['created_by'] = user
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        from ..services.constraint_validator import ConstraintValidatorService

        instance = self.get_object()
        self.check_workspace_access(instance.workspace_id)

        # Validate against dimension constraints if value is being updated
        dimension = serializer.validated_data.get('dimension', instance.dimension)
        value = serializer.validated_data.get('value', instance.value)

        if dimension and value:
            validation_result = ConstraintValidatorService.validate_all_constraints(
                value,
                dimension.id
            )

            if not validation_result['is_valid']:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'error': 'Constraint validation failed',
                    'validation_errors': validation_result['errors']
                })

        serializer.save()

    @extend_schema(tags=["Dimensions"])
    @action(detail=False, methods=['post'])
    def bulk_create(self, request, version=None):
        """
        POST /api/v1/workspaces/{workspace_id}/dimension-values/bulk_create/
        with body { "dimension_values": [ {...}, ... ] }
        
        Workspace ID comes from URL path.
        """
        workspace_id = self.kwargs.get('workspace_id')
        # WorkspaceValidationMixin already validated access in dispatch()
        
        if not workspace_id:
            return Response(
                {'error': 'Workspace ID is required in URL path'},
                status=status.HTTP_400_BAD_REQUEST
            )

        workspace_obj = models.Workspace.objects.get(pk=workspace_id)

        serializer = serializers.DimensionValueBulkCreateSerializer(
            data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        values_data = serializer.validated_data['dimension_values']
        for v in values_data:
            v['workspace'] = workspace_obj

        try:
            with transaction.atomic():
                results, errors = [], []
                for i, data in enumerate(values_data):
                    try:
                        user = getattr(request, 'user', None)
                        if user and user.is_authenticated:
                            data['created_by'] = user
                        dv = models.DimensionValue.objects.create(**data)
                        results.append(self.get_serializer(dv).data)
                    except Exception as e:
                        errors.append({
                            'index': i,
                            'value': data.get('value', 'Unknown'),
                            'error': str(e)
                        })

                return Response({
                    'success_count': len(results),
                    'error_count': len(errors),
                    'results': results,
                    'errors': errors
                })
        except Exception as e:
            return Response(
                {'error': f'Bulk creation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
