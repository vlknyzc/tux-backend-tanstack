from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db import transaction

from .. import serializers
from .. import models
from ..services import NamingPatternValidator


class RuleFilter(filters.FilterSet):
    platform = filters.NumberFilter(method='filter_platform_id')
    field = filters.NumberFilter(method='filter_field_id')
    status = filters.CharFilter()
    is_default = filters.BooleanFilter()

    class Meta:
        model = models.Rule
        fields = [
            'id',
            'field',
            'platform',
            'status',
            'is_default'
        ]

    def filter_platform_id(self, queryset, name, value):
        return queryset.filter(platform__id=value)

    def filter_field_id(self, queryset, name, value):
        return queryset.filter(rule_details__field__id=value).distinct()


class RuleViewSet(viewsets.ModelViewSet):
    queryset = models.Rule.objects.all().select_related(
        'platform').prefetch_related('rule_details')
    serializer_class = serializers.RuleSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleFilter

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new rule"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

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
        """Set this rule as the default for its platform."""
        rule = self.get_object()

        try:
            with transaction.atomic():
                # Unset any existing default for this platform
                models.Rule.objects.filter(
                    platform=rule.platform,
                    is_default=True
                ).update(is_default=False)

                # Set this rule as default
                rule.is_default = True
                rule.save()

                return Response({
                    'message': f'Rule "{rule.name}" is now the default for platform "{rule.platform.name}"',
                    'rule_id': rule.id,
                    'platform_id': rule.platform.id
                })

        except Exception as e:
            return Response(
                {'error': f'Failed to set default rule: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def defaults(self, request):
        """Get all default rules by platform."""
        default_rules = models.Rule.objects.filter(
            is_default=True).select_related('platform')
        serializer = self.get_serializer(default_rules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def required_dimensions(self, request, pk=None):
        """Get required dimensions for all fields in this rule."""
        rule = self.get_object()

        result = {}
        fields = models.Field.objects.filter(platform=rule.platform)

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
            'fields': result
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active rules."""
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

    class Meta:
        model = models.RuleDetail
        fields = ['id', 'rule', 'dimension_order',
                  'field', 'platform', 'is_required']


class RuleDetailViewSet(viewsets.ModelViewSet):
    queryset = models.RuleDetail.objects.all().select_related(
        'rule', 'field', 'dimension', 'rule__platform'
    )
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleDetailFilter

    def get_serializer_class(self):
        """Use different serializers for create vs read operations."""
        if self.action == 'create':
            return serializers.RuleDetailCreateSerializer
        return serializers.RuleDetailSerializer

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new rule detail"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['post'])
    def validate_order(self, request):
        """Validate dimension order for a rule and field combination."""
        rule_id = request.data.get('rule_id')
        field_id = request.data.get('field_id')

        if not rule_id or not field_id:
            return Response(
                {'error': 'rule_id and field_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rule = models.Rule.objects.get(id=rule_id)
            field = models.Field.objects.get(id=field_id)

            rule_details = models.RuleDetail.objects.filter(
                rule=rule, field=field
            ).order_by('dimension_order')

            # Check for gaps in dimension order
            orders = [rd.dimension_order for rd in rule_details]
            expected_orders = list(range(1, len(orders) + 1))

            has_gaps = orders != expected_orders

            return Response({
                'rule_id': rule_id,
                'field_id': field_id,
                'current_orders': orders,
                'expected_orders': expected_orders,
                'has_gaps': has_gaps,
                'is_valid': not has_gaps
            })

        except models.Rule.DoesNotExist:
            return Response({'error': 'Rule not found'}, status=status.HTTP_404_NOT_FOUND)
        except models.Field.DoesNotExist:
            return Response({'error': 'Field not found'}, status=status.HTTP_404_NOT_FOUND)


class RuleNestedViewSet(viewsets.ModelViewSet):
    queryset = models.Rule.objects.all().prefetch_related(
        'rule_details__field', 'rule_details__dimension')
    serializer_class = serializers.RuleNestedSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RuleFilter

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new rule"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone a rule with all its rule details."""
        original_rule = self.get_object()
        new_name = request.data.get('name')

        if not new_name:
            return Response(
                {'error': 'name is required for cloning'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Create new rule
                new_rule = models.Rule.objects.create(
                    platform=original_rule.platform,
                    name=new_name,
                    description=f"Cloned from {original_rule.name}",
                    status=original_rule.status,
                    is_default=False  # Never clone as default
                )

                # Clone all rule details
                for detail in original_rule.rule_details.all():
                    models.RuleDetail.objects.create(
                        rule=new_rule,
                        field=detail.field,
                        dimension=detail.dimension,
                        prefix=detail.prefix,
                        suffix=detail.suffix,
                        delimiter=detail.delimiter,
                        dimension_order=detail.dimension_order,
                        is_required=detail.is_required
                    )

                serializer = self.get_serializer(new_rule)
                return Response({
                    'message': f'Rule cloned successfully as "{new_name}"',
                    'original_rule_id': original_rule.id,
                    'new_rule': serializer.data
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Cloning failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
