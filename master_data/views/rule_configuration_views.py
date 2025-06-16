import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.conf import settings
import logging

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ..models import Rule
from ..services import (
    DimensionCatalogService,
    InheritanceMatrixService,
    FieldTemplateService,
    RuleService
)
from ..serializers import (
    LightweightRuleSerializer,
    FieldSpecificDataSerializer,
    GenerationPreviewSerializer,
    ValidationSummarySerializer,
    PerformanceMetricsSerializer,
    GenerationPreviewRequestSerializer,
    CacheInvalidationRequestSerializer,
    CompleteRuleSerializer
)
from ..permissions import IsAuthenticatedOrDebugReadOnly

logger = logging.getLogger(__name__)


class LightweightRuleView(APIView):
    """Lightweight endpoint for rule list views and basic operations"""
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    # 15 minutes cache for lightweight data
    @method_decorator(cache_page(15 * 60))
    def get(self, request, rule_id, version=None):
        """Get lightweight rule data"""
        start_time = time.time()

        try:
            # Check rule exists and user has access
            try:
                rule = Rule.objects.get(id=rule_id)
                workspace = getattr(request, 'workspace', None)

                # Validate workspace access
                if not request.user.is_superuser:
                    if workspace and not request.user.has_workspace_access(workspace):
                        raise PermissionDenied(
                            "Access denied to this workspace")

                    # Ensure rule belongs to the same workspace
                    if workspace and rule.workspace_id != workspace:
                        raise PermissionDenied(
                            "Rule not found in current workspace")

            except Rule.DoesNotExist:
                return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)

            lightweight_data = self.rule_service.get_lightweight_rule_data(
                rule_id)

            # Add minimal performance metrics
            lightweight_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'cached': True,
                'workspace': workspace
            }

            serializer = LightweightRuleSerializer(data=lightweight_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FieldSpecificRuleView(APIView):
    """Endpoint for field-specific rule data"""
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    def get(self, request, rule_id, field_id, version=None):
        """Get field-specific rule data"""
        start_time = time.time()

        try:
            # Check rule exists and user has access
            try:
                rule = Rule.objects.get(id=rule_id)
                workspace = getattr(request, 'workspace', None)

                # Validate workspace access
                if not request.user.is_superuser:
                    if workspace and not request.user.has_workspace_access(workspace):
                        raise PermissionDenied(
                            "Access denied to this workspace")

                    # Ensure rule belongs to the same workspace
                    if workspace and rule.workspace_id != workspace:
                        raise PermissionDenied(
                            "Rule not found in current workspace")

            except Rule.DoesNotExist:
                return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)

            field_data = self.rule_service.get_field_specific_data(
                rule_id, field_id)

            # Add performance metrics
            field_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'workspace': workspace
            }

            serializer = FieldSpecificDataSerializer(data=field_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RuleValidationView(APIView):
    """Endpoint for rule validation summary"""
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    def get(self, request, rule_id, version=None):
        """Get comprehensive rule validation summary"""
        start_time = time.time()

        try:
            # Check rule exists and user has access
            try:
                rule = Rule.objects.get(id=rule_id)
                workspace = getattr(request, 'workspace', None)

                # Validate workspace access
                if not request.user.is_superuser:
                    if workspace and not request.user.has_workspace_access(workspace):
                        raise PermissionDenied(
                            "Access denied to this workspace")

                    # Ensure rule belongs to the same workspace
                    if workspace and rule.workspace_id != workspace:
                        raise PermissionDenied(
                            "Rule not found in current workspace")

            except Rule.DoesNotExist:
                return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)

            validation_data = self.rule_service.get_rule_validation_summary(
                rule_id)

            # Add performance metrics
            validation_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'workspace': workspace
            }

            serializer = ValidationSummarySerializer(data=validation_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerationPreviewView(APIView):
    """Endpoint for string generation preview"""
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    def post(self, request):
        """Generate a preview of string generation"""
        start_time = time.time()

        workspace = getattr(request, 'workspace', None)
        if not workspace:
            return Response({'error': 'No workspace context available'}, status=status.HTTP_403_FORBIDDEN)

        # Validate request
        request_serializer = GenerationPreviewRequestSerializer(
            data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        rule = request_serializer.validated_data['rule']
        field = request_serializer.validated_data['field']
        sample_values = request_serializer.validated_data['sample_values']

        try:
            # Check rule exists and user has access
            try:
                rule = Rule.objects.get(id=rule)

                # Validate workspace access
                if not request.user.is_superuser:
                    if not request.user.has_workspace_access(workspace):
                        raise PermissionDenied(
                            "Access denied to this workspace")

                    # Ensure rule belongs to the same workspace
                    if rule.workspace_id != workspace:
                        raise PermissionDenied(
                            "Rule not found in current workspace")

            except Rule.DoesNotExist:
                return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)

            preview_data = self.rule_service.get_generation_preview(
                rule, field, sample_values)

            # Add performance metrics
            preview_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'workspace': workspace
            }

            serializer = GenerationPreviewSerializer(data=preview_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CacheManagementView(APIView):
    """Endpoint for cache management operations"""
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    def post(self, request):
        """Invalidate cache for specified rules"""
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            return Response({'error': 'No workspace context available'}, status=status.HTTP_403_FORBIDDEN)

        # Validate request
        request_serializer = CacheInvalidationRequestSerializer(
            data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        rule_ids = request_serializer.validated_data['rule_ids']

        try:
            # Validate all rules belong to current workspace
            if not request.user.is_superuser:
                rules = Rule.objects.filter(id__in=rule_ids)
                for rule in rules:
                    if rule.workspace_id != workspace:
                        return Response({'error': f'Rule {rule.id} not found in current workspace'},
                                        status=status.HTTP_403_FORBIDDEN)

            # Invalidate caches
            self.rule_service.bulk_invalidate_caches(rule_ids)

            return Response({
                'success': True,
                'message': f'Cache invalidated for {len(rule_ids)} rules',
                'rule_ids': rule_ids,
                'workspace': workspace,
                'timestamp': timezone.now().isoformat()
            })

        except Exception as e:
            return Response({'error': f'Cache invalidation failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, rule_id, version=None):
        """Get performance metrics for a specific rule"""
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            return Response({'error': 'No workspace context available'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Check rule exists and user has access
            try:
                rule = Rule.objects.get(id=rule_id)

                # Validate workspace access
                if not request.user.is_superuser:
                    if not request.user.has_workspace_access(workspace):
                        raise PermissionDenied(
                            "Access denied to this workspace")

                    # Ensure rule belongs to the same workspace
                    if rule.workspace_id != workspace:
                        raise PermissionDenied(
                            "Rule not found in current workspace")

            except Rule.DoesNotExist:
                return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)

            metrics = self.rule_service.get_performance_metrics(rule_id)

            serializer = PerformanceMetricsSerializer(data=metrics)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RuleConfigurationView(APIView):
    """Complete rule configuration endpoint with all data"""
    permission_classes = [IsAuthenticatedOrDebugReadOnly]

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    def get(self, request, rule_id, version=None):
        """Get complete rule configuration data"""
        start_time = time.time()

        workspace = getattr(request, 'workspace', None)

        try:
            # Check rule exists and user has access
            try:
                rule = Rule.objects.get(id=rule_id)

                # Validate workspace access
                if not request.user.is_superuser:
                    if workspace and not request.user.has_workspace_access(workspace):
                        raise PermissionDenied(
                            "Access denied to this workspace")

                    # Ensure rule belongs to the same workspace
                    if workspace and rule.workspace_id != workspace:
                        raise PermissionDenied(
                            "Rule not found in current workspace")

            except Rule.DoesNotExist:
                return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)

            complete_data = self.rule_service.get_complete_rule_data(
                rule_id)

            # Add view-specific performance metrics to the existing ones
            if 'performance_metrics' not in complete_data:
                complete_data['performance_metrics'] = {}

            # Store the view metrics separately to avoid overwriting service metrics
            complete_data['view_performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'workspace': workspace,
                'timestamp': timezone.now().isoformat()
            }

            serializer = CompleteRuleSerializer(data=complete_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
