"""
URL patterns for main RESTful API endpoints (submissions, strings, string details).
Implements the design patterns from restful-api-design.md
All endpoints require workspace context for security and isolation.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.main_api import (
    SubmissionViewSet,
    StringViewSet,
    StringDetailViewSet,
    SubmissionStringViewSet,
    StringDetailNestedViewSet
)

# Create the main workspace router
router = DefaultRouter()

# Core resources (require workspace context)
router.register(
    r'workspaces/(?P<workspace_id>[^/.]+)/submissions',
    SubmissionViewSet,
    basename='submissions'
)

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

# Separate router for nested resources
nested_router = DefaultRouter()

# Nested resources for submission strings
nested_router.register(
    r'workspaces/(?P<workspace_id>[^/.]+)/submissions/(?P<submission_id>[^/.]+)/strings',
    SubmissionStringViewSet,
    basename='nested-submission-strings'
)

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
- GET    /api/v1/workspaces/{workspace_id}/submissions/
- POST   /api/v1/workspaces/{workspace_id}/submissions/
- GET    /api/v1/workspaces/{workspace_id}/submissions/{id}/
- PATCH  /api/v1/workspaces/{workspace_id}/submissions/{id}/
- PUT    /api/v1/workspaces/{workspace_id}/submissions/{id}/
- DELETE /api/v1/workspaces/{workspace_id}/submissions/{id}/

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

Nested Resource Endpoints:
- GET    /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/
- POST   /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/
- GET    /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/{string_id}/
- DELETE /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/{string_id}/

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

- POST   /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/bulk/
- DELETE /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/bulk/
"""