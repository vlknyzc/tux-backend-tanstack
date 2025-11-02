"""
Views for ProjectString API endpoints (Phase 1 - Critical).
"""

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
import csv
import json

from ..models import (
    Project, ProjectString,
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

    def post(self, request, workspace_id, project_id, platform_id, version=None):
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

        # Validate user has permission (owner/editor)
        if not self.can_create_strings(request.user, project):
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

    def can_create_strings(self, user, project):
        """Check if user can create strings for this project."""
        if user.is_superuser:
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

    def get(self, request, workspace_id, project_id, platform_id, version=None):
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

    def get(self, request, workspace_id, project_id, platform_id, string_id, version=None):
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

    def put(self, request, workspace_id, project_id, platform_id, string_id, version=None):
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

        # Validate string exists
        project_string = get_object_or_404(
            ProjectString,
            id=string_id,
            project=project,
            platform=platform
        )

        # Validate user has permission
        if not self.can_update_string(request.user, project):
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

    def can_update_string(self, user, project):
        """Check if user can update strings for this project."""
        if user.is_superuser:
            return True

        # Check if user has owner/editor role in project
        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role in ['owner', 'editor']
        except ProjectMember.DoesNotExist:
            return False


class ProjectStringUnlockView(WorkspaceValidationMixin, views.APIView):
    """
    Unlock an approved string for editing.

    Endpoint: POST /workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/{string_id}/unlock

    Allows editing/deleting approved strings by unlocking them.
    Changes platform status back to draft and requires re-approval.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, workspace_id, project_id, platform_id, string_id, version=None):
        """Unlock string for editing."""
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

        # Validate user has permission
        if not self.can_unlock_string(request.user, project):
            return Response(
                {'error': 'You do not have permission to unlock strings for this project'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get reason from request
        reason = request.data.get('reason', '')

        # Create activity
        from ..models import ProjectActivity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            type='status_changed',
            description=f"unlocked string in platform {platform.name} for editing",
            metadata={
                'platform_id': platform.id,
                'string_id': string_id,
                'reason': reason
            }
        )

        return Response({
            'string_id': string_id,
            'unlocked_at': timezone.now(),
            'unlocked_by': request.user.id,
            'message': 'String unlocked successfully.'
        })

    def can_unlock_string(self, user, project):
        """Check if user can unlock strings for this project."""
        if user.is_superuser:
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

    def delete(self, request, workspace_id, project_id, platform_id, string_id, version=None):
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

        # Validate string exists
        project_string = get_object_or_404(
            ProjectString,
            id=string_id,
            project=project,
            platform=platform
        )

        # Validate user has permission
        if not self.can_delete_string(request.user, project):
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

    def can_delete_string(self, user, project):
        """Check if user can delete strings for this project."""
        if user.is_superuser:
            return True

        # Check if user has owner/editor role in project
        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role in ['owner', 'editor']
        except ProjectMember.DoesNotExist:
            return False


class BulkUpdateProjectStringsView(WorkspaceValidationMixin, views.APIView):
    """
    Bulk update multiple project strings.

    Endpoint: PUT /workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/bulk-update

    Request body: List of string updates
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, workspace_id, project_id, platform_id, version=None):
        """Bulk update project strings."""
        from django.db import transaction
        from ..serializers import ProjectStringUpdateSerializer

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

        # Validate user has permission
        if not self.can_update_strings(request.user, project):
            return Response(
                {'error': 'You do not have permission to update strings for this platform'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get updates from request
        updates = request.data.get('updates', [])

        if not updates:
            return Response(
                {'error': 'No updates provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_strings = []
        errors = []

        with transaction.atomic():
            for update_data in updates:
                string_id = update_data.get('id')

                if not string_id:
                    errors.append({'error': 'Missing string ID', 'data': update_data})
                    continue

                try:
                    # Get string
                    project_string = ProjectString.objects.get(
                        id=string_id,
                        project=project,
                        platform=platform
                    )

                    # Update string
                    serializer = ProjectStringUpdateSerializer(
                        project_string,
                        data=update_data,
                        partial=True
                    )

                    if serializer.is_valid():
                        updated_string = serializer.save()
                        updated_strings.append(updated_string)
                    else:
                        errors.append({
                            'string_id': string_id,
                            'errors': serializer.errors
                        })

                except ProjectString.DoesNotExist:
                    errors.append({
                        'string_id': string_id,
                        'error': 'String not found'
                    })
                except Exception as e:
                    errors.append({
                        'string_id': string_id,
                        'error': str(e)
                    })

        # Create activity
        from ..models import ProjectActivity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            type='strings_generated',
            description=f"bulk updated {len(updated_strings)} strings for {platform.name}",
            metadata={
                'platform_id': platform.id,
                'updated_count': len(updated_strings),
                'error_count': len(errors)
            }
        )

        from ..serializers import ProjectStringReadSerializer
        return Response({
            'updated_count': len(updated_strings),
            'error_count': len(errors),
            'updated_strings': ProjectStringReadSerializer(updated_strings, many=True).data,
            'errors': errors
        })

    def can_update_strings(self, user, project):
        """Check if user can update strings for this project."""
        if user.is_superuser:
            return True

        # Check if user has owner/editor role in project
        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role in ['owner', 'editor']
        except ProjectMember.DoesNotExist:
            return False


class ExportProjectStringsView(WorkspaceValidationMixin, views.APIView):
    """
    Export project strings in various formats.

    Endpoint: GET /workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/export

    Query Parameters:
    - format: csv, json (default: csv)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id, project_id, platform_id, version=None):
        """Export project strings."""
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

        # Get strings
        strings = ProjectString.objects.filter(
            project=project,
            platform=platform
        ).select_related(
            'project', 'platform', 'field', 'rule', 'created_by'
        ).prefetch_related('details__dimension', 'details__dimension_value')

        # Get export format
        export_format = request.query_params.get('format', 'csv').lower()

        if export_format == 'csv':
            return self.export_csv(project, platform, strings)
        elif export_format == 'json':
            return self.export_json(project, platform, strings)
        else:
            return Response(
                {'error': 'Invalid format. Supported formats: csv, json'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def export_csv(self, project, platform, strings):
        """Export strings as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="project_{project.id}_platform_{platform.id}_strings.csv"'

        writer = csv.writer(response)

        # Write header
        writer.writerow([
            'String ID', 'UUID', 'Project', 'Platform', 'Field', 'Field Level',
            'Value', 'Parent UUID', 'Rule', 'Created By', 'Created', 'Last Updated'
        ])

        # Write data
        for string in strings:
            writer.writerow([
                string.id,
                str(string.string_uuid),
                string.project.name,
                string.platform.name,
                string.field.name,
                string.field.field_level,
                string.value,
                str(string.parent_uuid) if string.parent_uuid else '',
                string.rule.name,
                string.created_by.get_full_name() if string.created_by else '',
                string.created.isoformat(),
                string.last_updated.isoformat()
            ])

        return response

    def export_json(self, project, platform, strings):
        """Export strings as JSON."""
        from ..serializers import ProjectStringReadSerializer

        serializer = ProjectStringReadSerializer(strings, many=True)

        export_data = {
            'project': {
                'id': project.id,
                'name': project.name,
                'slug': project.slug
            },
            'platform': {
                'id': platform.id,
                'name': platform.name
            },
            'exported_at': timezone.now().isoformat(),
            'count': strings.count(),
            'strings': serializer.data
        }

        response = HttpResponse(
            json.dumps(export_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="project_{project.id}_platform_{platform.id}_strings.json"'

        return response
