# myapp/api/views.py

import logging
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
from .mixins import WorkspaceValidationMixin, QueryParamMixin

logger = logging.getLogger(__name__)


class WorkspaceMixin:
    """
    Mixin to parse `?workspace=` from the querystring (or request attribute)
    and to check access in one place.
    """

    def get_workspace_param(self, param_name='workspace'):
        """
        Get a parameter from request query params.

        DRF Request objects always have query_params attribute,
        so no defensive checks are needed.
        """
        return self.request.query_params.get(param_name)

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
            return models.Dimension.objects.filter(
                workspace_id=workspace_id
            ).select_related(
                'parent',
                'created_by',
                'workspace'
            ).prefetch_related(
                'dimension_values'
            )
        return models.Dimension.objects.none()

    def get_serializer_context(self):
        """Add workspace to serializer context for validation."""
        context = super().get_serializer_context()
        workspace_id = self.kwargs.get('workspace_id')
        if workspace_id:
            try:
                workspace = models.Workspace.objects.get(id=workspace_id)
                context['workspace'] = workspace
            except models.Workspace.DoesNotExist:
                pass
        return context

    def perform_create(self, serializer):
        """Set workspace and created_by when creating objects."""
        # Get workspace from URL path
        workspace_id = self.kwargs.get('workspace_id')
        kwargs = {}

        if workspace_id:
            workspace = models.Workspace.objects.get(id=workspace_id)
            kwargs['workspace'] = workspace

        # Set created_by if user is authenticated
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)

    @extend_schema(tags=["Dimensions"])
    @action(detail=False, methods=['post'])
    def bulk_create(self, request, workspace_id=None, version=None):
        """
        POST /api/v1/workspaces/{workspace_id}/dimensions/bulk_create/
        with body { "dimensions": [ {name, type, …}, … ] }

        Workspace ID comes from URL path.
        """
        if not workspace_id:
            workspace_id = self.kwargs.get('workspace_id')
        # WorkspaceValidationMixin already validated access in dispatch()
        
        if not workspace_id:
            return Response(
                {'error': 'Workspace ID is required in URL path'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # fetch the Workspace instance once
        workspace_obj = models.Workspace.objects.get(pk=workspace_id)

        # Pass workspace context to serializer for validation
        serializer = serializers.DimensionBulkCreateSerializer(
            data=request.data,
            context={'workspace': workspace_obj}
        )
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
                # SECURITY: Log detailed error, return generic message to user
                logger.warning(
                    f"Dimension creation failed for '{dim.get('name', 'Unknown')}': {str(e)}",
                    extra={
                        'dimension_name': dim.get('name'),
                        'workspace_id': workspace_obj.id
                    }
                )
                errors.append({
                    'dimension_name': dim.get('name', 'Unknown'),
                    'error': 'Failed to create dimension'
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
                # SECURITY: Log detailed error, return generic message to user
                logger.warning(
                    f"Dimension creation failed for '{dim.get('name', 'Unknown')}': {str(e)}",
                    extra={
                        'dimension_name': dim.get('name'),
                        'workspace_id': workspace_obj.id
                    }
                )
                errors.append({
                    'dimension_name': dim.get('name', 'Unknown'),
                    'error': 'Failed to create dimension'
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
    def bulk_create(self, request, workspace_id=None, version=None):
        """
        POST /api/v1/workspaces/{workspace_id}/dimension-values/bulk_create/
        with body { "dimension_values": [ {...}, ... ] }

        Workspace ID comes from URL path.
        """
        if not workspace_id:
            workspace_id = self.kwargs.get('workspace_id')
        # WorkspaceValidationMixin already validated access in dispatch()
        
        if not workspace_id:
            return Response(
                {'error': 'Workspace ID is required in URL path'},
                status=status.HTTP_400_BAD_REQUEST
            )

        workspace_obj = models.Workspace.objects.get(pk=workspace_id)

        # Pass workspace context to serializer for validation
        serializer = serializers.DimensionValueBulkCreateSerializer(
            data=request.data,
            context={'workspace': workspace_obj}
        )
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
                        # SECURITY: Log detailed error, return generic message to user
                        logger.warning(
                            f"Dimension value creation failed at index {i}: {str(e)}",
                            extra={
                                'value': data.get('value'),
                                'workspace_id': workspace_id,
                                'index': i
                            }
                        )
                        errors.append({
                            'index': i,
                            'value': data.get('value', 'Unknown'),
                            'error': 'Failed to create dimension value'
                        })

                return Response({
                    'success_count': len(results),
                    'error_count': len(errors),
                    'results': results,
                    'errors': errors
                })
        except Exception as e:
            # SECURITY: Log detailed error but return generic message
            logger.error(
                f'Bulk dimension value creation failed for workspace {workspace_id}: {str(e)}',
                exc_info=True,
                extra={
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'workspace_id': workspace_id,
                    'values_count': len(values_data)
                }
            )
            return Response(
                {'error': 'Bulk creation failed. Please try again or contact support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
