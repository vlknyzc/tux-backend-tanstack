import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.conf import settings
import logging

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

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
    CompleteRuleSerializer,
    RuleConfigurationSerializer
)
from ..permissions import IsAuthenticatedOrDebugReadOnly
from ..models.workspace import Workspace

logger = logging.getLogger(__name__)


class WorkspaceScopedRuleViewMixin:
    """Mixin for workspace-scoped rule views that validates workspace access."""
    
    def validate_workspace_and_rule(self, request, rule_id, workspace_id=None):
        """
        Validate workspace access and ensure rule belongs to workspace.
        Returns (rule, workspace_id) tuple.
        
        Args:
            request: DRF request object
            rule_id: ID of the rule to validate
            workspace_id: Workspace ID from URL (required)
        """
        if not workspace_id:
            raise PermissionDenied("No workspace context available. workspace_id is required in URL path.")
        
        # Get user
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required")
        
        # Validate workspace access
        if not user.is_superuser:
            if not user.has_workspace_access(workspace_id):
                raise PermissionDenied(f"Access denied to workspace {workspace_id}")
        
        # Get rule
        try:
            rule = Rule.objects.get(id=rule_id)
        except Rule.DoesNotExist:
            raise Http404(f"Rule {rule_id} not found")
        
        # Ensure rule belongs to workspace
        if rule.workspace_id != workspace_id:
            raise PermissionDenied(
                f"Rule {rule_id} does not belong to workspace {workspace_id}"
            )
        
        return rule, workspace_id


