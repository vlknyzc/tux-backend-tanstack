"""
Views for dimension constraint management.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Max
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from .. import serializers
from .. import models
from ..permissions import IsAuthenticatedOrDebugReadOnly
from ..services.constraint_validator import ConstraintValidatorService
from .dimension_views import WorkspaceMixin


class DimensionConstraintFilter(filters.FilterSet):
    """Filter for dimension constraints."""
    dimension = filters.NumberFilter(field_name='dimension__id')
    constraint_type = filters.CharFilter(field_name='constraint_type')
    is_active = filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = models.DimensionConstraint
        fields = ['dimension', 'constraint_type', 'is_active']


@extend_schema(tags=['Dimension Constraints'])
class DimensionConstraintViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing dimension constraints.

    Provides CRUD operations for constraints with automatic workspace isolation.
    """
    queryset = models.DimensionConstraint.objects.all()
    serializer_class = serializers.DimensionConstraintSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionConstraintFilter

    def get_queryset(self):
        """Filter queryset by workspace."""
        wid = self.get_workspace_id()
        if wid:
            self.check_workspace_access(wid)
            return models.DimensionConstraint.objects.filter(dimension__workspace_id=wid)

        user = getattr(self.request, 'user', None)
        if user and user.is_superuser:
            return models.DimensionConstraint.objects.all()

        # Use workspace filtering through dimension relationship
        return models.DimensionConstraint.objects.select_related('dimension').all()

    def perform_create(self, serializer):
        """Create constraint with workspace validation."""
        dimension = serializer.validated_data.get('dimension')
        if not dimension:
            raise PermissionDenied("Dimension is required")

        # Check workspace access through dimension
        self.check_workspace_access(dimension.workspace_id)

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)

        # Clear constraint cache for the dimension
        ConstraintValidatorService.clear_constraint_cache(dimension.id)

    def perform_update(self, serializer):
        """Update constraint with workspace validation."""
        instance = self.get_object()
        self.check_workspace_access(instance.dimension.workspace_id)

        serializer.save()

        # Clear constraint cache
        ConstraintValidatorService.clear_constraint_cache(instance.dimension.id)

    def perform_destroy(self, instance):
        """Delete constraint with workspace validation."""
        self.check_workspace_access(instance.dimension.workspace_id)
        dimension_id = instance.dimension.id

        instance.delete()

        # Clear constraint cache
        ConstraintValidatorService.clear_constraint_cache(dimension_id)

    @extend_schema(
        tags=["Dimension Constraints"],
        description="Get all constraints for a specific dimension",
        parameters=[
            OpenApiParameter(
                name='dimension_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Dimension ID'
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-dimension/(?P<dimension_id>[^/.]+)')
    def by_dimension(self, request, dimension_id=None, **kwargs):
        """
        GET /api/dimension-constraints/by-dimension/{dimension_id}/

        Get all constraints for a specific dimension.
        """
        try:
            dimension = get_object_or_404(models.Dimension, id=dimension_id)
            self.check_workspace_access(dimension.workspace_id)

            constraints = models.DimensionConstraint.objects.filter(
                dimension=dimension
            ).order_by('order')

            serializer = self.get_serializer(constraints, many=True)
            return Response(serializer.data)

        except models.Dimension.DoesNotExist:
            return Response(
                {'error': f'Dimension with id {dimension_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=["Dimension Constraints"],
        description="Bulk create constraints for a dimension (e.g., applying presets)",
        request=serializers.ConstraintBulkCreateSerializer,
        responses={201: serializers.DimensionConstraintSerializer(many=True)}
    )
    @action(detail=False, methods=['post'], url_path='bulk-create/(?P<dimension_id>[^/.]+)')
    def bulk_create(self, request, dimension_id=None, **kwargs):
        """
        POST /api/dimension-constraints/bulk-create/{dimension_id}/

        Bulk create constraints for a dimension.
        Body: { "constraints": [ {constraint_type, value?, error_message?}, ... ] }
        """
        try:
            dimension = get_object_or_404(models.Dimension, id=dimension_id)
            self.check_workspace_access(dimension.workspace_id)

            serializer = serializers.ConstraintBulkCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            constraints_data = serializer.validated_data['constraints']
            created_constraints = []

            with transaction.atomic():
                # Get current max order
                max_order = models.DimensionConstraint.objects.filter(
                    dimension=dimension
                ).aggregate(Max('order'))['order__max'] or 0

                for i, constraint_data in enumerate(constraints_data):
                    constraint = models.DimensionConstraint(
                        dimension=dimension,
                        constraint_type=constraint_data['constraint_type'],
                        value=constraint_data.get('value'),
                        error_message=constraint_data.get('error_message'),
                        order=max_order + i + 1,
                        is_active=constraint_data.get('is_active', True),
                        created_by=request.user if request.user.is_authenticated else None
                    )
                    constraint.full_clean()
                    constraint.save()
                    created_constraints.append(constraint)

            # Clear constraint cache
            ConstraintValidatorService.clear_constraint_cache(dimension.id)

            result_serializer = serializers.DimensionConstraintSerializer(
                created_constraints,
                many=True
            )
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)

        except models.Dimension.DoesNotExist:
            return Response(
                {'error': f'Dimension with id {dimension_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=["Dimension Constraints"],
        description="Reorder constraints for a dimension",
        request=serializers.ConstraintReorderSerializer,
        responses={200: serializers.DimensionConstraintSerializer(many=True)}
    )
    @action(detail=False, methods=['put'], url_path='reorder/(?P<dimension_id>[^/.]+)')
    def reorder(self, request, dimension_id=None, **kwargs):
        """
        PUT /api/dimension-constraints/reorder/{dimension_id}/

        Reorder constraints for a dimension.
        Body: { "constraint_ids": [3, 1, 2] }  // New order
        """
        try:
            dimension = get_object_or_404(models.Dimension, id=dimension_id)
            self.check_workspace_access(dimension.workspace_id)

            serializer = serializers.ConstraintReorderSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            constraint_ids = serializer.validated_data['constraint_ids']

            # Verify all constraints belong to this dimension
            constraints = models.DimensionConstraint.objects.filter(
                id__in=constraint_ids,
                dimension=dimension
            )

            if constraints.count() != len(constraint_ids):
                return Response(
                    {'error': 'Some constraint IDs do not belong to this dimension or do not exist'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create a mapping of constraint_id to constraint object
            constraint_map = {c.id: c for c in constraints}

            # Update orders
            with transaction.atomic():
                for new_order, constraint_id in enumerate(constraint_ids, start=1):
                    constraint = constraint_map[constraint_id]
                    constraint.order = new_order
                    constraint.save(update_fields=['order'])

            # Clear constraint cache
            ConstraintValidatorService.clear_constraint_cache(dimension.id)

            # Return reordered constraints
            reordered = models.DimensionConstraint.objects.filter(
                dimension=dimension
            ).order_by('order')

            result_serializer = serializers.DimensionConstraintSerializer(
                reordered,
                many=True
            )
            return Response(result_serializer.data)

        except models.Dimension.DoesNotExist:
            return Response(
                {'error': f'Dimension with id {dimension_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=["Dimension Constraints"],
        description="Validate a value against dimension constraints",
        request=serializers.DimensionValueValidationSerializer,
        responses={
            200: OpenApiResponse(
                description="Validation result",
                response={
                    'type': 'object',
                    'properties': {
                        'is_valid': {'type': 'boolean'},
                        'errors': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'constraint_type': {'type': 'string'},
                                    'error_message': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['post'], url_path='validate/(?P<dimension_id>[^/.]+)')
    def validate_value(self, request, dimension_id=None, **kwargs):
        """
        POST /api/dimension-constraints/validate/{dimension_id}/

        Validate a value against dimension constraints.
        Body: { "value": "test-value" }
        """
        try:
            dimension = get_object_or_404(models.Dimension, id=dimension_id)
            self.check_workspace_access(dimension.workspace_id)

            serializer = serializers.DimensionValueValidationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            value = serializer.validated_data['value']

            # Validate against constraints
            validation_result = ConstraintValidatorService.validate_all_constraints(
                value,
                dimension.id
            )

            return Response(validation_result, status=status.HTTP_200_OK)

        except models.Dimension.DoesNotExist:
            return Response(
                {'error': f'Dimension with id {dimension_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=["Dimension Constraints"],
        description="Check existing dimension values for constraint violations",
        responses={
            200: OpenApiResponse(
                description="Constraint violation report",
                response={
                    'type': 'object',
                    'properties': {
                        'has_violations': {'type': 'boolean'},
                        'total_values': {'type': 'integer'},
                        'violating_values': {'type': 'integer'},
                        'violations': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'dimension_value_id': {'type': 'integer'},
                                    'value': {'type': 'string'},
                                    'label': {'type': 'string'},
                                    'errors': {'type': 'array'}
                                }
                            }
                        }
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='violations/(?P<dimension_id>[^/.]+)')
    def check_violations(self, request, dimension_id=None, **kwargs):
        """
        GET /api/dimension-constraints/violations/{dimension_id}/

        Check existing dimension values for constraint violations.
        Useful when adding constraints to dimensions with existing values.
        """
        try:
            dimension = get_object_or_404(models.Dimension, id=dimension_id)
            self.check_workspace_access(dimension.workspace_id)

            violations = ConstraintValidatorService.get_constraint_violations(dimension.id)

            return Response(violations, status=status.HTTP_200_OK)

        except models.Dimension.DoesNotExist:
            return Response(
                {'error': f'Dimension with id {dimension_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
