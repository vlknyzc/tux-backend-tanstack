"""
URL patterns for Project API endpoints.

All endpoints are prefixed with /workspaces/{workspace_id}/projects/
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectViewSet,
    BulkCreateProjectStringsView,
    ListProjectStringsView,
    ProjectStringExpandedView,
    ProjectStringUpdateView,
    ProjectStringDeleteView,
    ProjectStringUnlockView,
    BulkUpdateProjectStringsView,
    ExportProjectStringsView,
)


# Create router for ProjectViewSet
router = DefaultRouter()

# Register projects viewset with nested workspace route
# The viewset will handle: list, retrieve, create, update, delete
# URLs will be: /workspaces/{workspace_id}/projects/
router.register(
    r'workspaces/(?P<workspace_id>\d+)/projects',
    ProjectViewSet,
    basename='project'
)

urlpatterns = router.urls

# Add project string endpoints
urlpatterns += [
    # Bulk create strings for a platform
    path(
        'workspaces/<int:workspace_id>/projects/<int:project_id>/platforms/<int:platform_id>/strings/bulk',
        BulkCreateProjectStringsView.as_view(),
        name='project-strings-bulk-create'
    ),

    # List strings for a platform
    path(
        'workspaces/<int:workspace_id>/projects/<int:project_id>/platforms/<int:platform_id>/strings',
        ListProjectStringsView.as_view(),
        name='project-strings-list'
    ),

    # Get expanded string details
    path(
        'workspaces/<int:workspace_id>/projects/<int:project_id>/platforms/<int:platform_id>/strings/<int:string_id>/expanded',
        ProjectStringExpandedView.as_view(),
        name='project-string-expanded'
    ),

    # Update string
    path(
        'workspaces/<int:workspace_id>/projects/<int:project_id>/platforms/<int:platform_id>/strings/<int:string_id>',
        ProjectStringUpdateView.as_view(),
        name='project-string-update'
    ),

    # Delete string (same path as update but DELETE method)
    path(
        'workspaces/<int:workspace_id>/projects/<int:project_id>/platforms/<int:platform_id>/strings/<int:string_id>/delete',
        ProjectStringDeleteView.as_view(),
        name='project-string-delete'
    ),

    # Phase 3 endpoints
    # Unlock string
    path(
        'workspaces/<int:workspace_id>/projects/<int:project_id>/platforms/<int:platform_id>/strings/<int:string_id>/unlock',
        ProjectStringUnlockView.as_view(),
        name='project-string-unlock'
    ),

    # Bulk update strings
    path(
        'workspaces/<int:workspace_id>/projects/<int:project_id>/platforms/<int:platform_id>/strings/bulk-update',
        BulkUpdateProjectStringsView.as_view(),
        name='project-strings-bulk-update'
    ),

    # Export strings
    path(
        'workspaces/<int:workspace_id>/projects/<int:project_id>/platforms/<int:platform_id>/strings/export',
        ExportProjectStringsView.as_view(),
        name='project-strings-export'
    ),
]
