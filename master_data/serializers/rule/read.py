"""
Read serializers for displaying/retrieving Rule and RuleDetail data.

This module contains serializers responsible for reading and displaying
rules and rule details with computed fields and nested structures.
"""

from rest_framework import serializers
from django.db.models import Max
from typing import Optional, List, Dict, Any
from ...models import Rule, RuleDetail, Entity


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
    entity_name = serializers.SerializerMethodField()
    entity_level = serializers.SerializerMethodField()
    next_entity = serializers.SerializerMethodField()
    in_parent_entity = serializers.SerializerMethodField()
    is_max_entity_level = serializers.SerializerMethodField()

    class Meta:
        model = RuleDetail
        fields = [
            "id",
            "rule",
            "rule_name",
            "platform",
            "platform_name",
            "platform_slug",
            "entity",
            "entity_name",
            "entity_level",
            "next_entity",
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
            "in_parent_entity",
            "is_max_entity_level",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_platform(self, obj) -> int:
        return obj.rule.platform.id

    def get_entity_name(self, obj) -> str:
        return obj.entity.name

    def get_entity_level(self, obj) -> int:
        return obj.entity.entity_level

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

    def get_next_entity(self, obj) -> Optional[str]:
        if obj.entity.next_entity_id:
            return obj.entity.next_entity.name
        return None

    def get_rule_name(self, obj) -> str:
        return obj.rule.name

    def get_in_parent_entity(self, obj) -> bool:
        # Use annotated field from queryset to avoid N+1 query
        # If annotation exists, use it; otherwise fall back to entity_level check
        if hasattr(obj, 'in_parent_entity'):
            return obj.in_parent_entity

        # Fallback for cases where annotation isn't available
        entity_level = obj.entity.entity_level
        if entity_level <= 1:
            return False

        parent_exists = RuleDetail.objects.filter(
            entity__platform=obj.entity.platform,
            dimension=obj.dimension,
            entity__entity_level=entity_level - 1
        ).exists()

        return parent_exists

    def get_is_max_entity_level(self, obj) -> bool:
        max_entity_level = Entity.objects.filter(
            platform=obj.entity.platform
        ).aggregate(max_level=Max('entity_level'))['max_level']

        return obj.entity.entity_level == max_entity_level

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
    entities_with_rules = serializers.SerializerMethodField()

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
            "entities_with_rules",
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

    def get_entities_with_rules(self, obj) -> List[Dict[str, Any]]:
        """Get all entities that have rule details configured."""
        entity_ids = list(obj.get_entities_with_rules()
                         )  # Convert to list to avoid multiple evaluations
        entities = Entity.objects.filter(id__in=entity_ids)
        return [{"id": e.id, "name": e.name, "entity_level": e.entity_level} for e in entities]

    def get_required_dimensions(self, obj) -> Dict[str, List[str]]:
        """Get required dimensions by entity."""
        result = {}
        # Convert to list to avoid multiple evaluations
        entity_ids = list(obj.get_entities_with_rules())
        entities = Entity.objects.filter(id__in=entity_ids)
        for entity in entities:
            result[entity.name] = list(obj.get_required_dimensions(entity))
        return result


class RuleNestedReadSerializer(serializers.ModelSerializer):
    """Serializer for reading rules with comprehensive nested entity details."""

    entity_details = serializers.SerializerMethodField()
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
            "entity_details",
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

    def get_entity_details(self, obj) -> List[Dict[str, Any]]:
        """
        Get comprehensive entity details including dimension values for frontend.
        This orchestrates the process of grouping rule details by entity.
        """
        # Get optimized queryset
        rule_details = self._get_optimized_rule_details(obj)

        # Build lookup table for parent-child relationships
        rule_detail_lookup = self._build_rule_detail_lookup(rule_details)

        # Group details by entity and add dimension information
        grouped_details = self._group_details_by_entity(
            obj, rule_details, rule_detail_lookup
        )

        # Add computed information to each entity group
        self._add_computed_entity_info(obj, grouped_details)

        # Convert to sorted list
        return self._convert_to_sorted_list(grouped_details)

    def _get_optimized_rule_details(self, obj):
        """Get rule details with optimized database queries."""
        return obj.rule_details.select_related(
            'entity', 'dimension', 'dimension__parent'
        ).prefetch_related(
            'dimension__dimension_values'
        ).all()

    def _build_rule_detail_lookup(self, rule_details) -> Dict:
        """
        Build lookup table for parent-child relationships.
        Key: (rule, dimension, entity_level), Value: rule_detail
        """
        return {
            (detail.rule, detail.dimension, detail.entity.entity_level): detail
            for detail in rule_details
        }

    def _group_details_by_entity(
        self, obj, rule_details, rule_detail_lookup: Dict
    ) -> Dict:
        """Group rule details by entity and add dimension information."""
        grouped_details = {}

        for detail in rule_details:
            entity = detail.entity

            # Initialize entity group if not exists
            if entity not in grouped_details:
                grouped_details[entity] = self._init_entity_group(obj, detail)

            # Find parent rule detail
            parent_info = self._find_parent_rule_detail(
                detail, rule_detail_lookup
            )

            # Build dimension info
            dimension_info = self._build_dimension_info(detail, parent_info)

            grouped_details[entity]['dimensions'].append(dimension_info)

        return grouped_details

    def _init_entity_group(self, obj, detail) -> Dict[str, Any]:
        """Initialize an entity group with basic entity information."""
        entity = detail.entity
        return {
            'entity': entity.id,
            'entity_name': entity.name,
            'entity_level': entity.entity_level,
            'next_entity': entity.next_entity.id if entity.next_entity else None,
            'can_generate': obj.can_generate_for_entity(entity),
            'dimensions': []
        }

    def _find_parent_rule_detail(
        self, detail, rule_detail_lookup: Dict
    ) -> Dict[str, Any]:
        """
        Find parent rule detail if exists.
        Returns dict with 'parent_rule_detail' and 'inherits_from_parent'.
        """
        current_entity_level = detail.entity.entity_level

        for check_entity_level in range(1, current_entity_level):
            parent_key = (detail.rule, detail.dimension, check_entity_level)

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

    def _add_computed_entity_info(self, obj, grouped_details: Dict):
        """Add computed information to each entity group."""
        for entity, entity_data in grouped_details.items():
            # Sort dimensions by order
            entity_data['dimensions'].sort(key=lambda x: x['dimension_order'])

            # Add preview and counts
            entity_data['entity_rule_preview'] = self._generate_entity_rule_preview(
                entity_data['dimensions']
            )
            entity_data['dimension_count'] = len(entity_data['dimensions'])
            entity_data['required_dimension_count'] = sum(
                1 for d in entity_data['dimensions'] if d.get('is_required')
            )

            # Add required dimensions
            entity_data['required_dimensions'] = self._get_required_dimension_ids(
                obj, entity
            )

    def _generate_entity_rule_preview(self, dimensions: List[Dict]) -> str:
        """Generate entity rule preview string."""
        parts = [
            f"{dim.get('prefix', '')}"
            f"[{dim.get('dimension_name', '')}]"
            f"{dim.get('suffix', '')}"
            f"{dim.get('delimiter', '')}"
            for dim in dimensions
        ]
        return ''.join(parts)

    def _get_required_dimension_ids(self, obj, entity) -> List[int]:
        """Get list of required dimension IDs for an entity."""
        entity_obj = Entity.objects.get(id=entity.id)
        required_dims = obj.get_required_dimensions(entity_obj)

        if not required_dims:
            return []

        return [
            dim.id if hasattr(dim, 'id') else dim
            for dim in required_dims
        ]

    def _convert_to_sorted_list(self, grouped_details: Dict) -> List[Dict]:
        """Convert grouped details dict to sorted list."""
        result = list(grouped_details.values())
        result.sort(key=lambda x: x['entity_level'])
        return result
