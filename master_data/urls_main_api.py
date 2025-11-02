"""
URL patterns for main RESTful API endpoints (strings, string details).
Implements the design patterns from restful-api-design.md
All endpoints require workspace context for security and isolation.

NOTE: Submission endpoints have been deprecated in favor of Projects.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.string_views import StringViewSet
from .views.string_detail_views import (
    StringDetailViewSet,
    StringDetailNestedViewSet
)
from .views.multi_operations_views import MultiOperationsViewSet

# Create the main workspace router
router = DefaultRouter()

# Core resources (require workspace context)
router.register(
    r'workspaces/(?P<workspace_id>[^/.]+)/strings',
    StringViewSet,
    basename='strings'
)

router.register(
    r'workspaces/(?P<workspace_id>[^/.]+)/string-details',
    StringDetailViewSet,
    basename='string-details'
)

# Multi-operation endpoint for atomic operations
router.register(
    r'workspaces/(?P<workspace_id>[^/.]+)/multi-operations',
    MultiOperationsViewSet,
    basename='multi-operations'
)

# Separate router for nested resources
nested_router = DefaultRouter()

# Nested resources for string details
nested_router.register(
    r'workspaces/(?P<workspace_id>[^/.]+)/strings/(?P<string_id>[^/.]+)/details',
    StringDetailNestedViewSet,
    basename='nested-string-details'
)

# URL patterns
urlpatterns = [
    # Main API endpoints
    path('', include(router.urls)),

    # Nested endpoints
    path('', include(nested_router.urls)),
]

"""
This creates the following URL patterns:

Core Resource Endpoints:
- GET    /api/v1/workspaces/{workspace_id}/strings/
- POST   /api/v1/workspaces/{workspace_id}/strings/
- GET    /api/v1/workspaces/{workspace_id}/strings/{id}/
- DELETE /api/v1/workspaces/{workspace_id}/strings/{id}/

- GET    /api/v1/workspaces/{workspace_id}/string-details/
- POST   /api/v1/workspaces/{workspace_id}/string-details/
- GET    /api/v1/workspaces/{workspace_id}/string-details/{id}/
- PATCH  /api/v1/workspaces/{workspace_id}/string-details/{id}/
- PUT    /api/v1/workspaces/{workspace_id}/string-details/{id}/
- DELETE /api/v1/workspaces/{workspace_id}/string-details/{id}/

- POST   /api/v1/workspaces/{workspace_id}/multi-operations/execute/
- POST   /api/v1/workspaces/{workspace_id}/multi-operations/validate/

Nested Resource Endpoints:
- GET    /api/v1/workspaces/{workspace_id}/strings/{id}/details/
- POST   /api/v1/workspaces/{workspace_id}/strings/{id}/details/
- GET    /api/v1/workspaces/{workspace_id}/strings/{id}/details/{detail_id}/
- PATCH  /api/v1/workspaces/{workspace_id}/strings/{id}/details/{detail_id}/
- DELETE /api/v1/workspaces/{workspace_id}/strings/{id}/details/{detail_id}/

Bulk Operations:
- POST   /api/v1/workspaces/{workspace_id}/strings/bulk/
- POST   /api/v1/workspaces/{workspace_id}/string-details/bulk/
- PATCH  /api/v1/workspaces/{workspace_id}/string-details/bulk/
- DELETE /api/v1/workspaces/{workspace_id}/string-details/bulk/

NOTE: Submission endpoints have been removed. Use Project endpoints instead:
- For submissions → /api/v1/workspaces/{workspace_id}/projects/
"""