# myapp/api/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.conf import settings
from django.db import transaction
from django.core.exceptions import PermissionDenied

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .. import serializers
from .. import models
from ..permissions import IsAuthenticatedOrDebugReadOnly


class WorkspaceMixin:
    """
    Mixin to parse `?workspace=` from the querystring (or request attribute)
    and to check access in one place.
    """

    def get_workspace_param(self, param_name='workspace'):
        """
        Get a parameter from request, handling both DRF and Django requests.
        This is a defensive method to handle production issues where DRF request
        wrapper might not be applied properly.
        """
        # Handle both DRF Request (has query_params) and Django WSGIRequest (has GET)
        if hasattr(self.request, 'query_params'):
            return self.request.query_params.get(param_name)
        else:
            return self.request.GET.get(param_name)

    def get_workspace_id(self):
        raw = getattr(self.request, 'workspace', None)
        if not raw:
            raw = self.get_workspace_param('workspace')
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def check_workspace_access(self, workspace_id):
        # Handle both DRF Request and Django WSGIRequest
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        # Check workspace access for non-superusers
        if not user.is_superuser:
            # Some user models might not have has_workspace_access method
            if hasattr(user, 'has_workspace_access'):
                if not user.has_workspace_access(workspace_id):
                    raise PermissionDenied(
                        f"Access denied to workspace {workspace_id}")
            else:
                # Fallback: if method doesn't exist, only allow superusers
                raise PermissionDenied("Workspace access method not available")


#
# ─── DIMENSIONS ─────────────────────────────────────────────────────────────────
#

class DimensionFilter(filters.FilterSet):
    dimension = filters.NumberFilter(field_name='dimension__id')
    workspace = filters.NumberFilter(field_name='workspace__id')

    class Meta:
        model = models.Dimension
        fields = ['id', 'type', 'status', 'workspace', 'dimension']


class DimensionViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """
    CRUD + bulk_create for Dimension, scoped per-workspace.
    """
    queryset = models.Dimension.objects.all()
    serializer_class = serializers.DimensionSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionFilter
    # filterset_fields = ['id', 'type', 'status', 'workspace__id']

    def get_queryset(self):
        wid = self.get_workspace_id()
        if wid:
            # list/retrieve only dims in that workspace
            self.check_workspace_access(wid)
            return models.Dimension.objects.all_workspaces().filter(workspace_id=wid)

        # no `?workspace=`: superusers see all, regular users auto-filter via manager
        user = getattr(self.request, 'user', None)
        if user and user.is_superuser:
            return models.Dimension.objects.all_workspaces()
        return models.Dimension.objects.all()

    def get_object(self):
        # enforce workspace scoping on retrieve()
        obj = super().get_object()
        wid = self.get_workspace_id()
        if wid is not None and obj.workspace_id != wid:
            self.check_workspace_access(wid)
        return obj

    def perform_create(self, serializer):
        # require payload to include { "workspace": <id> } via a write-only field
        workspace_obj = serializer.validated_data.get('workspace')
        if not workspace_obj:
            raise PermissionDenied("No workspace context available")
        wid = workspace_obj.id
        self.check_workspace_access(wid)

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request, version=None):
        """
        POST /api/dimensions/bulk_create/?workspace=<id>
        with body { "dimensions": [ {name, type, …}, … ] }

        Workspace can be provided either as a query parameter (?workspace=<id>) 
        or in the request body ("workspace": <id>).
        """
        wid = self.get_workspace_id()

        # If workspace not found in query params, check request body
        if not wid and hasattr(request, 'data') and 'workspace' in request.data:
            try:
                wid = int(request.data['workspace'])
            except (ValueError, TypeError):
                return Response({'error': 'Invalid workspace ID in request body'},
                                status=status.HTTP_400_BAD_REQUEST)

        if not wid:
            return Response({'error': 'No workspace context available. Provide workspace as query parameter (?workspace=<id>) or in request body ("workspace": <id>)'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            self.check_workspace_access(wid)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

        # fetch the Workspace instance once
        workspace_obj = models.Workspace.objects.get(pk=wid)

        serializer = serializers.DimensionBulkCreateSerializer(
            data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        dimensions_data = serializer.validated_data['dimensions']
        # inject workspace into each item
        for d in dimensions_data:
            d['workspace'] = workspace_obj

        try:
            with transaction.atomic():
                results, errors = self._create_dimensions_with_dependencies(
                    dimensions_data,
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

    def _create_dimensions_with_dependencies(self, dimensions_data, user):
        """
        (unchanged) two-pass create for handling parent → child in the same batch.
        """
        results = []
        errors = []
        created = {}

        no_parents = [d for d in dimensions_data if '_parent_name' not in d]
        with_parents = [d for d in dimensions_data if '_parent_name' in d]

        # 1) create root dims
        for dim in no_parents:
            try:
                if user.is_authenticated:
                    dim['created_by'] = user
                obj = models.Dimension.objects.create(**dim)
                created[obj.name] = obj
                results.append(self.get_serializer(obj).data)
            except Exception as e:
                errors.append({
                    'dimension_name': dim.get('name', 'Unknown'),
                    'error': str(e)
                })

        # 2) create children
        for dim in with_parents:
            try:
                parent_name = dim.pop('_parent_name')
                if parent_name not in created:
                    raise ValueError(f"Parent '{parent_name}' not in batch")
                dim['parent'] = created[parent_name]

                if user.is_authenticated:
                    dim['created_by'] = user
                obj = models.Dimension.objects.create(**dim)
                created[obj.name] = obj
                results.append(self.get_serializer(obj).data)
            except Exception as e:
                errors.append({
                    'dimension_name': dim.get('name', 'Unknown'),
                    'error': str(e)
                })

        return results, errors


#
# ─── DIMENSION VALUES ────────────────────────────────────────────────────────────
#

class DimensionValueFilter(filters.FilterSet):
    dimension = filters.NumberFilter(field_name='dimension__id')
    workspace = filters.NumberFilter(field_name='workspace__id')

    class Meta:
        model = models.DimensionValue
        fields = ['id', 'dimension', 'workspace', 'value']


class DimensionValueViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """
    CRUD + bulk_create for DimensionValue, scoped per-workspace.
    """
    queryset = models.DimensionValue.objects.all()
    serializer_class = serializers.DimensionValueSerializer
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionValueFilter
    # filterset_fields = ['id', 'dimension__id', 'workspace__id']

    def get_queryset(self):
        wid = self.get_workspace_id()
        if wid:
            self.check_workspace_access(wid)
            return models.DimensionValue.objects.all_workspaces().filter(workspace_id=wid)
        user = getattr(self.request, 'user', None)
        if user and user.is_superuser:
            return models.DimensionValue.objects.all_workspaces()
        return models.DimensionValue.objects.all()

    def get_object(self):
        obj = super().get_object()
        wid = self.get_workspace_id()
        if wid is not None and obj.workspace_id != wid:
            self.check_workspace_access(wid)
        return obj

    def perform_create(self, serializer):
        # require a write-only `workspace` field in the serializer
        workspace_obj = serializer.validated_data.get('workspace')
        if not workspace_obj:
            raise PermissionDenied("No workspace context available")
        wid = workspace_obj.id
        self.check_workspace_access(wid)

        kwargs = {}
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            kwargs['created_by'] = user
        serializer.save(**kwargs)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request, version=None):
        """
        POST /api/dimension-values/bulk_create/?workspace=<id>
        with body { "dimension_values": [ {...}, ... ] }

        Workspace can be provided either as a query parameter (?workspace=<id>) 
        or in the request body ("workspace": <id>).
        """
        wid = self.get_workspace_id()

        # If workspace not found in query params, check request body
        if not wid and hasattr(request, 'data') and 'workspace' in request.data:
            try:
                wid = int(request.data['workspace'])
            except (ValueError, TypeError):
                return Response({'error': 'Invalid workspace ID in request body'},
                                status=status.HTTP_400_BAD_REQUEST)

        if not wid:
            return Response({'error': 'No workspace context available. Provide workspace as query parameter (?workspace=<id>) or in request body ("workspace": <id>)'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            self.check_workspace_access(wid)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

        workspace_obj = models.Workspace.objects.get(pk=wid)

        serializer = serializers.DimensionValueBulkCreateSerializer(
            data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        values_data = serializer.validated_data['dimension_values']
        for v in values_data:
            v['workspace'] = workspace_obj

        try:
            with transaction.atomic():
                results, errors = [], []
                for i, data in enumerate(values_data):
                    try:
                        user = getattr(request, 'user', None)
                        if user and user.is_authenticated:
                            data['created_by'] = user
                        dv = models.DimensionValue.objects.create(**data)
                        results.append(self.get_serializer(dv).data)
                    except Exception as e:
                        errors.append({
                            'index': i,
                            'value': data.get('value', 'Unknown'),
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
