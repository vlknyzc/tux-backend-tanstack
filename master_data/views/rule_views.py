from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.conf import settings
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef, F

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .. import serializers
from .. import models
from ..services import NamingPatternValidator
from ..permissions import IsAuthenticatedOrDebugReadOnly
from .mixins import WorkspaceValidationMixin


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


class RuleViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing rules, scoped per-workspace.
    
    URL: /api/v1/workspaces/{workspace_id}/rules/
    """
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleFilter

    @extend_schema(tags=["Rules"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.action in ['create', 'update', 'partial_update']:
            return serializers.RuleCreateUpdateSerializer
        elif self.action == 'retrieve':
            return serializers.RuleNestedReadSerializer
        else:
            return serializers.RuleReadSerializer

    def get_queryset(self):
        """Get rules filtered by workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        # WorkspaceValidationMixin already validated access in dispatch()

        if workspace_id:
            return models.Rule.objects.filter(
                workspace_id=workspace_id
            ).select_related(
                'platform',
                'workspace',
                'created_by'
            ).prefetch_related(
                'rule_details',
                'rule_details__dimension',
                'rule_details__dimension__parent',
                'rule_details__dimension__dimension_values',
                'rule_details__field',
                'rule_details__field__next_field',
                'rule_details__created_by'
            )

        return models.Rule.objects.none()

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new rule."""
        workspace_id = self.kwargs.get('workspace_id')
        if not workspace_id:
            raise PermissionDenied("No workspace context available")
        
        workspace = models.Workspace.objects.get(id=workspace_id)
        # WorkspaceValidationMixin already validated access in dispatch()
        
        kwargs = {'workspace': workspace}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)

    @extend_schema(tags=["Rules"])
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

    @extend_schema(tags=["Rules"])
    @action(detail=True, methods=['get'])
    def validate_configuration(self, request, pk=None):
        """Validate the rule configuration."""
        rule = self.get_object()
        serializer = serializers.RuleValidationSerializer(rule)
        return Response(serializer.data)

    @extend_schema(tags=["Rules"])
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

    @extend_schema(tags=["Rules"])
    @action(detail=False, methods=['get'])
    def defaults(self, request):
        """Get all default rules by platform in current workspace."""
        default_rules = models.Rule.objects.filter(
            is_default=True).select_related('platform', 'workspace')
        serializer = self.get_serializer(default_rules, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["Rules"])
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

    @extend_schema(tags=["Rules"])
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active rules in current workspace."""
        active_rules = models.Rule.objects.active()

        # Filter by platform if provided
        # Handle both DRF Request (has query_params) and Django WSGIRequest (has GET)
        if hasattr(request, 'query_params'):
            platform_id = request.query_params.get('platform_id')
        else:
            platform_id = request.GET.get('platform_id')
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


class RuleDetailViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing rule details, scoped per-workspace.
    
    URL: /api/v1/workspaces/{workspace_id}/rule-details/
    """
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleDetailFilter

    @extend_schema(tags=["Rules"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Get rule details filtered by workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        # WorkspaceValidationMixin already validated access in dispatch()

        if workspace_id:
            # Subquery to check if dimension exists in parent field
            parent_field_subquery = models.RuleDetail.objects.filter(
                rule=OuterRef('rule'),
                field__platform=OuterRef('field__platform'),
                dimension=OuterRef('dimension'),
                field__field_level=OuterRef('field__field_level') - 1
            )

            return models.RuleDetail.objects.filter(
                workspace_id=workspace_id
            ).select_related(
                'rule',
                'field',
                'field__next_field',
                'dimension',
                'dimension__parent',
                'rule__platform',
                'created_by'
            ).annotate(
                in_parent_field=Exists(parent_field_subquery)
            )

        return models.RuleDetail.objects.none()

    def get_serializer_class(self):
        """Use different serializers for create vs read operations."""
        if self.action == 'create':
            return serializers.RuleDetailCreateSerializer
        return serializers.RuleDetailReadSerializer

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new rule detail."""
        workspace_id = self.kwargs.get('workspace_id')
        if not workspace_id:
            raise PermissionDenied("No workspace context available")
        
        workspace = models.Workspace.objects.get(id=workspace_id)
        # WorkspaceValidationMixin already validated access in dispatch()
        
        kwargs = {'workspace': workspace}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)

    @extend_schema(tags=["Rules"])
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


class RuleNestedViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing rules with nested details, scoped per-workspace.
    
    URL: /api/v1/workspaces/{workspace_id}/rule-nested/
    """
    permission_classes = [IsAuthenticatedOrDebugReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleFilter

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.action in ['create', 'update', 'partial_update']:
            return serializers.RuleNestedSerializer
        else:
            return serializers.RuleNestedReadSerializer

    @extend_schema(tags=["Rules"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Rules"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Get rules with nested details filtered by workspace from URL path."""
        workspace_id = self.kwargs.get('workspace_id')
        # WorkspaceValidationMixin already validated access in dispatch()
        
        if workspace_id:
            return models.Rule.objects.filter(
                workspace_id=workspace_id
            ).prefetch_related(
                'rule_details__field',
                'rule_details__field__next_field',
                'rule_details__dimension',
                'rule_details__dimension__parent',
                'rule_details__dimension__dimension_values'
            )
        
        return models.Rule.objects.none()

    def perform_create(self, serializer):
        """Set created_by and workspace when creating a new rule."""
        workspace_id = self.kwargs.get('workspace_id')
        if not workspace_id:
            raise PermissionDenied("No workspace context available")
        
        workspace = models.Workspace.objects.get(id=workspace_id)
        # WorkspaceValidationMixin already validated access in dispatch()
        
        kwargs = {'workspace': workspace}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user

        serializer.save(**kwargs)

    @extend_schema(tags=["Rules"])
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
