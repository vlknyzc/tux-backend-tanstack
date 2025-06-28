from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Prefetch

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import WorkspaceUser
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer,
    WorkspaceUserSerializer, WorkspaceUserCreateSerializer, UserAuthorizationSummarySerializer
)

User = get_user_model()


class WorkspaceUserFilter(FilterSet):
    class Meta:
        model = WorkspaceUser
        fields = {
            'workspace': ['exact'],
            'user': ['exact'],
            'role': ['exact'],
            'is_active': ['exact']
        }


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users and their basic information.
    Provides CRUD operations for user accounts.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'is_staff', 'is_superuser']

    def get_permissions(self):
        """
        Different permissions for different actions
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only superusers and workspace admins can modify users
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Get users based on user permissions"""
        user = self.request.user

        if user.is_superuser:
            # Superusers see all users
            return User.objects.all().prefetch_related(
                Prefetch('workspaceuser_set',
                         queryset=WorkspaceUser.objects.select_related('workspace'))
            ).annotate(
                workspace_count=Count('workspaces', filter=Q(
                    workspaceuser__is_active=True))
            )
        else:
            # Regular users see only users in their workspaces
            user_workspaces = user.get_accessible_workspaces()
            return User.objects.filter(
                Q(workspaces__in=user_workspaces) | Q(id=user.id)
            ).distinct().prefetch_related(
                Prefetch('workspaceuser_set',
                         queryset=WorkspaceUser.objects.select_related('workspace'))
            ).annotate(
                workspace_count=Count('workspaces', filter=Q(
                    workspaceuser__is_active=True))
            )

    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        else:
            return UserDetailSerializer

    def perform_create(self, serializer):
        """Create user - only superusers can do this"""
        if not self.request.user.is_superuser:
            raise PermissionDenied("Only superusers can create users")
        serializer.save()

    def perform_update(self, serializer):
        """Update user - check permissions"""
        user = self.request.user
        target_user = self.get_object()

        # Superusers can update anyone
        if user.is_superuser:
            serializer.save()
            return

        # Users can only update themselves (limited fields)
        if user == target_user:
            # Only allow updating name fields for self
            allowed_fields = ['first_name', 'last_name']
            data = {k: v for k, v in serializer.validated_data.items()
                    if k in allowed_fields}
            serializer.save(**data)
            return

        raise PermissionDenied("You can only update your own profile")

    def perform_destroy(self, instance):
        """Delete user - only superusers can do this"""
        if not self.request.user.is_superuser:
            raise PermissionDenied("Only superusers can delete users")

        if instance == self.request.user:
            raise PermissionDenied("You cannot delete your own account")

        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['get'])
    def authorizations(self, request, pk=None):
        """Get detailed authorization information for a user"""
        user = self.get_object()

        # Build authorization summary
        authorizations = []
        if user.is_superuser:
            from master_data.models import Workspace
            workspaces = Workspace.objects.all()
            for workspace in workspaces:
                authorizations.append({
                    'workspace': workspace.id,
                    'workspace_name': workspace.name,
                    'role': 'superuser',
                    'is_active': True,
                    'assigned_date': None,
                    'permissions': ['all']
                })
        else:
            workspace_users = user.workspaceuser_set.select_related(
                'workspace').all()
            for wu in workspace_users:
                permissions_list = []
                if wu.role == 'admin':
                    permissions_list = [
                        'read', 'write', 'delete', 'manage_users']
                elif wu.role == 'user':
                    permissions_list = ['read', 'write']
                elif wu.role == 'viewer':
                    permissions_list = ['read']

                authorizations.append({
                    'workspace': wu.workspace.id,
                    'workspace_name': wu.workspace.name,
                    'role': wu.role,
                    'is_active': wu.is_active,
                    'assigned_date': wu.created,
                    'permissions': permissions_list
                })

        summary_data = {
            'user': user.id,
            'email': user.email,
            'full_name': user.get_full_name(),
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'workspace_authorizations': authorizations,
            'total_workspaces': len(authorizations),
            'active_assignments': len([a for a in authorizations if a['is_active']])
        }

        serializer = UserAuthorizationSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class WorkspaceUserManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workspace-user relationships.
    Allows assigning/removing users from workspaces and managing roles.

    list:
        Return a list of workspace-user relationships.

    create:
        Create a new workspace-user relationship.

    retrieve:
        Return the given workspace-user relationship.

    update:
        Update the given workspace-user relationship.

    partial_update:
        Update part of the given workspace-user relationship.

    destroy:
        Delete the given workspace-user relationship.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workspace', 'user', 'role', 'is_active']
    schema = AutoSchema()

    def get_schema_fields(self, view):
        """
        Add custom schema fields for filtering and actions.
        """
        fields = super().get_schema_fields(view)
        fields.append(coreapi.Field(
            name='workspace',
            location='query',
            required=False,
            type='integer',
            description='Filter by workspace ID'
        ))
        fields.append(coreapi.Field(
            name='user',
            location='query',
            required=False,
            type='integer',
            description='Filter by user ID'
        ))
        fields.append(coreapi.Field(
            name='role',
            location='query',
            required=False,
            type='string',
            description='Filter by role (admin, user, viewer)'
        ))
        fields.append(coreapi.Field(
            name='is_active',
            location='query',
            required=False,
            type='boolean',
            description='Filter by active status'
        ))
        return fields

    def get_queryset(self):
        """Get workspace-user relationships based on permissions"""
        user = self.request.user

        if user.is_superuser:
            # Superusers see all relationships
            return WorkspaceUser.objects.all().select_related('user', 'workspace')
        else:
            # Regular users see only relationships in their workspaces
            user_workspaces = user.get_accessible_workspaces()
            return WorkspaceUser.objects.filter(
                workspace__in=user_workspaces
            ).select_related('user', 'workspace')

    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == 'create':
            return WorkspaceUserCreateSerializer
        else:
            return WorkspaceUserSerializer

    def perform_create(self, serializer):
        """Create workspace-user relationship"""
        user = self.request.user
        workspace = serializer.validated_data['workspace']

        # Check if user can manage this workspace
        if not user.is_superuser:
            if not user.has_workspace_access(workspace.id):
                raise PermissionDenied(
                    "You don't have access to this workspace")

            # Only workspace admins can assign users
            user_role = user.get_workspace_role(workspace.id)
            if user_role != 'admin':
                raise PermissionDenied(
                    "Only workspace admins can assign users")

        serializer.save()

    def perform_update(self, serializer):
        """Update workspace-user relationship"""
        user = self.request.user
        workspace_user = self.get_object()
        workspace = workspace_user.workspace

        # Check if user can manage this workspace
        if not user.is_superuser:
            if not user.has_workspace_access(workspace.id):
                raise PermissionDenied(
                    "You don't have access to this workspace")

            # Only workspace admins can modify assignments
            user_role = user.get_workspace_role(workspace.id)
            if user_role != 'admin':
                raise PermissionDenied(
                    "Only workspace admins can modify user assignments")

        serializer.save()

    def perform_destroy(self, instance):
        """Remove workspace-user relationship"""
        user = self.request.user
        workspace = instance.workspace

        # Check if user can manage this workspace
        if not user.is_superuser:
            if not user.has_workspace_access(workspace.id):
                raise PermissionDenied(
                    "You don't have access to this workspace")

            # Only workspace admins can remove assignments
            user_role = user.get_workspace_role(workspace.id)
            if user_role != 'admin':
                raise PermissionDenied(
                    "Only workspace admins can remove user assignments")

        # Don't allow removing the last admin
        if instance.role == 'admin':
            admin_count = WorkspaceUser.objects.filter(
                workspace=workspace, role='admin', is_active=True
            ).count()
            if admin_count <= 1:
                raise PermissionDenied(
                    "Cannot remove the last admin from a workspace")

        instance.delete()

    @action(detail=False, methods=['post'])
    def bulk_assign(self, request):
        """
        Bulk assign users to workspaces.
        Only available to superusers.
        """
        if not request.user.is_superuser:
            raise PermissionDenied(
                "Only superusers can perform bulk assignments")

        user_ids = request.data.get('user_ids', [])
        workspace_ids = request.data.get('workspace_ids', [])
        role = request.data.get('role', 'user')

        if not user_ids or not workspace_ids:
            return Response(
                {'error': 'user_ids and workspace_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_assignments = []
        errors = []

        for user_id in user_ids:
            for workspace_id in workspace_ids:
                try:
                    workspace_user, created = WorkspaceUser.objects.get_or_create(
                        user=user_id,
                        workspace=workspace_id,
                        defaults={'role': role, 'is_active': True}
                    )
                    if created:
                        created_assignments.append({
                            'user': user_id,
                            'workspace': workspace_id,
                            'role': role
                        })
                    else:
                        # Update existing assignment
                        workspace_user.role = role
                        workspace_user.is_active = True
                        workspace_user.save()
                        created_assignments.append({
                            'user': user_id,
                            'workspace': workspace_id,
                            'role': role,
                            'updated': True
                        })
                except Exception as e:
                    errors.append({
                        'user': user_id,
                        'workspace': workspace_id,
                        'error': str(e)
                    })

        return Response({
            'success_count': len(created_assignments),
            'error_count': len(errors),
            'assignments': created_assignments,
            'errors': errors
        })

    def get_schema_operation_parameters(self, action):
        """
        Add custom schema parameters for actions.
        """
        parameters = super().get_schema_operation_parameters(action)

        if action == 'bulk_assign':
            parameters.extend([
                coreapi.Field(
                    name='user_ids',
                    location='form',
                    required=True,
                    type='array',
                    description='List of user IDs to assign'
                ),
                coreapi.Field(
                    name='workspace_ids',
                    location='form',
                    required=True,
                    type='array',
                    description='List of workspace IDs to assign users to'
                ),
                coreapi.Field(
                    name='role',
                    location='form',
                    required=False,
                    type='string',
                    description='Role to assign (admin, user, viewer). Defaults to user.'
                )
            ])

        return parameters

    @action(detail=False, methods=['get'])
    def workspace_summary(self, request):
        """
        Get summary of all workspace assignments.

        get:
            Returns a summary of user assignments grouped by workspace,
            including counts of total users, active users, and users by role.

        responses:
            200:
                description: Successfully retrieved workspace summary
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                workspace_summaries:
                                    type: array
                                    items:
                                        type: object
                                        properties:
                                            workspace__id:
                                                type: integer
                                            workspace__name:
                                                type: string
                                            total_users:
                                                type: integer
                                            active_users:
                                                type: integer
                                            admin_count:
                                                type: integer
                                            user_count:
                                                type: integer
                                            viewer_count:
                                                type: integer
                                total_workspaces:
                                    type: integer
        """
        user = request.user

        if user.is_superuser:
            workspace_users = WorkspaceUser.objects.all()
        else:
            user_workspaces = user.get_accessible_workspaces()
            workspace_users = WorkspaceUser.objects.filter(
                workspace__in=user_workspaces)

        # Group by workspace
        from django.db.models import Count
        summary = workspace_users.select_related('workspace').values(
            'workspace', 'workspace__name'
        ).annotate(
            total_users=Count('user', distinct=True),
            active_users=Count('user', filter=Q(
                is_active=True), distinct=True),
            admin_count=Count('user', filter=Q(
                role='admin', is_active=True), distinct=True),
            user_count=Count('user', filter=Q(
                role='user', is_active=True), distinct=True),
            viewer_count=Count('user', filter=Q(
                role='viewer', is_active=True), distinct=True)
        )

        return Response({
            'workspace_summaries': list(summary),
            'total_workspaces': summary.count()
        })
