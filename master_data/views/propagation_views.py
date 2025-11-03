"""
Views for string propagation functionality.
"""

import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import PermissionDenied
from django.db import transaction

from drf_spectacular.utils import extend_schema, OpenApiParameter

from .. import serializers
from .. import models
from ..services.propagation_service import PropagationService, PropagationError
from ..permissions import IsAuthenticatedOrDebugReadOnly
from .mixins import WorkspaceValidationMixin

logger = logging.getLogger(__name__)


@extend_schema(tags=['Propagation'])
class PropagationJobViewSet(WorkspaceValidationMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing propagation jobs.
    Read-only to maintain audit trail integrity.
    
    URL: /api/v1/workspaces/{workspace_id}/propagation-jobs/
    """
    serializer_class = serializers.PropagationJobSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'processing_method', 'triggered_by']
    ordering = ['-created']

    @extend_schema(tags=["String Propagation"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["String Propagation"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        """Get propagation jobs filtered by workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        
        if workspace_id:
            return models.PropagationJob.objects.filter(
                workspace_id=workspace_id
            ).select_related('workspace', 'triggered_by')
        
        return models.PropagationJob.objects.none()

    @extend_schema(tags=["String Propagation"])
    @action(detail=True, methods=['get'])
    def errors(self, request, pk=None):
        """Get errors for a specific propagation job."""
        job = self.get_object()
        errors = job.errors.all().select_related(
            'string', 'string_detail', 'resolved_by')
        serializer = serializers.PropagationErrorSerializer(errors, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["String Propagation"])
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for propagation jobs."""
        workspace_id = self.kwargs.get('workspace_id')
        if not workspace_id:
            raise PermissionDenied("No workspace context available")

        queryset = self.get_queryset()

        # Calculate summary statistics
        total_jobs = queryset.count()
        completed_jobs = queryset.filter(status='completed').count()
        failed_jobs = queryset.filter(status='failed').count()
        running_jobs = queryset.filter(status='running').count()

        # Average processing time for completed jobs
        completed_with_duration = queryset.filter(
            status='completed',
            started_at__isnull=False,
            completed_at__isnull=False
        )

        avg_duration = None
        if completed_with_duration.exists():
            durations = [
                (job.completed_at - job.started_at).total_seconds()
                for job in completed_with_duration
            ]
            avg_duration = sum(durations) / len(durations)

        return Response({
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'running_jobs': running_jobs,
            'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            'average_duration_seconds': avg_duration
        })


@extend_schema(tags=['Propagation'])
class PropagationErrorViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing propagation errors.
    Allows marking errors as resolved.
    
    URL: /api/v1/workspaces/{workspace_id}/propagation-errors/
    """
    serializer_class = serializers.PropagationErrorSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['error_type', 'resolved', 'is_retryable']
    ordering = ['-created']

    @extend_schema(tags=["String Propagation"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["String Propagation"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["String Propagation"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def get_queryset(self):
        """Get propagation errors filtered by workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        
        if workspace_id:
            return models.PropagationError.objects.filter(
                job__workspace_id=workspace_id
            ).select_related('job', 'string', 'string_detail', 'resolved_by')
        
        return models.PropagationError.objects.none()

    @extend_schema(tags=["String Propagation"])
    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark an error as resolved."""
        error = self.get_object()

        if error.resolved:
            return Response({
                'message': 'Error is already resolved'
            }, status=status.HTTP_400_BAD_REQUEST)

        error.mark_resolved(user=request.user)

        serializer = self.get_serializer(error)
        return Response({
            'message': 'Error marked as resolved',
            'error': serializer.data
        })

    @extend_schema(tags=["String Propagation"])
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed operation."""
        error = self.get_object()

        if not error.is_retryable:
            return Response({
                'error': 'This error is not retryable'
            }, status=status.HTTP_400_BAD_REQUEST)

        if error.retry_count >= 3:  # Max retry limit
            return Response({
                'error': 'Maximum retry limit reached'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Increment retry count
            error.increment_retry_count()

            # Attempt to retry the operation
            # This would typically involve re-queuing the failed operation
            # For now, we'll just mark it as retried

            return Response({
                'message': f'Retry initiated (attempt {error.retry_count})',
                'retry_count': error.retry_count
            })

        except Exception as e:
            # SECURITY: Log detailed error but return generic message
            logger.error(
                f"Retry failed for error {error.id}: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'error_id': error.id,
                    'retry_count': error.retry_count
                }
            )
            return Response({
                'error': 'Retry operation failed. Please try again or contact support.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Propagation'])
class EnhancedStringDetailViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    Enhanced StringDetail ViewSet with propagation control.
    Extends the existing StringDetailViewSet functionality.
    
    URL: /api/v1/workspaces/{workspace_id}/enhanced-string-details/
    """
    serializer_class = serializers.StringDetailUpdateWithPropagationSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['string', 'dimension', 'dimension_value']

    def _get_workspace_from_url(self):
        """Get workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        if not workspace_id:
            raise PermissionDenied("No workspace context available")
        
        from ..models.workspace import Workspace
        try:
            return Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            raise PermissionDenied(f"Workspace {workspace_id} does not exist")

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'batch_update':
            return serializers.StringDetailBatchUpdateRequestSerializer
        elif self.action == 'analyze_impact':
            return serializers.PropagationImpactRequestSerializer
        return super().get_serializer_class()

    @extend_schema(tags=["String Details"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    def update(self, request, *args, **kwargs):
        return self._enhanced_update(request, *args, **kwargs)

    @extend_schema(tags=["String Details"])
    def partial_update(self, request, *args, **kwargs):
        return self._enhanced_update(request, *args, partial=True, **kwargs)

    def get_queryset(self):
        """Get string details filtered by workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        
        if workspace_id:
            return models.StringDetail.objects.filter(
                string__workspace_id=workspace_id
            ).select_related('string', 'dimension', 'dimension_value')
        
        return models.StringDetail.objects.none()

    def _enhanced_update(self, request, partial=False, *args, **kwargs):
        """Enhanced update with propagation control."""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Extract propagation control parameters
        propagate = serializer.validated_data.pop('propagate', True)
        propagation_depth = serializer.validated_data.pop(
            'propagation_depth', 10)
        dry_run = serializer.validated_data.pop('dry_run', False)

        workspace = self._get_workspace_from_url()

        if dry_run:
            # Perform impact analysis without making changes
            return self._handle_dry_run(instance, serializer.validated_data,
                                        propagation_depth, workspace)

        try:
            with transaction.atomic():
                # Save the instance
                self.perform_update(serializer)

                # The enhanced signal handler will handle propagation
                # We just need to prepare the response
                response_data = serializer.data

                # Add propagation summary (would be populated by signal handler)
                response_data['propagation_summary'] = {
                    'propagation_enabled': propagate,
                    'max_depth': propagation_depth,
                    'status': 'completed'
                }

                return Response(response_data)

        except Exception as e:
            # SECURITY: Log detailed error but return generic message
            logger.error(
                f"Enhanced update failed for StringDetail {instance.id}: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'string_detail_id': instance.id,
                    'workspace_id': workspace.id
                }
            )
            return Response({
                'error': 'Update operation failed. Please try again or contact support.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_dry_run(self, instance, validated_data, max_depth, workspace):
        """Handle dry run requests with impact analysis."""
        try:
            # Prepare update data for analysis
            update_data = {
                'string_detail_id': instance.id,
                **validated_data
            }

            # Perform impact analysis
            impact = PropagationService.analyze_impact(
                [update_data], workspace, max_depth
            )

            return Response({
                'dry_run': True,
                'impact_analysis': impact,
                'message': 'Dry run completed - no changes were made'
            })

        except PropagationError as e:
            # SECURITY: Log detailed error but return generic message
            logger.warning(
                f"Impact analysis failed for StringDetail {instance.id}: {str(e)}",
                extra={
                    'string_detail_id': instance.id,
                    'workspace_id': workspace.id,
                    'max_depth': max_depth
                }
            )
            return Response({
                'error': 'Impact analysis failed. Please check your input and try again.'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    @extend_schema(
        tags=["String Details"],
        request=serializers.PropagationImpactRequestSerializer,
        responses={200: serializers.PropagationImpactResponseSerializer}
    )
    def analyze_impact(self, request, **kwargs):
        """Analyze propagation impact without making changes."""
        workspace = self._get_workspace_from_url()

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                string_detail_updates = serializer.validated_data['string_detail_updates']
                max_depth = serializer.validated_data['max_depth']

                impact = PropagationService.analyze_impact(
                    string_detail_updates, workspace, max_depth
                )

                response_serializer = serializers.PropagationImpactResponseSerializer(
                    data=impact
                )
                response_serializer.is_valid(raise_exception=True)

                return Response(response_serializer.data)

            except PropagationError as e:
                # SECURITY: Log detailed error but return generic message
                logger.warning(
                    f"Impact analysis failed: {str(e)}",
                    extra={
                        'user_id': request.user.id if request.user.is_authenticated else None,
                        'workspace_id': workspace.id,
                        'max_depth': max_depth
                    }
                )
                return Response({
                    'error': 'Impact analysis failed. Please check your input and try again.'
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'])
    @extend_schema(
        tags=["String Details"],
        request=serializers.StringDetailBatchUpdateRequestSerializer,
        responses={200: serializers.StringDetailBatchUpdateResponseSerializer}
    )
    def batch_update(self, request, **kwargs):
        """Perform batch updates on multiple StringDetails."""
        workspace = self._get_workspace_from_url()

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                updates = serializer.validated_data['updates']
                options = serializer.validated_data.get('options', {})

                # Execute batch propagation
                result = PropagationService.execute_propagation(
                    updates, workspace, request.user, options
                )

                response_serializer = serializers.StringDetailBatchUpdateResponseSerializer(
                    data=result
                )
                response_serializer.is_valid(raise_exception=True)

                return Response(response_serializer.data)

            except PropagationError as e:
                # SECURITY: Log detailed error but return generic message
                logger.warning(
                    f"Batch update failed: {str(e)}",
                    extra={
                        'user_id': request.user.id if request.user.is_authenticated else None,
                        'workspace_id': workspace.id,
                        'update_count': len(updates)
                    }
                )
                return Response({
                    'error': 'Batch update failed. Please check your input and try again.'
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Propagation'])
class PropagationSettingsViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing user propagation settings.
    
    URL: /api/v1/workspaces/{workspace_id}/propagation-settings/
    """
    serializer_class = serializers.PropagationSettingsSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]

    @extend_schema(tags=["String Propagation"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["String Propagation"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["String Propagation"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["String Propagation"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["String Propagation"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def get_queryset(self):
        """Get propagation settings filtered by workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        
        if workspace_id:
            # Users can only see their own settings
            return models.PropagationSettings.objects.filter(
                workspace_id=workspace_id,
                user=self.request.user
            )
        
        return models.PropagationSettings.objects.none()

    def perform_create(self, serializer):
        """Set user and workspace when creating settings."""
        workspace_id = self.kwargs.get('workspace_id')
        if not workspace_id:
            raise PermissionDenied("No workspace context available")
        
        workspace = models.Workspace.objects.get(id=workspace_id)
        
        serializer.save(user=self.request.user, workspace=workspace)

    @extend_schema(tags=["String Propagation"])
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's settings for current workspace."""
        workspace_id = self.kwargs.get('workspace_id')
        if not workspace_id:
            raise PermissionDenied("No workspace context available")
        
        workspace = models.Workspace.objects.get(id=workspace_id)
        
        settings = models.PropagationSettings.objects.get_for_user_and_workspace(
            request.user, workspace
        )

        serializer = self.get_serializer(settings)
        return Response(serializer.data)
