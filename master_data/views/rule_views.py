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
from ..services import NamingPatternValidator


class RuleFilter(filters.FilterSet):
    platform = filters.NumberFilter(method='filter_platform_id')
    field = filters.NumberFilter(method='filter_field_id')
    status = filters.CharFilter()
    is_default = filters.BooleanFilter()
    workspace = filters.NumberFilter(field_name='workspace__id')

    class Meta:
        model = models.Rule
        fields = [
            'id',
            'field',
            'platform',
            'status',
            'is_default',
            'workspace'
        ]

    def filter_platform_id(self, queryset, name, value):
        return queryset.filter(platform__id=value)

    def filter_field_id(self, queryset, name, value):
        return queryset.filter(rule_details__field__id=value).distinct()


class RuleViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RuleSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleFilter

    def get_queryset(self):
        """Get rules filtered by workspace context"""
        # Check if workspace_id is explicitly provided in query params
        workspace = self.request.query_params.get('workspace')

        if workspace:
            # If workspace_id is explicitly provided, filter by it (for both superusers and regular users)
            try:
                workspace = int(workspace)
                # Validate user has access to this workspace (unless superuser)
                if hasattr(self.request, 'user') and not self.request.user.is_superuser:
                    if not self.request.user.has_workspace_access(workspace):
                        # Return empty queryset for unauthorized access
                        return models.Rule.objects.none()

                # Return queryset filtered by the specified workspace
                return models.Rule.objects.all_workspaces().filter(
                    workspace_id=workspace
                ).select_related('platform').prefetch_related('rule_details')

            except (ValueError, TypeError):
                # Invalid workspace parameter, return empty queryset
                return models.Rule.objects.none()

        # Default behavior when no workspace is specified
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.Rule.objects.all_workspaces().select_related(
                'platform').prefetch_related('rule_details')

        # For regular users, automatic workspace filtering is applied by managers
        return models.Rule.objects.all().select_related(
            'platform').prefetch_related('rule_details')

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new rule"""
        workspace = getattr(self.request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        # Validate user has access to this workspace
        if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace):
            raise PermissionDenied("Access denied to this workspace")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Workspace is auto-set by WorkspaceMixin.save()
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Generate a preview of string generation for this rule."""
        rule = self.get_object()
        serializer = serializers.RulePreviewRequestSerializer(
            data=request.data)

        if serializer.is_valid():
            try:
                field = models.Field.objects.get(
                    id=serializer.validated_data['field_id'])
                sample_values = serializer.validated_data['sample_values']

                preview = rule.get_preview(field, sample_values)

                return Response({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'field_id': field.id,
                    'field_name': field.name,
                    'sample_values': sample_values,
                    'preview': preview,
                    'success': 'Preview failed' not in preview
                })

            except models.Field.DoesNotExist:
                return Response(
                    {'error': 'Field not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': f'Preview generation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def validate_configuration(self, request, pk=None):
        """Validate the rule configuration."""
        rule = self.get_object()
        serializer = serializers.RuleValidationSerializer(rule)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set this rule as the default for its platform within the workspace."""
        rule = self.get_object()

        try:
            with transaction.atomic():
                # Unset any existing default for this platform in the workspace
                models.Rule.objects.filter(
                    workspace=rule.workspace,
                    platform=rule.platform,
                    is_default=True
                ).update(is_default=False)

                # Set this rule as default
                rule.is_default = True
                rule.save()

                return Response({
                    'message': f'Rule "{rule.name}" is now the default for platform "{rule.platform.name}" in workspace "{rule.workspace.name}"',
                    'rule_id': rule.id,
                    'platform_id': rule.platform.id,
                    'workspace_id': rule.workspace.id
                })

        except Exception as e:
            return Response(
                {'error': f'Failed to set default rule: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def defaults(self, request):
        """Get all default rules by platform in current workspace."""
        default_rules = models.Rule.objects.filter(
            is_default=True).select_related('platform', 'workspace')
        serializer = self.get_serializer(default_rules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def required_dimensions(self, request, pk=None):
        """Get required dimensions for all fields in this rule."""
        rule = self.get_object()

        result = {}
        fields = models.Field.objects.filter(
            workspace=rule.workspace,
            platform=rule.platform
        )

        for field in fields:
            if rule.can_generate_for_field(field):
                result[field.name] = {
                    'field_id': field.id,
                    'field_level': field.field_level,
                    'required_dimensions': list(rule.get_required_dimensions(field)),
                    'generation_order': rule.get_generation_order(field)
                }

        return Response({
            'rule_id': rule.id,
            'rule_name': rule.name,
            'platform': rule.platform.name,
            'workspace': rule.workspace.name,
            'fields': result
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active rules in current workspace."""
        active_rules = models.Rule.objects.active()

        # Filter by platform if provided
        platform_id = request.query_params.get('platform_id')
        if platform_id:
            active_rules = active_rules.filter(platform_id=platform_id)

        serializer = self.get_serializer(active_rules, many=True)
        return Response(serializer.data)


class RuleDetailFilter(filters.FilterSet):
    field = filters.NumberFilter(field_name='field__id')
    platform = filters.NumberFilter(field_name='rule__platform__id')
    rule = filters.NumberFilter()
    dimension_order = filters.NumberFilter()
    is_required = filters.BooleanFilter()
    workspace = filters.NumberFilter(field_name='workspace__id')

    class Meta:
        model = models.RuleDetail
        fields = ['id', 'rule', 'dimension_order', 'field',
                  'platform', 'is_required', 'workspace']


class RuleDetailViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleDetailFilter

    def get_queryset(self):
        """Get rule details filtered by workspace context"""
        # Check if workspace_id is explicitly provided in query params
        workspace = self.request.query_params.get('workspace')

        if workspace:
            # If workspace_id is explicitly provided, filter by it (for both superusers and regular users)
            try:
                workspace = int(workspace)
                # Validate user has access to this workspace (unless superuser)
                if hasattr(self.request, 'user') and not self.request.user.is_superuser:
                    if not self.request.user.has_workspace_access(workspace):
                        # Return empty queryset for unauthorized access
                        return models.RuleDetail.objects.none()

                # Return queryset filtered by the specified workspace
                return models.RuleDetail.objects.all_workspaces().filter(
                    workspace_id=workspace
                ).select_related('rule', 'field', 'dimension', 'rule__platform')

            except (ValueError, TypeError):
                # Invalid workspace parameter, return empty queryset
                return models.RuleDetail.objects.none()

        # Default behavior when no workspace is specified
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.RuleDetail.objects.all_workspaces().select_related(
                'rule', 'field', 'dimension', 'rule__platform'
            )

        # For regular users, automatic workspace filtering is applied by managers
        return models.RuleDetail.objects.all().select_related(
            'rule', 'field', 'dimension', 'rule__platform'
        )

    def get_serializer_class(self):
        """Use different serializers for create vs read operations."""
        if self.action == 'create':
            return serializers.RuleDetailCreateSerializer
        return serializers.RuleDetailSerializer

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new rule detail"""
        workspace = getattr(self.request, 'workspace', None)
        if not workspace:
            raise PermissionDenied("No workspace context available")

        # Validate user has access to this workspace
        if not self.request.user.is_superuser and not self.request.user.has_workspace_access(workspace):
            raise PermissionDenied("Access denied to this workspace")

        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Workspace is auto-set by WorkspaceMixin.save()
        serializer.save(**kwargs)

    @action(detail=False, methods=['post'])
    def validate_order(self, request):
        """Validate dimension order for a rule and field."""
        serializer = serializers.RuleDetailCreateSerializer(data=request.data)

        if serializer.is_valid():
            rule_id = serializer.validated_data['rule'].id
            field_id = serializer.validated_data['field'].id
            dimension_order = serializer.validated_data['dimension_order']

            # Check for existing orders
            existing_orders = models.RuleDetail.objects.filter(
                rule_id=rule_id,
                field_id=field_id
            ).values_list('dimension_order', flat=True)

            existing_orders_list = list(existing_orders)

            return Response({
                'rule_id': rule_id,
                'field_id': field_id,
                'requested_order': dimension_order,
                'existing_orders': existing_orders_list,
                'is_valid': dimension_order not in existing_orders_list,
                'next_available_order': max(existing_orders_list, default=0) + 1 if existing_orders_list else 1
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RuleNestedViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RuleNestedLegacySerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleFilter

    def get_queryset(self):
        """Get rules with nested details filtered by workspace context"""
        # Check if workspace_id is explicitly provided in query params
        workspace = self.request.query_params.get('workspace')

        if workspace:
            # If workspace_id is explicitly provided, filter by it (for both superusers and regular users)
            try:
                workspace = int(workspace)
                # Validate user has access to this workspace (unless superuser)
                if hasattr(self.request, 'user') and not self.request.user.is_superuser:
                    if not self.request.user.has_workspace_access(workspace):
                        # Return empty queryset for unauthorized access
                        return models.Rule.objects.none()

                # Return queryset filtered by the specified workspace
                return models.Rule.objects.all_workspaces().filter(
                    workspace=workspace
                ).prefetch_related('rule_details__field', 'rule_details__dimension')

            except (ValueError, TypeError):
                # Invalid workspace parameter, return empty queryset
                return models.Rule.objects.none()

        # Default behavior when no workspace is specified
        # If user is superuser, they can see all workspaces
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.Rule.objects.all_workspaces().prefetch_related(
                'rule_details__field', 'rule_details__dimension')

        # For regular users, automatic workspace filtering is applied by managers
        return models.Rule.objects.all().prefetch_related(
            'rule_details__field', 'rule_details__dimension')

    def perform_create(self, serializer):
        """Set created_by when creating a new rule"""
        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        # Let the serializer handle workspace validation and creation
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone a rule with all its details within the same workspace."""
        original_rule = self.get_object()

        data = request.data
        new_name = data.get('name', f"{original_rule.name} (Copy)")

        try:
            with transaction.atomic():
                # Create new rule
                new_rule = models.Rule.objects.create(
                    workspace=original_rule.workspace,
                    platform=original_rule.platform,
                    name=new_name,
                    description=data.get(
                        'description', original_rule.description),
                    status=original_rule.status,
                    is_default=False,  # Cloned rules are never default
                    created_by=self.request.user if self.request.user.is_authenticated else None
                )

                # Clone all rule details
                for detail in original_rule.rule_details.all():
                    models.RuleDetail.objects.create(
                        workspace=original_rule.workspace,
                        rule=new_rule,
                        field=detail.field,
                        dimension=detail.dimension,
                        prefix=detail.prefix,
                        suffix=detail.suffix,
                        delimiter=detail.delimiter,
                        dimension_order=detail.dimension_order,
                        is_required=detail.is_required,
                        created_by=self.request.user if self.request.user.is_authenticated else None
                    )

                serializer = self.get_serializer(new_rule)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Failed to clone rule: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
