from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db import transaction
from django.core.exceptions import PermissionDenied

from .. import serializers
from .. import models


class DimensionFilter(filters.FilterSet):
    workspace_id = filters.NumberFilter(field_name='workspace__id')

    class Meta:
        model = models.Dimension
        fields = ['id', 'type', 'status', 'workspace_id']


class DimensionViewSet(viewsets.ModelViewSet):
    queryset = models.Dimension.objects.all()  # Default queryset for router
    serializer_class = serializers.DimensionSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionFilter

    def get_queryset(self):
        """Get dimensions filtered by workspace context"""
        # Check if workspace_id is explicitly provided in query params
        workspace_id = self.request.query_params.get('workspace_id')

        if workspace_id:
            # If workspace_id is explicitly provided, filter by it (for both superusers and regular users)
            try:
                workspace_id = int(workspace_id)
                # Validate user has access to this workspace (unless superuser)
                if hasattr(self.request, 'user') and not self.request.user.is_superuser:
                    if not self.request.user.has_workspace_access(workspace_id):
                        # Return empty queryset for unauthorized access
                        return models.Dimension.objects.none()

                # Return queryset filtered by the specified workspace
                return models.Dimension.objects.all_workspaces().filter(workspace_id=workspace_id)

            except (ValueError, TypeError):
                # Invalid workspace_id parameter, return empty queryset
                return models.Dimension.objects.none()

        # Default behavior when no workspace_id is specified
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.Dimension.objects.all_workspaces()

        # For regular users, automatic workspace filtering is applied by managers
        return models.Dimension.objects.all()

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new dimension"""
        workspace_id = getattr(self.request, 'workspace_id', None)

        # Handle workspace context automatically based on user's access
        if not workspace_id:
            # Check if workspace is explicitly specified in the request data
            workspace_data = serializer.validated_data.get('workspace')
            if workspace_data:
                workspace_id = workspace_data.id
                # Verify user has access to this workspace
                if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace_id):
                    raise PermissionDenied(
                        f"Access denied to workspace {workspace_id}")
                # Set the workspace context for this request
                self.request.workspace_id = workspace_id
            else:
                # Try to auto-determine workspace from user's assignments
                user_workspaces = self.request.user.get_accessible_workspaces()

                if self.request.user.is_superuser:
                    raise PermissionDenied(
                        "Superusers must specify 'workspace' in the request data.")
                elif len(user_workspaces) == 1:
                    # User has access to only one workspace - use it automatically
                    workspace_id = user_workspaces[0].id
                    self.request.workspace_id = workspace_id
                elif len(user_workspaces) > 1:
                    raise PermissionDenied(
                        "Multiple workspaces available. Please specify 'workspace' in the request data.")
                else:
                    raise PermissionDenied(
                        "No workspace access available for this user.")

        if not workspace_id:
            raise PermissionDenied("No workspace context available")

        # Validate user has access to this workspace
        if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace_id):
            raise PermissionDenied("Access denied to this workspace")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Workspace is auto-set by WorkspaceMixin.save()
        serializer.save(**kwargs)

    def _create_dimensions_with_dependencies(self, dimensions_data, user):
        """Create dimensions handling parent dependencies within the same batch."""
        results = []
        errors = []
        # name -> dimension instance mapping for batch-created dimensions
        created_dimensions = {}

        # Separate dimensions without dependencies and those with dependencies
        no_deps = [d for d in dimensions_data if '_parent_name' not in d]
        with_deps = [d for d in dimensions_data if '_parent_name' in d]

        # First, create dimensions without dependencies
        for i, dimension_data in enumerate(no_deps):
            try:
                if user.is_authenticated:
                    dimension_data['created_by'] = user

                dimension = models.Dimension.objects.create(**dimension_data)
                created_dimensions[dimension.name] = dimension
                dimension_serializer = self.get_serializer(dimension)
                results.append(dimension_serializer.data)

            except Exception as e:
                errors.append({
                    'index': dimensions_data.index(dimension_data),
                    'dimension_name': dimension_data.get('name', 'Unknown'),
                    'error': str(e)
                })

        # Then create dimensions with dependencies, resolving parent names
        for dimension_data in with_deps:
            try:
                parent_name = dimension_data.pop('_parent_name')

                # Look for parent in created dimensions
                if parent_name in created_dimensions:
                    dimension_data['parent'] = created_dimensions[parent_name]
                else:
                    # This shouldn't happen due to validation, but handle gracefully
                    raise ValueError(
                        f"Parent dimension '{parent_name}' not found in batch")

                if user.is_authenticated:
                    dimension_data['created_by'] = user

                dimension = models.Dimension.objects.create(**dimension_data)
                created_dimensions[dimension.name] = dimension
                dimension_serializer = self.get_serializer(dimension)
                results.append(dimension_serializer.data)

            except Exception as e:
                errors.append({
                    'index': dimensions_data.index(dimension_data),
                    'dimension_name': dimension_data.get('name', 'Unknown'),
                    'error': str(e)
                })

        return results, errors

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple dimensions in a single request."""
        workspace_id = getattr(request, 'workspace_id', None)
        if not workspace_id:
            return Response(
                {'error': 'No workspace context available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user has access to this workspace
        if not request.user.is_superuser and not request.user.has_workspace_access(workspace_id):
            return Response(
                {'error': 'Access denied to this workspace'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = serializers.DimensionBulkCreateSerializer(
            data=request.data)

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    results, errors = self._create_dimensions_with_dependencies(
                        serializer.validated_data['dimensions'],
                        request.user
                    )

                    return Response({
                        'success_count': len(results),
                        'error_count': len(errors),
                        'results': results,
                        'errors': errors
                    })

            except Exception as e:
                return Response(
                    {'error': f'Bulk creation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DimensionValueFilter(filters.FilterSet):
    dimension = filters.NumberFilter(method='filter_dimension_id')
    workspace_id = filters.NumberFilter(field_name='workspace__id')

    class Meta:
        model = models.DimensionValue
        fields = ['dimension', 'workspace_id']

    def filter_dimension_id(self, queryset, name, value):
        return queryset.filter(dimension__id=value)


class DimensionValueViewSet(viewsets.ModelViewSet):
    queryset = models.DimensionValue.objects.all()  # Default queryset for router
    serializer_class = serializers.DimensionValueSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionValueFilter

    def get_queryset(self):
        """Get dimension values filtered by workspace context"""
        # Check if workspace_id is explicitly provided in query params
        workspace_id = self.request.query_params.get('workspace_id')

        if workspace_id:
            # If workspace_id is explicitly provided, filter by it (for both superusers and regular users)
            try:
                workspace_id = int(workspace_id)
                # Validate user has access to this workspace (unless superuser)
                if hasattr(self.request, 'user') and not self.request.user.is_superuser:
                    if not self.request.user.has_workspace_access(workspace_id):
                        # Return empty queryset for unauthorized access
                        return models.DimensionValue.objects.none()

                # Return queryset filtered by the specified workspace
                return models.DimensionValue.objects.all_workspaces().filter(workspace_id=workspace_id)

            except (ValueError, TypeError):
                # Invalid workspace_id parameter, return empty queryset
                return models.DimensionValue.objects.none()

        # Default behavior when no workspace_id is specified
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.DimensionValue.objects.all_workspaces()

        # For regular users, automatic workspace filtering is applied by managers
        return models.DimensionValue.objects.all()

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new dimension value"""
        workspace_id = getattr(self.request, 'workspace_id', None)

        # Handle workspace context automatically based on user's access
        if not workspace_id:
            # Check if workspace is explicitly specified in the request data
            workspace_data = serializer.validated_data.get('workspace')
            if workspace_data:
                workspace_id = workspace_data.id
                # Verify user has access to this workspace
                if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace_id):
                    raise PermissionDenied(
                        f"Access denied to workspace {workspace_id}")
                # Set the workspace context for this request
                self.request.workspace_id = workspace_id
            else:
                # Try to auto-determine workspace from user's assignments
                user_workspaces = self.request.user.get_accessible_workspaces()

                if self.request.user.is_superuser:
                    raise PermissionDenied(
                        "Superusers must specify 'workspace' in the request data.")
                elif len(user_workspaces) == 1:
                    # User has access to only one workspace - use it automatically
                    workspace_id = user_workspaces[0].id
                    self.request.workspace_id = workspace_id
                elif len(user_workspaces) > 1:
                    raise PermissionDenied(
                        "Multiple workspaces available. Please specify 'workspace' in the request data.")
                else:
                    raise PermissionDenied(
                        "No workspace access available for this user.")

        if not workspace_id:
            raise PermissionDenied("No workspace context available")

        # Validate user has access to this workspace
        if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace_id):
            raise PermissionDenied("Access denied to this workspace")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Workspace is auto-set by WorkspaceMixin.save()
        serializer.save(**kwargs)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple dimension values in a single request."""
        workspace_id = getattr(request, 'workspace_id', None)
        if not workspace_id:
            return Response(
                {'error': 'No workspace context available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user has access to this workspace
        if not request.user.is_superuser and not request.user.has_workspace_access(workspace_id):
            return Response(
                {'error': 'Access denied to this workspace'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = serializers.DimensionValueBulkCreateSerializer(
            data=request.data)

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    results = []
                    errors = []

                    for i, value_data in enumerate(serializer.validated_data['dimension_values']):
                        try:
                            # Set created_by if user is authenticated
                            if request.user.is_authenticated:
                                value_data['created_by'] = request.user

                            dimension_value = models.DimensionValue.objects.create(
                                **value_data)
                            value_serializer = self.get_serializer(
                                dimension_value)
                            results.append(value_serializer.data)

                        except Exception as e:
                            errors.append({
                                'index': i,
                                'dimension_value': value_data.get('value', 'Unknown'),
                                'dimension_id': value_data.get('dimension', 'Unknown'),
                                'error': str(e)
                            })

                    return Response({
                        'success_count': len(results),
                        'error_count': len(errors),
                        'results': results,
                        'errors': errors
                    })

            except Exception as e:
                return Response(
                    {'error': f'Bulk creation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
