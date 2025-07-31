from rest_framework import viewsets, permissions, response, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.conf import settings
from django.db import transaction, IntegrityError
from django.db.models import Prefetch, Q
from django.core.exceptions import ValidationError, PermissionDenied
import logging

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .. import models
from ..serializers.nested_submission import SubmissionNestedSerializer, SubmissionNestedCreateSerializer
from ..permissions import IsAuthenticatedOrDebugReadOnly

logger = logging.getLogger(__name__)


class SubmissionNestedFilter(filters.FilterSet):
    rule = filters.NumberFilter(field_name='rule')
    status = filters.CharFilter(field_name='status')
    workspace = filters.NumberFilter(field_name='workspace__id')

    class Meta:
        model = models.Submission
        fields = ['id', 'rule', 'status', 'workspace']


class SubmissionNestedViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing submissions with nested strings and string details.
    This endpoint allows CRUD operations on a submission with all its strings
    and string details in a single request.
    """
    serializer_class = SubmissionNestedSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubmissionNestedFilter

    def get_serializer_class(self):
        """
        Return different serializers for different HTTP methods.
        Use simplified serializer for POST requests (without next_field_name/next_field_code).
        """
        if self.action == 'create':
            return SubmissionNestedCreateSerializer
        return SubmissionNestedSerializer

    def get_queryset(self):
        """
        Get submissions with optimized prefetch and workspace filtering
        """
        # Check if workspace is explicitly provided in query params
        workspace = self.request.query_params.get('workspace')

        if workspace:
            # If workspace is explicitly provided, filter by it (for both superusers and regular users)
            try:
                workspace = int(workspace)
                # Validate user has access to this workspace (unless superuser)
                if hasattr(self.request, 'user') and not self.request.user.is_superuser:
                    if not self.request.user.has_workspace_access(workspace):
                        # Return empty queryset for unauthorized access
                        return models.Submission.objects.none()

                # Return queryset filtered by the specified workspace
                return models.Submission.objects.all_workspaces().filter(
                    workspace=workspace
                ).select_related('rule').prefetch_related(
                    'submission_strings',
                    'submission_strings__field',
                    'submission_strings__string_details',
                    'submission_strings__string_details__dimension',
                    'submission_strings__string_details__dimension_value'
                )

            except (ValueError, TypeError):
                # Invalid workspace parameter, return empty queryset
                return models.Submission.objects.none()

        # Default behavior when no workspace is specified
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.Submission.objects.all_workspaces().select_related(
                'rule'
            ).prefetch_related(
                'submission_strings',
                'submission_strings__field',
                'submission_strings__string_details',
                'submission_strings__string_details__dimension',
                'submission_strings__string_details__dimension_value'
            )

        # For regular users, automatic workspace filtering is applied by managers
        return models.Submission.objects.all().select_related(
            'rule'
        ).prefetch_related(
            'submission_strings',
            'submission_strings__field',
            'submission_strings__string_details',
            'submission_strings__string_details__dimension',
            'submission_strings__string_details__dimension_value'
        )

    @extend_schema(tags=["Submissions"])
    def list(self, request, *args, **kwargs):
        """
        Override list to optimize rule detail lookups for all submissions
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Get all submission IDs in the filtered queryset
        submission_ids = list(queryset.values_list('id', flat=True))

        if submission_ids:
            # Get all rules used by these submissions
            rule_ids = list(queryset.values_list(
                'rule_id', flat=True).distinct())

            # Get all dimensions used in string details for these submissions
            dimensions = models.StringDetail.objects.filter(
                string__submission_id__in=submission_ids
            ).values_list('dimension_id', flat=True).distinct()

            # Get all rule details in a single query
            if rule_ids and dimensions:
                rule_details = models.RuleDetail.objects.filter(
                    rule_id__in=rule_ids,
                    dimension_id__in=dimensions
                )

                # Group rule details by rule_id and dimension_id for faster lookup
                # Format: {(rule_id, dimension_id): rule_detail}
                rule_details_dict = {
                    (rd.rule_id, rd.dimension_id): rd for rd in rule_details
                }

                # Attach to the request context
                self.request.rule_details_dict = rule_details_dict

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

    @extend_schema(tags=["Submissions"])
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to optimize rule detail lookups
        """
        instance = self.get_object()

        # When retrieving a single object, we can optimize the rule details lookup
        if instance.rule:
            # Prefetch rule details for this specific submission
            dimensions = models.StringDetail.objects.filter(
                string__submission=instance
            ).values_list('dimension', flat=True).distinct()

            # Get all relevant rule details in a single query
            rule_details = models.RuleDetail.objects.filter(
                rule=instance.rule,
                dimension__in=dimensions
            )

            # Attach the rule details to the request context for serializer to use
            self.request.rule_details = {
                rd.dimension_id: rd for rd in rule_details
            }

        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a submission with nested strings and string details atomically"""
        try:
            logger.info(
                f"Creating nested submission. Payload size: {len(str(request.data))} bytes")
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            logger.error(
                f"IntegrityError in nested submission creation: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return response.Response(
                {
                    'error': 'Data integrity constraint violation. This submission conflicts with existing data.',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            logger.error(
                f"ValidationError in nested submission creation: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return response.Response(
                {
                    'error': 'Validation failed for submission data.',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in nested submission creation: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Request data: {request.data}")
            return response.Response(
                {
                    'error': 'An unexpected error occurred while creating the submission.',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new submission"""
        workspace = getattr(self.request, 'workspace', None)

        # Handle workspace context automatically based on user's access
        if not workspace:
            # Check if workspace is explicitly specified in the request data
            workspace_data = serializer.validated_data.get('workspace')
            if workspace_data:
                workspace = workspace_data.id
                # Verify user has access to this workspace (skip for anonymous users in DEBUG)
                if (self.request.user.is_authenticated and
                    not self.request.user.is_superuser and
                        not self.request.user.has_workspace_access(workspace)):
                    raise PermissionDenied(
                        f"Access denied to workspace {workspace}")
                # Set the workspace context for this request
                self.request.workspace = workspace
            else:
                # Skip workspace auto-determination for anonymous users
                if not self.request.user.is_authenticated:
                    raise PermissionDenied(
                        "Workspace must be specified in the request data for anonymous access.")

                # Try to auto-determine workspace from user's assignments
                user_workspaces = self.request.user.get_accessible_workspaces()

                if self.request.user.is_superuser:
                    raise PermissionDenied(
                        "Superusers must specify 'workspace' in the request data.")
                elif len(user_workspaces) == 1:
                    # User has access to only one workspace - use it automatically
                    workspace = user_workspaces[0].id
                    self.request.workspace = workspace
                elif len(user_workspaces) > 1:
                    raise PermissionDenied(
                        "Multiple workspaces available. Please specify 'workspace' in the request data.")
                else:
                    raise PermissionDenied(
                        "No workspace access available for this user.")

        if not workspace:
            raise PermissionDenied("No workspace context available")

        # Validate user has access to this workspace (skip for anonymous users in DEBUG)
        if (self.request.user.is_authenticated and
            not self.request.user.is_superuser and
                not self.request.user.has_workspace_access(workspace)):
            raise PermissionDenied("Access denied to this workspace")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Workspace is auto-set by WorkspaceMixin.save()
        serializer.save(**kwargs)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update a submission with nested strings and string details atomically"""
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """Partially update a submission with nested strings and string details atomically"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Submissions"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Delete a submission with its related strings and string details atomically"""
        return super().destroy(request, *args, **kwargs)
