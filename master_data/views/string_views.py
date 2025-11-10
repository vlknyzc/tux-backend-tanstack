"""
RESTful API views for strings.
These views implement the design patterns from restful-api-design.md
All endpoints require workspace context for security and isolation.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter

from master_data import models
from master_data.serializers.string import (
    StringWithDetailsSerializer,
    StringWithDetailsReadSerializer
)
from master_data.serializers.bulk_operations import (
    BulkStringCreateSerializer
)
from master_data.permissions import IsAuthenticatedOrDebugReadOnly
from .mixins import WorkspaceValidationMixin
import logging

logger = logging.getLogger(__name__)


class StringWorkspaceFilter(filters.FilterSet):
    """Filter for workspace-scoped strings."""
    submission = filters.NumberFilter(field_name='submission')
    entity = filters.NumberFilter(field_name='entity')
    entity_level = filters.NumberFilter(field_name='entity__entity_level')
    platform = filters.NumberFilter(field_name='rule__platform__id')

    class Meta:
        model = models.String
        fields = ['id', 'submission', 'entity', 'entity_level', 'platform']


@extend_schema(tags=['Strings'])
class StringViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    Workspace-scoped string viewset with embedded details.

    Implements:
    - GET    /api/v1/workspaces/{workspace_id}/strings/
    - POST   /api/v1/workspaces/{workspace_id}/strings/
    - GET    /api/v1/workspaces/{workspace_id}/strings/{id}/
    - DELETE /api/v1/workspaces/{workspace_id}/strings/{id}/

    Note: String values are generated from details, not updated directly.
    """

    queryset = models.String.objects.all()
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringWorkspaceFilter
    http_method_names = ['get', 'post', 'delete',
                         'head', 'options']  # No PUT/PATCH

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.action in ['create']:
            return StringWithDetailsSerializer
        else:
            return StringWithDetailsReadSerializer

    def get_queryset(self):
        """Get workspace-filtered strings with optimized prefetch."""
        queryset = super().get_queryset()

        if not hasattr(queryset, 'model'):
            queryset = models.String.objects.all()

        return queryset.select_related(
            'entity',
            'entity__platform',  # Prevent N+1 query for platform access
            'submission',
            'rule',
            'workspace',
            'created_by',
            'parent'
        ).prefetch_related(
            'string_details__dimension',
            'string_details__dimension_value'
        )

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

    @extend_schema(
        tags=["Strings"],
        parameters=[
            OpenApiParameter(
                name='workspace_id',
                description='Workspace ID',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """List strings in workspace."""
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create string with details (value generated from details)."""
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    def retrieve(self, request, *args, **kwargs):
        """Get string with details."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Strings"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Delete string and all related details."""
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        tags=["Strings"],
        methods=['post'],
        request=BulkStringCreateSerializer,
        summary="Create multiple strings in bulk"
    )
    @action(detail=False, methods=['post'], url_path='bulk')
    @transaction.atomic
    def bulk_create(self, request, workspace_id=None):
        """Create multiple strings in bulk."""
        workspace_id = getattr(request, 'workspace_id', None)

        # Add workspace to each string in the request
        data = request.data.copy()
        if 'strings' in data:
            for string_data in data['strings']:
                string_data['workspace'] = workspace_id

        serializer = BulkStringCreateSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(
            StringWithDetailsReadSerializer(result['strings'], many=True).data,
            status=status.HTTP_201_CREATED
        )