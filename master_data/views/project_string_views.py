"""
Views for ProjectString API endpoints (Phase 1 - Critical).
"""

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

from ..models import (
    Project, PlatformAssignment, ProjectString,
    ProjectMember, Workspace, Platform
)
from ..serializers import (
    BulkProjectStringCreateSerializer,
    ProjectStringReadSerializer,
    ProjectStringExpandedSerializer,
    ProjectStringUpdateSerializer,
)
from .mixins import WorkspaceValidationMixin


class BulkCreateProjectStringsView(WorkspaceValidationMixin, views.APIView):
    """
    Bulk create project strings for a specific platform within a project.

    Endpoint: POST /workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/bulk
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, workspace_id, project_id, platform_id):
        """Create multiple project strings in bulk."""
        # Validate workspace access
        workspace = get_object_or_404(Workspace, id=workspace_id)
        if not request.user.has_workspace_access(workspace_id):
            return Response(
                {'error': 'Access denied to this workspace'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate project exists and belongs to workspace
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        # Validate platform exists
        platform = get_object_or_404(Platform, id=platform_id)

        # Validate platform assignment exists
        platform_assignment = get_object_or_404(
            PlatformAssignment,
            project=project,
            platform=platform
        )

        # Validate user has permission (assigned to platform or owner/editor)
        if not self.can_create_strings(request.user, project, platform_assignment):
            return Response(
                {'error': 'You do not have permission to create strings for this platform'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate and create strings
        serializer = BulkProjectStringCreateSerializer(
            data=request.data,
            context={
                'request': request,
                'project': project,
                'platform': platform
            }
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create strings
        created_strings = serializer.save()

        # Return created strings
        return Response({
            'created_count': len(created_strings),
            'strings': ProjectStringReadSerializer(created_strings, many=True).data
        }, status=status.HTTP_201_CREATED)

    def can_create_strings(self, user, project, platform_assignment):
        """Check if user can create strings for this platform."""
        if user.is_superuser:
            return True

        # Check if user is assigned to platform
        if platform_assignment.assigned_members.filter(id=user.id).exists():
            return True

        # Check if user has owner/editor role in project
        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role in ['owner', 'editor']
        except ProjectMember.DoesNotExist:
            return False


class ListProjectStringsView(WorkspaceValidationMixin, views.APIView):
    """
    List project strings for a specific platform within a project.

    Endpoint: GET /workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings

    Query Parameters:
    - field: Filter by field ID
    - parent_field: Filter by parent field ID (returns parent strings for a given field level)
    - parent_uuid: Filter by parent UUID (returns children of a specific parent)
    - search: Search by string value
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id, project_id, platform_id):
        """List project strings with filtering and pagination."""
        # Validate workspace access
        workspace = get_object_or_404(Workspace, id=workspace_id)
        if not request.user.has_workspace_access(workspace_id):
            return Response(
                {'error': 'Access denied to this workspace'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate project exists and belongs to workspace
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        # Validate platform exists
        platform = get_object_or_404(Platform, id=platform_id)

        # Validate platform assignment exists
        get_object_or_404(PlatformAssignment, project=project, platform=platform)

        # Base queryset
        queryset = ProjectString.objects.filter(
            project=project,
            platform=platform
        ).select_related(
            'project', 'platform', 'field', 'rule', 'created_by'
        ).prefetch_related('details')

        # Apply filters
        field_id = request.query_params.get('field')
        if field_id:
            queryset = queryset.filter(field_id=field_id)

        parent_field_id = request.query_params.get('parent_field')
        if parent_field_id:
            queryset = queryset.filter(field_id=parent_field_id, parent__isnull=True)

        parent_uuid = request.query_params.get('parent_uuid')
        if parent_uuid:
            queryset = queryset.filter(parent_uuid=parent_uuid)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(value__icontains=search)

        # Order by field level and value
        queryset = queryset.order_by('field__field_level', 'value')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # Serialize results
        serializer = ProjectStringReadSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'results': serializer.data
        })