class LightweightRuleView(APIView, WorkspaceScopedRuleViewMixin):
    """
    Lightweight endpoint for rule list views and basic operations.
    
    URL: /api/v1/workspaces/{workspace_id}/rules/{rule_id}/lightweight/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LightweightRuleSerializer

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    # 15 minutes cache for lightweight data
    @method_decorator(cache_page(15 * 60))
    @extend_schema(tags=["Rule Configuration"])
    def get(self, request, workspace_id, rule_id, version=None):
        """Get lightweight rule data"""
        start_time = time.time()

        try:
            # Validate workspace and rule access
            rule, workspace_id = self.validate_workspace_and_rule(
                request, rule_id, workspace_id
            )

            lightweight_data = self.rule_service.get_lightweight_rule_data(
                rule_id)

            # Add minimal performance metrics
            lightweight_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'cached': True,
                'workspace': workspace_id
            }

            serializer = LightweightRuleSerializer(data=lightweight_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Rule.DoesNotExist:
            return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FieldSpecificRuleView(APIView, WorkspaceScopedRuleViewMixin):
    """
    Endpoint for field-specific rule data.
    
    URL: /api/v1/workspaces/{workspace_id}/rules/{rule_id}/fields/{field_id}/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FieldSpecificDataSerializer

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    @extend_schema(tags=["Rule Configuration"])
    def get(self, request, workspace_id, rule_id, field_id, version=None):
        """Get field-specific rule data"""
        start_time = time.time()

        try:
            # Validate workspace and rule access
            rule, workspace_id = self.validate_workspace_and_rule(
                request, rule_id, workspace_id
            )

            field_data = self.rule_service.get_field_specific_data(
                rule_id, field_id)

            # Add performance metrics
            field_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'workspace': workspace_id
            }

            serializer = FieldSpecificDataSerializer(data=field_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Rule.DoesNotExist:
            return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RuleValidationView(APIView, WorkspaceScopedRuleViewMixin):
    """
    Endpoint for rule validation summary.
    
    URL: /api/v1/workspaces/{workspace_id}/rules/{rule_id}/validation/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ValidationSummarySerializer

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    @extend_schema(tags=["Rule Configuration"])
    def get(self, request, workspace_id, rule_id, version=None):
        """Get comprehensive rule validation summary"""
        start_time = time.time()

        try:
            # Validate workspace and rule access
            rule, workspace_id = self.validate_workspace_and_rule(
                request, rule_id, workspace_id
            )

            validation_data = self.rule_service.get_rule_validation_summary(
                rule_id)

            # Add performance metrics
            validation_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'workspace': workspace_id
            }

            serializer = ValidationSummarySerializer(data=validation_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Rule.DoesNotExist:
            return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerationPreviewView(APIView, WorkspaceScopedRuleViewMixin):
    """
    Endpoint for string generation preview.
    
    URL: /api/v1/workspaces/{workspace_id}/rules/generation-preview/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GenerationPreviewSerializer

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    @extend_schema(tags=["Rule Configuration"])
    def post(self, request, workspace_id):
        """Generate string preview based on rule and sample values"""
        start_time = time.time()

        # Validate request
        request_serializer = GenerationPreviewRequestSerializer(
            data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        rule_id = request_serializer.validated_data['rule']
        field = request_serializer.validated_data['field']
        sample_values = request_serializer.validated_data['sample_values']

        try:
            # Validate workspace and rule access
            rule, workspace_id = self.validate_workspace_and_rule(
                request, rule_id, workspace_id
            )

            preview_data = self.rule_service.get_generation_preview(
                rule, field, sample_values)

            # Add performance metrics
            preview_data['performance_metrics'] = {
                'generation_time_ms': (time.time() - start_time) * 1000,
                'workspace': workspace_id
            }

            serializer = GenerationPreviewSerializer(data=preview_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response({'error': 'Serialization error', 'details': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Rule.DoesNotExist:
            return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return Response({'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CacheManagementView(APIView, WorkspaceScopedRuleViewMixin):
    """
    Endpoint for cache management operations.
    
    URLs:
    - POST /api/v1/workspaces/{workspace_id}/rules/cache/invalidate/
    - GET /api/v1/workspaces/{workspace_id}/rules/{rule_id}/metrics/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PerformanceMetricsSerializer

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    @extend_schema(tags=["Rule Configuration"])
    def post(self, request, workspace_id):
        """Invalidate cache for specified rules"""
        # Validate request
        request_serializer = CacheInvalidationRequestSerializer(
            data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        rule_ids = request_serializer.validated_data['rule_ids']

        try:
            # Get user
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                raise PermissionDenied("Authentication required")

            # Validate workspace access
            if not user.is_superuser:
                if not user.has_workspace_access(workspace_id):
                    raise PermissionDenied(f"Access denied to workspace {workspace_id}")

            # Validate all rules belong to current workspace
            rules = Rule.objects.filter(id__in=rule_ids)
            for rule in rules:
                if rule.workspace_id != workspace_id:
                    return Response(
                        {'error': f'Rule {rule.id} does not belong to workspace {workspace_id}'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            # Invalidate caches
            self.rule_service.bulk_invalidate_caches(rule_ids)

            return Response({
                'success': True,
                'message': f'Cache invalidated for {len(rule_ids)} rules',
                'rule_ids': rule_ids,
                'workspace': workspace_id,
                'timestamp': timezone.now().isoformat()
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'error': f'Cache invalidation failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(tags=["Rule Configuration"])
    def get(self, request, workspace_id, rule_id, version=None):
        """Get performance metrics for a specific rule"""
        try:
            # Validate workspace and rule access
            rule, workspace_id = self.validate_workspace_and_rule(
                request, rule_id, workspace_id
            )

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


class RuleConfigurationView(APIView, WorkspaceScopedRuleViewMixin):
    """
    Complete rule configuration endpoint with all data.
    
    URL: /api/v1/workspaces/{workspace_id}/rules/{rule_id}/configuration/
    """
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    serializer_class = RuleConfigurationSerializer

    def __init__(self):
        super().__init__()
        self.rule_service = RuleService()

    @extend_schema(
        summary="Get Rule Configuration",
        description="Retrieve complete rule configuration data including fields, dimensions, and dimension values",
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the workspace",
                required=True
            ),
            OpenApiParameter(
                name="rule_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the rule to get configuration for",
                required=True
            ),
        ],
        responses={
            200: RuleConfigurationSerializer,
            403: {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Access denied to this workspace"}
                }
            },
            404: {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Rule not found"}
                }
            },
            500: {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Internal server error"}
                }
            }
        },
        examples=[
            OpenApiExample(
                "Success Response",
                value={
                    "id": 22,
                    "name": "Shopping",
                    "slug": "shopping-1",
                    "platform": {
                        "id": 12,
                        "name": "Amazon Ads",
                        "slug": "amazon-ads"
                    },
                    "workspace": {
                        "id": 2,
                        "name": "Client 1"
                    },
                    "fields": [
                        {
                            "id": 50,
                            "name": "Advertiser",
                            "level": 1,
                            "next_field_id": 51,
                            "next_field_name": "Campaign",
                            "field_items": [
                                {
                                    "id": 1,
                                    "dimension_id": 22,
                                    "order": 1,
                                    "is_required": True,
                                    "is_inherited": False,
                                    "inherits_from_field_item": None,
                                    "prefix": None,
                                    "suffix": None,
                                    "delimiter": None
                                }
                            ]
                        }
                    ],
                    "dimensions": {
                        "22": {
                            "id": 22,
                            "name": "Country",
                            "type": "list",
                            "description": ""
                        }
                    },
                    "dimension_values": {
                        "22": [
                            {
                                "id": 13,
                                "dimension_id": 22,
                                "value": "tr",
                                "label": "Turkey",
                                "utm": "tr",
                                "description": "",
                                "parent": None,
                                "has_parent": False,
                                "parent_dimension": None
                            }
                        ]
                    },
                    "generated_at": "2025-07-06T13:56:16.403076Z",
                    "created_by": {
                        "id": 1,
                        "name": "John Doe"
                    },
                    "performance_metrics": {
                        "generation_time_ms": 45.2,
                        "cached": True,
                        "workspace": 2
                    }
                },
                response_only=True,
                status_codes=["200"]
            )
        ],
        tags=["Rules"]
    )
    @method_decorator(cache_page(15 * 60))  # 15 minutes cache
    def get(self, request, workspace_id, rule_id, version=None):
        """Get complete rule configuration data"""
        start_time = time.time()

        try:
            # Validate workspace and rule access
            rule, workspace_id = self.validate_workspace_and_rule(
                request, rule_id, workspace_id
            )

            # Get configuration data from service
            configuration_data = self.rule_service.get_rule_configuration_data(
                rule_id)

            # Add performance metrics
            configuration_data['performance_metrics'] = {
                'generation_time_ms': round((time.time() - start_time) * 1000, 2),
                'cached': True,
                'workspace': workspace_id
            }

            # Validate and serialize response
            serializer = RuleConfigurationSerializer(data=configuration_data)
            if not serializer.is_valid():
                logger.error(
                    f"RuleConfigurationSerializer validation failed for rule {rule_id}: {serializer.errors}")

                # Clear cache if there's a serialization error
                self.rule_service.clear_rule_configuration_cache(rule_id)

                return Response(
                    {'error': 'Serialization error', 'details': serializer.errors},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(serializer.validated_data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Rule.DoesNotExist:
            return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(
                f"Unexpected error in rule configuration endpoint: {str(e)}")

            # Clear cache on unexpected errors
            try:
                self.rule_service.clear_rule_configuration_cache(rule_id)
            except:
                pass  # Don't let cache clearing errors affect the main error response

            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def force_clear_cache(self, rule_id: int):
        """Force clear cache for testing purposes"""
        try:
            self.rule_service.clear_rule_configuration_cache(rule_id)
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache for rule {rule_id}: {str(e)}")
            return False
