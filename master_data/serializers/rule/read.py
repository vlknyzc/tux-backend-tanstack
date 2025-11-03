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
        This groups rule details by field and includes all dimension information.
        """
        # Get all rule details for this rule with optimized queries
        rule_details = obj.rule_details.select_related(
            'field', 'dimension', 'dimension__parent'
        ).prefetch_related(
            'dimension__dimension_values'
        ).all()

        # Create a dictionary to group by field
        grouped_details = {}

        # Create a lookup for parent-child relationships
        # Key: (rule, dimension, field_level), Value: rule_detail
        rule_detail_lookup = {}

        # First pass: build the lookup table
        for detail in rule_details:
            key = (detail.rule, detail.dimension,
                   detail.field.field_level)
            rule_detail_lookup[key] = detail

        for detail in rule_details:
            field = detail.field

            if field not in grouped_details:
                # Initialize the field group with field information
                grouped_details[field] = {
                    'field': field.id,
                    'field_name': detail.field.name,
                    'field_level': detail.field.field_level,
                    'next_field': detail.field.next_field.id if detail.field.next_field else None,
                    'can_generate': obj.can_generate_for_field(detail.field),
                    'dimensions': []
                }

            # Check for parent-child relationship
            parent_rule_detail = None
            inherits_from_parent = False

            # Look for a rule detail with same rule and dimension but smaller field_level
            current_field_level = detail.field.field_level
            for check_field_level in range(1, current_field_level):
                parent_key = (detail.rule, detail.dimension,
                              check_field_level)
                if parent_key in rule_detail_lookup:
                    parent_rule_detail = rule_detail_lookup[parent_key]
                    parent_rule_detail = parent_rule_detail.id
                    inherits_from_parent = True
                    break  # Found the parent (smallest field_level)

            # Add comprehensive dimension information
            dimension_info = {
                'id': detail.id,
                'dimension': detail.dimension.id,
                'dimension_name': detail.dimension.name,
                'dimension_type': detail.dimension.type,
                'dimension_description': detail.dimension.description or '',
                'dimension_order': detail.dimension_order,
                'is_required': detail.is_required,
                'prefix': detail.prefix or '',
                'suffix': detail.suffix or '',
                'delimiter': detail.delimiter or '',
                'effective_delimiter': detail.get_effective_delimiter(),
                'parent_dimension_name': (detail.dimension.parent.name
                                          if detail.dimension.parent else None),
                'parent_dimension': detail.dimension.parent.id if detail.dimension.parent else None,
                # New parent-child relationship fields
                'inherits_from_parent': inherits_from_parent,
                'parent_rule_detail': parent_rule_detail,
                'dimension_values': [
                    {
                        'id': value.id,
                        'value': value.value,
                        'label': value.label,
                        'utm': value.utm,
                        'description': value.description or '',
                        'is_active': getattr(value, 'is_active', True),
                    } for value in detail.dimension.dimension_values.all()
                ],
                'dimension_value_count': detail.dimension.dimension_values.count(),
                'allows_freetext': detail.dimension.type == 'text',
                'is_dropdown': detail.dimension.type == 'list',
            }

            grouped_details[field]['dimensions'].append(dimension_info)

        # Process each field group to add computed information
        for field, field_data in grouped_details.items():
            # Sort dimensions by order
            field_data['dimensions'].sort(key=lambda x: x['dimension_order'])

            # Generate field rule preview
            dimension_preview_parts = []
            for dim in field_data['dimensions']:
                part = (dim.get('prefix', '') or '') + \
                    f"[{dim.get('dimension_name', '')}]" + \
                       (dim.get('suffix', '') or '') + \
                       (dim.get('delimiter', '') or '')
                dimension_preview_parts.append(part)

            field_data['field_rule_preview'] = ''.join(dimension_preview_parts)
            field_data['dimension_count'] = len(field_data['dimensions'])
            field_data['required_dimension_count'] = sum(
                1 for d in field_data['dimensions'] if d.get('is_required'))

            # Get required dimensions for this field
            field_obj = Field.objects.get(id=field.id)
            required_dims = obj.get_required_dimensions(field_obj)
            # Convert to list of dimension IDs if they're model instances
            if required_dims:
                field_data['required_dimensions'] = [
                    dim.id if hasattr(dim, 'id') else dim for dim in required_dims
                ]
            else:
                field_data['required_dimensions'] = []

        # Convert dictionary to list and sort by field level
        result = list(grouped_details.values())
        result.sort(key=lambda x: x['field_level'])

        return result
