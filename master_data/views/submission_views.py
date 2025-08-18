"""
RESTful API views for submissions.
These views implement the design patterns from restful-api-design.md
All endpoints require workspace context for security and isolation.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiParameter

from master_data import models
from master_data.serializers.submission import (
    SubmissionWithStringsSerializer,
    SubmissionWithStringsReadSerializer
)
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


class SubmissionWorkspaceFilter(filters.FilterSet):
    """Filter for workspace-scoped submissions."""
    rule = filters.NumberFilter(field_name='rule')
    status = filters.CharFilter(field_name='status')

    class Meta:
        model = models.Submission
        fields = ['id', 'rule', 'status']


class SubmissionViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    Workspace-scoped submission viewset with optional initial_strings support.

    Implements:
    - GET    /api/v1/workspaces/{workspace_id}/submissions/
    - POST   /api/v1/workspaces/{workspace_id}/submissions/
    - GET    /api/v1/workspaces/{workspace_id}/submissions/{id}/
    - PATCH  /api/v1/workspaces/{workspace_id}/submissions/{id}/
    - PUT    /api/v1/workspaces/{workspace_id}/submissions/{id}/
    - DELETE /api/v1/workspaces/{workspace_id}/submissions/{id}/
    """

    queryset = models.Submission.objects.all()
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubmissionWorkspaceFilter

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.action in ['create', 'update', 'partial_update']:
            # Use write serializer for POST/PUT/PATCH
            return SubmissionWithStringsSerializer
        else:
            # Use read serializer for GET operations
            return SubmissionWithStringsReadSerializer

    def get_queryset(self):
        """Get workspace-filtered submissions with optimized prefetch."""
        queryset = super().get_queryset()

        if not hasattr(queryset, 'model'):
            queryset = models.Submission.objects.all()

        return queryset.select_related('rule', 'starting_field', 'created_by', 'workspace').prefetch_related(
            'submission_strings__string_details__dimension',
            'submission_strings__string_details__dimension_value'
        )

    @extend_schema(
        tags=["Submissions"],
        parameters=[
            OpenApiParameter(
                name='workspace_id',
                description='Workspace ID',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            ),
            OpenApiParameter(
                name='include',
                description='Include related data (strings, details)',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """List submissions in workspace."""
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create submission with optional initial strings."""
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    def retrieve(self, request, *args, **kwargs):
        """Get submission details."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update submission."""
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """Partially update submission."""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Delete submission and all related strings/details."""
        return super().destroy(request, *args, **kwargs)


class SubmissionStringViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    Nested viewset for strings within a submission.

    Implements:
    - GET    /api/v1/workspaces/{workspace_id}/submissions/{submission_id}/strings/
    - POST   /api/v1/workspaces/{workspace_id}/submissions/{submission_id}/strings/
    - GET    /api/v1/workspaces/{workspace_id}/submissions/{submission_id}/strings/{string_id}/
    - DELETE /api/v1/workspaces/{workspace_id}/submissions/{submission_id}/strings/{string_id}/
    """

    queryset = models.String.objects.all()
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.action in ['create']:
            return StringWithDetailsSerializer
        else:
            return StringWithDetailsReadSerializer

    def get_submission(self):
        """Get the submission for this nested resource."""
        workspace_id = getattr(self.request, 'workspace_id')
        submission_id = self.kwargs.get('submission_id')

        return get_object_or_404(
            models.Submission,
            id=submission_id,
            workspace_id=workspace_id
        )

    def get_queryset(self):
        """Get strings for the specific submission."""
        submission = self.get_submission()
        return models.String.objects.filter(
            submission=submission
        ).select_related('field', 'submission', 'rule', 'workspace').prefetch_related(
            'string_details__dimension',
            'string_details__dimension_value'
        )

    def perform_create(self, serializer):
        """Set submission when creating strings."""
        submission = self.get_submission()
        kwargs = {
            'submission': submission,
            'workspace': submission.workspace
        }

        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)

    @extend_schema(
        tags=["Submissions"],
        parameters=[
            OpenApiParameter(
                name='workspace_id',
                description='Workspace ID',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            ),
            OpenApiParameter(
                name='submission_id',
                description='Submission ID',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """List strings for submission."""
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Add string to submission."""
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    def retrieve(self, request, *args, **kwargs):
        """Get submission string."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Remove string from submission."""
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        tags=["Submissions"],
        methods=['post'],
        request=BulkStringCreateSerializer,
        summary="Create multiple strings for submission in bulk"
    )
    @action(detail=False, methods=['post'], url_path='bulk')
    @transaction.atomic
    def bulk_create(self, request, *args, **kwargs):
        """Create multiple strings for submission in bulk."""
        submission = self.get_submission()

        # Add submission and workspace to each string in the request
        data = request.data.copy()
        if 'strings' in data:
            for string_data in data['strings']:
                string_data['submission'] = submission.id
                string_data['workspace'] = submission.workspace.id

        serializer = BulkStringCreateSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(
            StringWithDetailsReadSerializer(result['strings'], many=True).data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        tags=["Submissions"],
        methods=['delete'],
        summary="Delete multiple strings for submission in bulk"
    )
    @action(detail=False, methods=['delete'], url_path='bulk')
    @transaction.atomic
    def bulk_delete(self, request, *args, **kwargs):
        """Delete multiple strings for submission in bulk."""
        submission = self.get_submission()
        string_ids = request.data.get('string_ids', [])

        if not string_ids:
            return Response(
                {'error': 'No string IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate all strings belong to the submission
        strings = models.String.objects.filter(
            id__in=string_ids,
            submission=submission
        )

        if strings.count() != len(string_ids):
            return Response(
                {'error': 'Some strings do not exist or do not belong to this submission'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete strings (cascade will handle details)
        strings.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)