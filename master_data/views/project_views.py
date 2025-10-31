"""
Views for Project management API endpoints.
"""

from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from ..models import (
    Project, PlatformAssignment, ProjectMember,
    ProjectActivity, ApprovalHistory, Workspace
)
from ..serializers import (
    ProjectListSerializer, ProjectDetailSerializer,
    ProjectCreateSerializer, ProjectUpdateSerializer,
    SubmitForApprovalSerializer, ApproveSerializer, RejectSerializer
)
from .mixins import WorkspaceValidationMixin


class ProjectViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    ViewSet for Project CRUD operations.

    Supports:
    - List projects (GET /workspaces/{workspace_id}/projects/)
    - Get project detail (GET /workspaces/{workspace_id}/projects/{id}/)
    - Create project (POST /workspaces/{workspace_id}/projects/)
    - Update project (PUT /workspaces/{workspace_id}/projects/{id}/)
    - Delete project (DELETE /workspaces/{workspace_id}/projects/{id}/)
    - Submit for approval (POST /workspaces/{workspace_id}/projects/{id}/submit-for-approval/)
    - Approve project (POST /workspaces/{workspace_id}/projects/{id}/approve/)
    - Reject project (POST /workspaces/{workspace_id}/projects/{id}/reject/)
    """

    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        """Get projects for the workspace."""
        workspace_id = self.kwargs.get('workspace_id')
        queryset = Project.objects.filter(workspace_id=workspace_id)

        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Search by name or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        # Prefetch related data for better performance
        queryset = queryset.select_related('workspace', 'owner').prefetch_related(
            'platform_assignments__platform',
            'platform_assignments__assigned_members',
            'team_members__user',
            'activities',
            'strings'
        )

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'retrieve':
            return ProjectDetailSerializer
        elif self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        elif self.action == 'submit_for_approval':
            return SubmitForApprovalSerializer
        elif self.action == 'approve':
            return ApproveSerializer
        elif self.action == 'reject':
            return RejectSerializer
        return ProjectDetailSerializer

    def perform_create(self, serializer):
        """Create project and set workspace from URL."""
        workspace_id = self.kwargs.get('workspace_id')
        workspace = get_object_or_404(Workspace, id=workspace_id)

        # Validate user has access to workspace
        if not self.request.user.has_workspace_access(workspace_id):
            raise PermissionError("Access denied to this workspace")

        serializer.save(workspace=workspace)

    def update(self, request, *args, **kwargs):
        """Override update to return proper serializer for response."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # Use ProjectDetailSerializer for response
        response_serializer = ProjectDetailSerializer(instance, context=self.get_serializer_context())
        return Response(response_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to return proper serializer for response."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        """
        Delete project.

        Only project owners or workspace admins can delete projects.
        """
        # Check permissions
        if not self.can_delete_project(instance):
            raise PermissionError(
                "Only project owners or workspace admins can delete projects"
            )

        instance.delete()

    def can_delete_project(self, project):
        """Check if user can delete project."""
        user = self.request.user

        # Superusers can delete anything
        if user.is_superuser:
            return True

        # Check if user is workspace admin
        workspace_role = user.get_workspace_role(project.workspace_id)
        if workspace_role == 'admin':
            return True

        # Check if user is project owner
        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role == 'owner'
        except ProjectMember.DoesNotExist:
            return False

    @action(detail=True, methods=['post'], url_path='submit-for-approval')
    def submit_for_approval(self, request, workspace_id=None, id=None):
        """
        Submit project for approval.

        Changes approval_status from 'draft' or 'rejected' to 'pending_approval'.
        """
        project = self.get_object()

        # Validate current status
        if project.approval_status not in ['draft', 'rejected']:
            return Response(
                {'error': 'Project must be in draft or rejected status to submit for approval'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user has permission (owner or editor)
        if not self.can_submit_for_approval(project):
            return Response(
                {'error': 'Only project owners or editors can submit for approval'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update project status
        project.approval_status = 'pending_approval'
        project.save(update_fields=['approval_status', 'last_updated'])

        # Create approval history
        ApprovalHistory.objects.create(
            project=project,
            user=request.user,
            action='submitted',
            comment=serializer.validated_data.get('comment', '')
        )

        # Create activity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            type='submitted_for_approval',
            description='submitted the project for approval'
        )

        return Response({
            'id': project.id,
            'approval_status': project.approval_status,
            'submitted_at': timezone.now(),
            'submitted_by': request.user.id
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, workspace_id=None, id=None):
        """
        Approve project.

        Changes approval_status from 'pending_approval' to 'approved'.
        """
        project = self.get_object()

        # Validate current status
        if project.approval_status != 'pending_approval':
            return Response(
                {'error': 'Project must be in pending_approval status to approve'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user has permission (workspace admin)
        if not self.can_approve_project(project):
            return Response(
                {'error': 'Only workspace admins can approve projects'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update project status
        project.approval_status = 'approved'
        project.approved_by = request.user
        project.approved_at = timezone.now()
        project.save(update_fields=[
            'approval_status', 'approved_by', 'approved_at', 'last_updated'
        ])

        # Create approval history
        ApprovalHistory.objects.create(
            project=project,
            user=request.user,
            action='approved',
            comment=serializer.validated_data.get('comment', '')
        )

        # Create activity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            type='approved',
            description='approved the project'
        )

        return Response({
            'id': project.id,
            'approval_status': project.approval_status,
            'approved_at': project.approved_at,
            'approved_by': request.user.id
        })

    @action(detail=True, methods=['post'])
    def reject(self, request, workspace_id=None, id=None):
        """
        Reject project.

        Changes approval_status from 'pending_approval' to 'rejected'.
        """
        project = self.get_object()

        # Validate current status
        if project.approval_status != 'pending_approval':
            return Response(
                {'error': 'Project must be in pending_approval status to reject'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user has permission (workspace admin)
        if not self.can_approve_project(project):
            return Response(
                {'error': 'Only workspace admins can reject projects'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update project status
        project.approval_status = 'rejected'
        project.rejected_by = request.user
        project.rejected_at = timezone.now()
        project.rejection_reason = serializer.validated_data['reason']
        project.save(update_fields=[
            'approval_status', 'rejected_by', 'rejected_at', 'rejection_reason', 'last_updated'
        ])

        # Create approval history
        ApprovalHistory.objects.create(
            project=project,
            user=request.user,
            action='rejected',
            comment=serializer.validated_data['reason']
        )

        # Create activity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            type='rejected',
            description='rejected the project'
        )

        return Response({
            'id': project.id,
            'approval_status': project.approval_status,
            'rejected_at': project.rejected_at,
            'rejected_by': request.user.id,
            'rejection_reason': project.rejection_reason
        })

    def can_submit_for_approval(self, project):
        """Check if user can submit project for approval."""
        user = self.request.user

        if user.is_superuser:
            return True

        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role in ['owner', 'editor']
        except ProjectMember.DoesNotExist:
            return False

    def can_approve_project(self, project):
        """Check if user can approve/reject project."""
        user = self.request.user

        if user.is_superuser:
            return True

        # Check if user is workspace admin
        workspace_role = user.get_workspace_role(project.workspace_id)
        return workspace_role == 'admin'


class PlatformAssignmentApprovalView(WorkspaceValidationMixin, views.APIView):
    """
    Views for platform-level approval operations.

    Supports:
    - Submit platform for approval
    - Approve platform
    - Reject platform
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, workspace_id, project_id, platform_id, action):
        """Handle platform approval actions."""
        # Validate workspace access
        workspace = get_object_or_404(Workspace, id=workspace_id)
        if not request.user.has_workspace_access(workspace_id):
            raise PermissionError("Access denied to this workspace")

        # Validate project exists and belongs to workspace
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        # Validate platform assignment exists
        platform_assignment = get_object_or_404(
            PlatformAssignment,
            project=project,
            platform_id=platform_id
        )

        # Route to appropriate handler
        if action == 'submit-for-approval':
            return self.submit_for_approval(request, platform_assignment)
        elif action == 'approve':
            return self.approve(request, platform_assignment)
        elif action == 'reject':
            return self.reject(request, platform_assignment)
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def submit_for_approval(self, request, platform_assignment):
        """Submit platform assignment for approval."""
        # Validate current status
        if platform_assignment.approval_status not in ['draft', 'rejected']:
            return Response(
                {'error': 'Platform must be in draft or rejected status to submit for approval'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user has permission (assigned to platform or owner/editor)
        if not self.can_submit_platform(request.user, platform_assignment):
            return Response(
                {'error': 'Only assigned members or project owners/editors can submit for approval'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = SubmitForApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update platform assignment status
        platform_assignment.approval_status = 'pending_approval'
        platform_assignment.save(update_fields=['approval_status', 'last_updated'])

        # Create approval history
        ApprovalHistory.objects.create(
            platform_assignment=platform_assignment,
            user=request.user,
            action='submitted',
            comment=serializer.validated_data.get('comment', '')
        )

        # Create project activity
        ProjectActivity.objects.create(
            project=platform_assignment.project,
            user=request.user,
            type='submitted_for_approval',
            description=f"submitted platform {platform_assignment.platform.name} for approval",
            metadata={'platform_id': platform_assignment.platform.id}
        )

        return Response({
            'platform_assignment_id': platform_assignment.id,
            'approval_status': platform_assignment.approval_status,
            'submitted_at': timezone.now(),
            'submitted_by': request.user.id
        })

    def approve(self, request, platform_assignment):
        """Approve platform assignment."""
        # Validate current status
        if platform_assignment.approval_status != 'pending_approval':
            return Response(
                {'error': 'Platform must be in pending_approval status to approve'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user has permission (workspace admin)
        if not self.can_approve_platform(request.user, platform_assignment):
            return Response(
                {'error': 'Only workspace admins can approve platforms'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update platform assignment status
        platform_assignment.approval_status = 'approved'
        platform_assignment.approved_by = request.user
        platform_assignment.approved_at = timezone.now()
        platform_assignment.save(update_fields=[
            'approval_status', 'approved_by', 'approved_at', 'last_updated'
        ])

        # Create approval history
        ApprovalHistory.objects.create(
            platform_assignment=platform_assignment,
            user=request.user,
            action='approved',
            comment=serializer.validated_data.get('comment', '')
        )

        # Create project activity
        ProjectActivity.objects.create(
            project=platform_assignment.project,
            user=request.user,
            type='approved',
            description=f"approved platform {platform_assignment.platform.name}",
            metadata={'platform_id': platform_assignment.platform.id}
        )

        return Response({
            'platform_assignment_id': platform_assignment.id,
            'approval_status': platform_assignment.approval_status,
            'approved_at': platform_assignment.approved_at,
            'approved_by': request.user.id
        })

    def reject(self, request, platform_assignment):
        """Reject platform assignment."""
        # Validate current status
        if platform_assignment.approval_status != 'pending_approval':
            return Response(
                {'error': 'Platform must be in pending_approval status to reject'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user has permission (workspace admin)
        if not self.can_approve_platform(request.user, platform_assignment):
            return Response(
                {'error': 'Only workspace admins can reject platforms'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update platform assignment status
        platform_assignment.approval_status = 'rejected'
        platform_assignment.rejected_by = request.user
        platform_assignment.rejected_at = timezone.now()
        platform_assignment.rejection_reason = serializer.validated_data['reason']
        platform_assignment.save(update_fields=[
            'approval_status', 'rejected_by', 'rejected_at', 'rejection_reason', 'last_updated'
        ])

        # Create approval history
        ApprovalHistory.objects.create(
            platform_assignment=platform_assignment,
            user=request.user,
            action='rejected',
            comment=serializer.validated_data['reason']
        )

        # Create project activity
        ProjectActivity.objects.create(
            project=platform_assignment.project,
            user=request.user,
            type='rejected',
            description=f"rejected platform {platform_assignment.platform.name}",
            metadata={'platform_id': platform_assignment.platform.id}
        )

        return Response({
            'platform_assignment_id': platform_assignment.id,
            'approval_status': platform_assignment.approval_status,
            'rejected_at': platform_assignment.rejected_at,
            'rejected_by': request.user.id,
            'rejection_reason': platform_assignment.rejection_reason
        })

    def can_submit_platform(self, user, platform_assignment):
        """Check if user can submit platform for approval."""
        if user.is_superuser:
            return True

        # Check if user is assigned to platform
        if platform_assignment.assigned_members.filter(id=user.id).exists():
            return True

        # Check if user has owner/editor role in project
        try:
            member = ProjectMember.objects.get(project=platform_assignment.project, user=user)
            return member.role in ['owner', 'editor']
        except ProjectMember.DoesNotExist:
            return False

    def can_approve_platform(self, user, platform_assignment):
        """Check if user can approve/reject platform."""
        if user.is_superuser:
            return True

        # Check if user is workspace admin
        workspace_role = user.get_workspace_role(platform_assignment.project.workspace_id)
        return workspace_role == 'admin'
