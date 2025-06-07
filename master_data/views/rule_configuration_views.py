import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.core.cache import cache
import logging

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

logger = logging.getLogger(__name__)


class LightweightRuleView(APIView):
    """Lightweight endpoint for rule list views and basic operations"""

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    # 15 minutes cache for lightweight data
    @method_decorator(cache_page(15 * 60))
    def get(self, request, rule_id):
        """Get lightweight rule data"""
        start_time = time.time()

        try:
            lightweight_data = self.rule_service.get_lightweight_rule_data(
                rule_id)

            # Add minimal performance metrics
            lightweight_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'cached': True,
            }

            serializer = LightweightRuleSerializer(data=lightweight_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FieldSpecificRuleView(APIView):
    """Endpoint for field-specific rule data"""

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    def get(self, request, rule_id, field_id):
        """Get field-specific rule data"""
        start_time = time.time()

        try:
            field_data = self.rule_service.get_field_specific_data(
                rule_id, field_id)

            # Add performance metrics
            field_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
            }

            serializer = FieldSpecificDataSerializer(data=field_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RuleValidationView(APIView):
    """Endpoint for rule validation summary"""

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    def get(self, request, rule_id):
        """Get comprehensive rule validation summary"""
        start_time = time.time()

        try:
            validation_data = self.rule_service.get_rule_validation_summary(
                rule_id)

            # Add performance metrics
            validation_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
            }

            serializer = ValidationSummarySerializer(data=validation_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerationPreviewView(APIView):
    """Endpoint for string generation preview"""

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    def post(self, request):
        """Generate a preview of string generation"""
        start_time = time.time()

        # Validate request
        request_serializer = GenerationPreviewRequestSerializer(
            data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        rule_id = request_serializer.validated_data['rule_id']
        field_id = request_serializer.validated_data['field_id']
        sample_values = request_serializer.validated_data['sample_values']

        try:
            preview_data = self.rule_service.get_generation_preview(
                rule_id, field_id, sample_values)

            # Add performance metrics
            preview_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
            }

            serializer = GenerationPreviewSerializer(data=preview_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CacheManagementView(APIView):
    """Endpoint for cache management operations"""

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    def post(self, request):
        """Invalidate cache for specified rules"""
        # Validate request
        request_serializer = CacheInvalidationRequestSerializer(
            data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        rule_ids = request_serializer.validated_data['rule_ids']

        try:
            # Invalidate caches
            self.rule_service.bulk_invalidate_caches(rule_ids)

            return Response({
                'success': True,
                'message': f'Cache invalidated for {len(rule_ids)} rules',
                'rule_ids': rule_ids,
                'timestamp': timezone.now().isoformat()
            })

        except Exception as e:
            return Response({'error': f'Cache invalidation failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, rule_id):
        """Get performance metrics for a rule"""
        try:
            metrics = self.rule_service.get_performance_metrics(rule_id)
            serializer = PerformanceMetricsSerializer(metrics)
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': f'Failed to get metrics: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RuleConfigurationView(APIView):
    """
    Rule Configuration Endpoint

    Provides optimized rule configuration with:
    - O(1) inheritance lookup tables
    - Pre-computed constraint mappings
    - Indexed metadata for instant access
    - Comprehensive relationship maps

    This endpoint eliminates all array searches and provides hash-map based
    lookups for maximum frontend performance.
    """

    def get(self, request, rule_id):
        try:
            rule_service = RuleService()
            complete_data = rule_service.get_complete_rule_data(
                rule_id)

            serializer = CompleteRuleSerializer(
                data=complete_data)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(
                    f"Rule configuration serialization errors: {serializer.errors}")
                return Response(
                    {'error': 'Data serialization failed',
                        'details': serializer.errors},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in RuleConfigurationView: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
