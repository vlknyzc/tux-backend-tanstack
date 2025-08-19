"""
RESTful API views for string details.
These views implement the design patterns from restful-api-design.md
All endpoints require workspace context for security and isolation.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter

from master_data import models
from master_data.serializers.string import (
    StringDetailReadSerializer,
    StringDetailWriteSerializer
)
from master_data.serializers.bulk_operations import (
    BulkStringDetailUpdateSerializer
)
from master_data.permissions import IsAuthenticatedOrDebugReadOnly
from .mixins import WorkspaceValidationMixin
import logging

logger = logging.getLogger(__name__)


class StringDetailWorkspaceFilter(filters.FilterSet):
    """Filter for workspace-scoped string details."""
    string = filters.NumberFilter(field_name='string')
    dimension = filters.NumberFilter(field_name='dimension')

    class Meta:
        model = models.StringDetail
        fields = ['id', 'string', 'dimension']


class StringDetailViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    Workspace-scoped string detail viewset.

    Implements:
    - GET    /api/v1/workspaces/{workspace_id}/string-details/
    - POST   /api/v1/workspaces/{workspace_id}/string-details/
    - GET    /api/v1/workspaces/{workspace_id}/string-details/{id}/
    - PATCH  /api/v1/workspaces/{workspace_id}/string-details/{id}/
    - PUT    /api/v1/workspaces/{workspace_id}/string-details/{id}/
    - DELETE /api/v1/workspaces/{workspace_id}/string-details/{id}/

    Updates to string details trigger automatic string regeneration.
    """

    queryset = models.StringDetail.objects.all()
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringDetailWorkspaceFilter

    def get_queryset(self):
        """Get workspace-filtered string details with optimized prefetch."""
        queryset = super().get_queryset()

        if not hasattr(queryset, 'model'):
            queryset = models.StringDetail.objects.all()

        return queryset.select_related(
            'string', 'dimension', 'dimension_value', 'workspace'
        )

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.action in ['create', 'update', 'partial_update']:
            return StringDetailWriteSerializer
        else:
            return StringDetailReadSerializer

    @extend_schema(
        tags=["String Details"],
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
        """List string details in workspace."""
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create string detail (triggers string regeneration)."""
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    def retrieve(self, request, *args, **kwargs):
        """Get string detail."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update string detail (triggers string regeneration)."""
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """Partially update string detail (triggers string regeneration)."""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Delete string detail (triggers string regeneration)."""
        response = super().destroy(request, *args, **kwargs)

        # Note: String regeneration is handled by the signal handlers
        # when the StringDetail is deleted

        return response

    @extend_schema(
        tags=["String Details"],
        methods=['patch'],
        request=BulkStringDetailUpdateSerializer,
        summary="Update multiple string details in bulk"
    )
    @action(detail=False, methods=['patch'], url_path='bulk-update')
    @transaction.atomic
    def bulk_update(self, request, *args, **kwargs):
        """Update multiple string details in bulk."""
        serializer = BulkStringDetailUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.update(None, serializer.validated_data)

        return Response(
            StringDetailReadSerializer(result['details'], many=True).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        tags=["String Details"],
        methods=['post'],
        summary="Create multiple string details in bulk"
    )
    @action(detail=False, methods=['post'], url_path='bulk-create')
    @transaction.atomic
    def bulk_create_action(self, request, *args, **kwargs):
        """Create multiple string details in bulk."""
        # This action allows creating multiple string details
        # Each creation will trigger string regeneration automatically

        workspace_id = getattr(request, 'workspace_id', None)
        details_data = request.data.get('details', [])

        if not details_data:
            return Response(
                {'error': 'No details provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_details = []
        for detail_data in details_data:
            detail_data['workspace'] = workspace_id
            serializer = StringDetailWriteSerializer(
                data=detail_data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            detail = serializer.save()
            created_details.append(detail)

        return Response(
            StringDetailReadSerializer(created_details, many=True).data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        tags=["String Details"],
        methods=['delete'],
        summary="Delete multiple string details in bulk"
    )
    @action(detail=False, methods=['delete'], url_path='bulk-delete')
    @transaction.atomic
    def bulk_delete(self, request, *args, **kwargs):
        """Delete multiple string details in bulk."""
        detail_ids = request.data.get('detail_ids', [])

        if not detail_ids:
            return Response(
                {'error': 'No detail IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        workspace_id = getattr(request, 'workspace_id', None)

        # Validate all details belong to the workspace
        details = models.StringDetail.objects.filter(
            id__in=detail_ids,
            workspace_id=workspace_id
        )

        if details.count() != len(detail_ids):
            return Response(
                {'error': 'Some details do not exist or do not belong to this workspace'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get affected strings for regeneration
        affected_strings = set(detail.string for detail in details)

        # Delete details
        details.delete()

        # Regenerate affected strings
        for string in affected_strings:
            string.regenerate_value()

        return Response(status=status.HTTP_204_NO_CONTENT)


class StringDetailNestedViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    Nested viewset for string details within a string.

    Implements:
    - GET    /api/v1/workspaces/{workspace_id}/strings/{string_id}/details/
    - POST   /api/v1/workspaces/{workspace_id}/strings/{string_id}/details/
    - GET    /api/v1/workspaces/{workspace_id}/strings/{string_id}/details/{detail_id}/
    - PATCH  /api/v1/workspaces/{workspace_id}/strings/{string_id}/details/{detail_id}/
    - DELETE /api/v1/workspaces/{workspace_id}/strings/{string_id}/details/{detail_id}/
    """

    queryset = models.StringDetail.objects.all()
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StringDetailWorkspaceFilter

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.action in ['create', 'update', 'partial_update']:
            return StringDetailWriteSerializer
        else:
            return StringDetailReadSerializer

    def get_string(self):
        """Get the string for this nested resource."""
        workspace_id = getattr(self.request, 'workspace_id')
        string_id = self.kwargs.get('string_id')

        return get_object_or_404(
            models.String,
            id=string_id,
            workspace_id=workspace_id
        )

    def get_queryset(self):
        """Get details for the specific string."""
        string = self.get_string()
        return models.StringDetail.objects.filter(
            string=string
        ).select_related('string', 'dimension', 'dimension_value', 'workspace')

    def perform_create(self, serializer):
        """Set string when creating details."""
        string = self.get_string()
        kwargs = {
            'string': string,
            'workspace': string.workspace
        }

        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)

    @extend_schema(
        tags=["String Details"],
        parameters=[
            OpenApiParameter(
                name='workspace_id',
                description='Workspace ID',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            ),
            OpenApiParameter(
                name='string_id',
                description='String ID',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """List details for string."""
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Add detail to string (triggers string regeneration)."""
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    def retrieve(self, request, *args, **kwargs):
        """Get string detail."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update string detail (triggers string regeneration)."""
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """Partially update string detail (triggers string regeneration)."""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Remove detail from string (triggers string regeneration)."""
        return super().destroy(request, *args, **kwargs)