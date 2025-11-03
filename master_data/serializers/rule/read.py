"""
Read serializers for displaying/retrieving Rule and RuleDetail data.

This module contains serializers responsible for reading and displaying
rules and rule details with computed fields and nested structures.
"""

from rest_framework import serializers
from django.db.models import Max
from typing import Optional, List, Dict, Any
from ...models import Rule, RuleDetail, Field


class RuleDetailReadSerializer(serializers.ModelSerializer):
    """Serializer for reading rule details with computed fields."""

    platform = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    platform_slug = serializers.SerializerMethodField()
    rule_name = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()
    dimension_type = serializers.SerializerMethodField()
    parent_dimension = serializers.SerializerMethodField()
    parent_dimension_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    next_field = serializers.SerializerMethodField()
    in_parent_field = serializers.SerializerMethodField()
    is_max_field_level = serializers.SerializerMethodField()

    class Meta:
        model = RuleDetail
        fields = [
            "id",
            "rule",
            "rule_name",
            "platform",
            "platform_name",
            "platform_slug",
            "field",
            "field_name",
            "field_level",
            "next_field",
            "dimension",
            "dimension_name",
            "dimension_type",
            "dimension_order",
            "prefix",
            "suffix",
            "delimiter",
            "is_required",
            "parent_dimension_name",
            "parent_dimension",
            "in_parent_field",
            "is_max_field_level",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_platform(self, obj) -> int:
        return obj.rule.platform.id

    def get_field_name(self, obj) -> str:
        return obj.field.name

    def get_field_level(self, obj) -> int:
        return obj.field.field_level

    def get_platform_name(self, obj) -> str:
        return obj.rule.platform.name

    def get_platform_slug(self, obj) -> str:
        return obj.rule.platform.slug

    def get_dimension_name(self, obj) -> str:
        return obj.dimension.name

    def get_dimension_type(self, obj) -> str:
        return obj.dimension.type

    def get_parent_dimension(self, obj) -> Optional[int]:
        if obj.dimension.parent:
            return obj.dimension.parent.id
        return None

    def get_parent_dimension_name(self, obj) -> Optional[str]:
        # Use already-loaded parent dimension from select_related
        if obj.dimension.parent:
            return obj.dimension.parent.name
        return None

    def get_next_field(self, obj) -> Optional[str]:
        if obj.field.next_field_id:
            return obj.field.next_field.name
        return None

    def get_rule_name(self, obj) -> str:
        return obj.rule.name

    def get_in_parent_field(self, obj) -> bool:
        # Use annotated field from queryset to avoid N+1 query
        # If annotation exists, use it; otherwise fall back to field_level check
        if hasattr(obj, 'in_parent_field'):
            return obj.in_parent_field

        # Fallback for cases where annotation isn't available
        field_level = obj.field.field_level
        if field_level <= 1:
            return False

        parent_exists = RuleDetail.objects.filter(
            field__platform=obj.field.platform,
            dimension=obj.dimension,
            field__field_level=field_level - 1
        ).exists()

        return parent_exists

    def get_is_max_field_level(self, obj) -> bool:
        max_field_level = Field.objects.filter(
            platform=obj.field.platform
        ).aggregate(max_level=Max('field_level'))['max_level']

        return obj.field.field_level == max_field_level

    def get_effective_delimiter(self, obj) -> str:
        """Get the effective delimiter for this rule detail."""
        return obj.get_effective_delimiter()

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None


class RuleReadSerializer(serializers.ModelSerializer):
    """Serializer for reading rules with business logic fields."""

    platform_name = serializers.SerializerMethodField()
    platform_slug = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    workspace = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()

    # New business logic fields
    configuration_errors = serializers.SerializerMethodField()
    required_dimensions = serializers.SerializerMethodField()
    fields_with_rules = serializers.SerializerMethodField()

    class Meta:
        model = Rule
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "status",
            "is_default",
            "platform",
            "platform_name",
            "platform_slug",
            "workspace",
            "workspace_name",
            "configuration_errors",
            "required_dimensions",
            "fields_with_rules",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    extra_kwargs = {
        'workspace': {'required': True, 'allow_null': False, "help_text": "ID of the workspace this rule belongs to"},
        'slug': {'required': False, 'allow_blank': True, 'help_text': 'URL-friendly version of the name (auto-generated)'},
    }

    def get_platform_name(self, obj) -> str:
        return obj.platform.name

    def get_platform_slug(self, obj) -> str:
        return obj.platform.slug

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_workspace(self, obj) -> int:
        return obj.workspace.id

    def get_workspace_name(self, obj) -> Optional[str]:
        return obj.workspace.name if obj.workspace else None

    def get_configuration_errors(self, obj) -> List[str]:
        """Get configuration validation errors."""
        return obj.validate_configuration()

    def get_fields_with_rules(self, obj) -> List[Dict[str, Any]]:
        """Get all fields that have rule details configured."""
        field_ids = list(obj.get_fields_with_rules()
                         )  # Convert to list to avoid multiple evaluations
        fields = Field.objects.filter(id__in=field_ids)
        return [{"id": f.id, "name": f.name, "field_level": f.field_level} for f in fields]

    def get_required_dimensions(self, obj) -> Dict[str, List[str]]:
        """Get required dimensions by field."""
        result = {}
        # Convert to list to avoid multiple evaluations
        field_ids = list(obj.get_fields_with_rules())
        fields = Field.objects.filter(id__in=field_ids)
        for field in fields:
            result[field.name] = list(obj.get_required_dimensions(field))
        return result


class RuleNestedReadSerializer(serializers.ModelSerializer):
    """Serializer for reading rules with comprehensive nested field details."""

    field_details = serializers.SerializerMethodField()
    configuration_errors = serializers.SerializerMethodField()
    platform_id = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    platform_slug = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Rule
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "status",
            "is_default",
            "platform_id",
            "platform_name",
            "platform_slug",
            "configuration_errors",
            "field_details",
            "created_by_id",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_platform_id(self, obj) -> int:
        return obj.platform.id

    def get_created_by_id(self, obj) -> Optional[int]:
        return obj.created_by.id if obj.created_by else None

    def get_platform_name(self, obj) -> str:
        return obj.platform.name

    def get_platform_slug(self, obj) -> str:
        return obj.platform.slug

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_configuration_errors(self, obj) -> List[str]:
        """Get configuration validation errors."""
        return obj.validate_configuration()

    def get_field_details(self, obj) -> List[Dict[str, Any]]:
        """
        Get comprehensive field details including dimension values for frontend.
        This orchestrates the process of grouping rule details by field.
        """
        # Get optimized queryset
        rule_details = self._get_optimized_rule_details(obj)

        # Build lookup table for parent-child relationships
        rule_detail_lookup = self._build_rule_detail_lookup(rule_details)

        # Group details by field and add dimension information
        grouped_details = self._group_details_by_field(
            obj, rule_details, rule_detail_lookup
        )

        # Add computed information to each field group
        self._add_computed_field_info(obj, grouped_details)

        # Convert to sorted list
        return self._convert_to_sorted_list(grouped_details)

    def _get_optimized_rule_details(self, obj):
        """Get rule details with optimized database queries."""
        return obj.rule_details.select_related(
            'field', 'dimension', 'dimension__parent'
        ).prefetch_related(
            'dimension__dimension_values'
        ).all()

    def _build_rule_detail_lookup(self, rule_details) -> Dict:
        """
        Build lookup table for parent-child relationships.
        Key: (rule, dimension, field_level), Value: rule_detail
        """
        return {
            (detail.rule, detail.dimension, detail.field.field_level): detail
            for detail in rule_details
        }

    def _group_details_by_field(
        self, obj, rule_details, rule_detail_lookup: Dict
    ) -> Dict:
        """Group rule details by field and add dimension information."""
        grouped_details = {}

        for detail in rule_details:
            field = detail.field

            # Initialize field group if not exists
            if field not in grouped_details:
                grouped_details[field] = self._init_field_group(obj, detail)

            # Find parent rule detail
            parent_info = self._find_parent_rule_detail(
                detail, rule_detail_lookup
            )

            # Build dimension info
            dimension_info = self._build_dimension_info(detail, parent_info)

            grouped_details[field]['dimensions'].append(dimension_info)

        return grouped_details

    def _init_field_group(self, obj, detail) -> Dict[str, Any]:
        """Initialize a field group with basic field information."""
        field = detail.field
        return {
            'field': field.id,
            'field_name': field.name,
            'field_level': field.field_level,
            'next_field': field.next_field.id if field.next_field else None,
            'can_generate': obj.can_generate_for_field(field),
            'dimensions': []
        }

    def _find_parent_rule_detail(
        self, detail, rule_detail_lookup: Dict
    ) -> Dict[str, Any]:
        """
        Find parent rule detail if exists.
        Returns dict with 'parent_rule_detail' and 'inherits_from_parent'.
        """
        current_field_level = detail.field.field_level

        for check_field_level in range(1, current_field_level):
            parent_key = (detail.rule, detail.dimension, check_field_level)

            if parent_key in rule_detail_lookup:
                parent_detail = rule_detail_lookup[parent_key]
                return {
                    'parent_rule_detail': parent_detail.id,
                    'inherits_from_parent': True
                }

        return {
            'parent_rule_detail': None,
            'inherits_from_parent': False
        }

    def _build_dimension_info(
        self, detail, parent_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comprehensive dimension information."""
        dimension = detail.dimension

        return {
            'id': detail.id,
            'dimension': dimension.id,
            'dimension_name': dimension.name,
            'dimension_type': dimension.type,
            'dimension_description': dimension.description or '',
            'dimension_order': detail.dimension_order,
            'is_required': detail.is_required,
            'prefix': detail.prefix or '',
            'suffix': detail.suffix or '',
            'delimiter': detail.delimiter or '',
            'effective_delimiter': detail.get_effective_delimiter(),
            'parent_dimension_name': (
                dimension.parent.name if dimension.parent else None
            ),
            'parent_dimension': (
                dimension.parent.id if dimension.parent else None
            ),
            'inherits_from_parent': parent_info['inherits_from_parent'],
            'parent_rule_detail': parent_info['parent_rule_detail'],
            'dimension_values': self._get_dimension_values(dimension),
            'dimension_value_count': dimension.dimension_values.count(),
            'allows_freetext': dimension.type == 'text',
            'is_dropdown': dimension.type == 'list',
        }

    def _get_dimension_values(self, dimension) -> List[Dict[str, Any]]:
        """Get formatted dimension values."""
        return [
            {
                'id': value.id,
                'value': value.value,
                'label': value.label,
                'utm': value.utm,
                'description': value.description or '',
                'is_active': getattr(value, 'is_active', True),
            }
            for value in dimension.dimension_values.all()
        ]

    def _add_computed_field_info(self, obj, grouped_details: Dict):
        """Add computed information to each field group."""
        for field, field_data in grouped_details.items():
            # Sort dimensions by order
            field_data['dimensions'].sort(key=lambda x: x['dimension_order'])

            # Add preview and counts
            field_data['field_rule_preview'] = self._generate_field_rule_preview(
                field_data['dimensions']
            )
            field_data['dimension_count'] = len(field_data['dimensions'])
            field_data['required_dimension_count'] = sum(
                1 for d in field_data['dimensions'] if d.get('is_required')
            )

            # Add required dimensions
            field_data['required_dimensions'] = self._get_required_dimension_ids(
                obj, field
            )

    def _generate_field_rule_preview(self, dimensions: List[Dict]) -> str:
        """Generate field rule preview string."""
        parts = [
            f"{dim.get('prefix', '')}"
            f"[{dim.get('dimension_name', '')}]"
            f"{dim.get('suffix', '')}"
            f"{dim.get('delimiter', '')}"
            for dim in dimensions
        ]
        return ''.join(parts)

    def _get_required_dimension_ids(self, obj, field) -> List[int]:
        """Get list of required dimension IDs for a field."""
        field_obj = Field.objects.get(id=field.id)
        required_dims = obj.get_required_dimensions(field_obj)

        if not required_dims:
            return []

        return [
            dim.id if hasattr(dim, 'id') else dim
            for dim in required_dims
        ]

    def _convert_to_sorted_list(self, grouped_details: Dict) -> List[Dict]:
        """Convert grouped details dict to sorted list."""
        result = list(grouped_details.values())
        result.sort(key=lambda x: x['field_level'])
        return result