class ProjectStringExpandedView(WorkspaceValidationMixin, views.APIView):
    """
    Get expanded project string details with hierarchy and suggestions.

    Endpoint: GET /workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/{string_id}/expanded

    Used for parent string inheritance - when user selects a parent string in grid builder,
    frontend fetches expanded details to populate inherited dimension values.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id, project_id, platform_id, string_id):
        """Get expanded project string."""
        # Validate workspace access
        workspace = get_object_or_404(Workspace, id=workspace_id)
        if not request.user.has_workspace_access(workspace_id):
            return Response(
                {'error': 'Access denied to this workspace'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate project exists and belongs to workspace
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        # Validate platform exists
        platform = get_object_or_404(Platform, id=platform_id)

        # Validate string exists
        project_string = get_object_or_404(
            ProjectString,
            id=string_id,
            project=project,
            platform=platform
        )

        # Serialize with expanded data
        serializer = ProjectStringExpandedSerializer(project_string)

        return Response(serializer.data)


class ProjectStringUpdateView(WorkspaceValidationMixin, views.APIView):
    """
    Update a project string.

    Endpoint: PUT /workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/{string_id}
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, workspace_id, project_id, platform_id, string_id):
        """Update project string."""
        # Validate workspace access
        workspace = get_object_or_404(Workspace, id=workspace_id)
        if not request.user.has_workspace_access(workspace_id):
            return Response(
                {'error': 'Access denied to this workspace'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate project exists and belongs to workspace
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        # Validate platform exists
        platform = get_object_or_404(Platform, id=platform_id)

        # Validate platform assignment exists
        platform_assignment = get_object_or_404(
            PlatformAssignment,
            project=project,
            platform=platform
        )

        # Validate string exists
        project_string = get_object_or_404(
            ProjectString,
            id=string_id,
            project=project,
            platform=platform
        )

        # Validate user has permission
        if not self.can_update_string(request.user, project, platform_assignment):
            return Response(
                {'error': 'You do not have permission to update strings for this platform'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update string
        serializer = ProjectStringUpdateSerializer(
            project_string,
            data=request.data,
            partial=False
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        updated_string = serializer.save()

        # Return updated string with expanded details
        return Response(
            ProjectStringExpandedSerializer(updated_string).data
        )

    def can_update_string(self, user, project, platform_assignment):
        """Check if user can update strings for this platform."""
        if user.is_superuser:
            return True

        # Check if user is assigned to platform
        if platform_assignment.assigned_members.filter(id=user.id).exists():
            return True

        # Check if user has owner/editor role in project
        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role in ['owner', 'editor']
        except ProjectMember.DoesNotExist:
            return False


class ProjectStringDeleteView(WorkspaceValidationMixin, views.APIView):
    """
    Delete a project string.

    Endpoint: DELETE /workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/{string_id}

    Returns 400 Bad Request if string has children (must delete children first).
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, workspace_id, project_id, platform_id, string_id):
        """Delete project string."""
        # Validate workspace access
        workspace = get_object_or_404(Workspace, id=workspace_id)
        if not request.user.has_workspace_access(workspace_id):
            return Response(
                {'error': 'Access denied to this workspace'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate project exists and belongs to workspace
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        # Validate platform exists
        platform = get_object_or_404(Platform, id=platform_id)

        # Validate platform assignment exists
        platform_assignment = get_object_or_404(
            PlatformAssignment,
            project=project,
            platform=platform
        )

        # Validate string exists
        project_string = get_object_or_404(
            ProjectString,
            id=string_id,
            project=project,
            platform=platform
        )

        # Validate user has permission
        if not self.can_delete_string(request.user, project, platform_assignment):
            return Response(
                {'error': 'You do not have permission to delete strings for this platform'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if string has children
        children_count = ProjectString.objects.filter(
            parent_uuid=project_string.string_uuid,
            platform=platform
        ).count()

        if children_count > 0:
            return Response({
                'error': 'Conflict',
                'message': 'String has children and cannot be deleted',
                'details': {
                    'string_id': string_id,
                    'children_count': children_count
                }
            }, status=status.HTTP_409_CONFLICT)

        # Delete string
        project_string.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def can_delete_string(self, user, project, platform_assignment):
        """Check if user can delete strings for this platform."""
        if user.is_superuser:
            return True

        # Check if user is assigned to platform
        if platform_assignment.assigned_members.filter(id=user.id).exists():
            return True

        # Check if user has owner/editor role in project
        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role in ['owner', 'editor']
        except ProjectMember.DoesNotExist:
            return False
