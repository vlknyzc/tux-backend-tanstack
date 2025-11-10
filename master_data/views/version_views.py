from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.versioning import URLPathVersioning
from datetime import datetime
import logging
from drf_spectacular.utils import extend_schema
from master_data.serializers.rule import (
    APIVersionResponseSerializer,
    APIHealthResponseSerializer,
    VersionDemoResponseSerializer,
    ErrorResponseSerializer
)

logger = logging.getLogger(__name__)


class APIVersionView(APIView):
    """
    Simple view to demonstrate API versioning.
    Returns different responses based on the API version.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = APIVersionResponseSerializer

    @extend_schema(tags=["System"])
    def get(self, request, version=None, format=None):
        detected_version = request.version

        # Debug logging
        logger.info(f"Request path: {request.path}")
        logger.info(f"URL version parameter: {version}")
        logger.info(f"Request.version: {detected_version}")
        logger.info(
            f"Request META: {request.META.get('PATH_INFO', 'Not found')}")

        if detected_version == 'v1':
            return Response({
                'version': detected_version,
                'message': 'Welcome to tuxonomy.com API v1',
                'features': [
                    'Multi-tenant workspace support',
                    'Basic string generation',
                    'Rule management',
                    'Entity hierarchy support'
                ],
                'deprecated_features': [],
                'breaking_changes': [],
                'debug_info': {
                    'request_path': request.path,
                    'url_version_param': version,
                    'detected_version': detected_version
                }
            })
        elif detected_version == 'v2':
            return Response({
                'version': detected_version,
                'message': 'Welcome to tuxonomy.com API v2',
                'features': [
                    'Enhanced multi-tenant workspace support',
                    'Advanced string generation with AI',
                    'Advanced rule management with validation',
                    'Complex entity hierarchy support',
                    'Real-time collaboration features',
                    'Advanced caching and performance optimizations'
                ],
                'deprecated_features': [
                    'Legacy string generation endpoints',
                    'Simple rule validation'
                ],
                'breaking_changes': [
                    'Modified response format for string generation',
                    'Enhanced workspace access control',
                    'New required fields in rule creation'
                ],
                'debug_info': {
                    'request_path': request.path,
                    'detected_version': version
                }
            })
        else:
            return Response({
                'error': 'Unsupported API version',
                'supported_versions': ['v1', 'v2'],
                'debug_info': {
                    'request_path': request.path,
                    'detected_version': version
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class APIHealthView(APIView):
    """
    Health check endpoint that includes version information.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = APIHealthResponseSerializer

    @extend_schema(tags=["System"])
    def get(self, request, version=None, format=None):
        return Response({
            'status': 'healthy',
            'version': request.version or 'unknown',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'cache': 'operational',
            'workspace_detection': 'active',
            'debug_info': {
                'request_path': request.path,
                'url_version_param': version,
                'detected_version': request.version
            }
        })


class VersionDemoView(APIView):
    """
    Demonstration view showing how to implement version-specific behavior.
    This shows how existing endpoints can be enhanced for v2 while maintaining v1 compatibility.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = VersionDemoResponseSerializer

    @extend_schema(tags=["System"])
    def get(self, request, version=None, format=None):
        detected_version = request.version

        # Debug logging
        logger.info(f"Demo view - Request path: {request.path}")
        logger.info(f"Demo view - URL version param: {version}")
        logger.info(f"Demo view - Detected version: {detected_version}")

        # Base data that's common to all versions
        base_data = {
            'message': 'This is a demonstration of version-specific responses',
            'timestamp': datetime.now().isoformat(),
            'debug_info': {
                'request_path': request.path,
                'url_version_param': version,
                'detected_version': detected_version
            }
        }

        if detected_version == 'v1':
            # v1 response format - simple and basic
            return Response({
                **base_data,
                'version': 'v1',
                'data': {
                    'simple_field': 'basic_value',
                    'count': 42
                }
            })
        elif detected_version == 'v2':
            # v2 response format - enhanced with additional fields
            return Response({
                **base_data,
                'version': 'v2',
                'data': {
                    'enhanced_field': 'advanced_value',
                    'count': 42,
                    'metadata': {
                        'created_by': 'system',
                        'last_modified': datetime.now().isoformat(),
                        'tags': ['demo', 'versioning', 'api']
                    },
                    'performance_metrics': {
                        'response_time_ms': 15,
                        'cache_hit': True
                    }
                },
                'links': {
                    'self': f'/api/v2/demo/',
                    'related': f'/api/v2/demo/related/'
                }
            })
        else:
            return Response({
                'error': 'Unsupported API version',
                'supported_versions': ['v1', 'v2'],
                'debug_info': {
                    'request_path': request.path,
                    'detected_version': version
                }
            }, status=status.HTTP_400_BAD_REQUEST)
