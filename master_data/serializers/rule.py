from rest_framework import serializers
from django.db.models import Max
from .. import models
from ..services import NamingPatternValidator
from typing import Optional, Dict, List, Any


class RuleDetailSerializer(serializers.ModelSerializer):
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
        model = models.RuleDetail
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

    def get_parent_dimension_name(self, obj) -> Optional[str]:
        if obj.dimension.parent:
            parent = models.Dimension.objects.get(id=obj.dimension.parent.id)
            return parent.name
        else:
            return None

    def get_next_field(self, obj) -> Optional[str]:
        if obj.field.next_field:
            next_field = models.Field.objects.get(
                id=obj.field.next_field.id)
            return next_field.name
        else:
            return None

    def get_rule_name(self, obj) -> str:
        return obj.rule.name

    def get_in_parent_field(self, obj) -> bool:
        field_level = obj.field.field_level
        if field_level <= 1:
            return False

        parent_exists = models.RuleDetail.objects.filter(
            field__platform=obj.field.platform,
            dimension=obj.dimension,
            field__field_level=field_level - 1
        ).exists()

        return parent_exists

    def get_is_max_field_level(self, obj) -> bool:
        max_field_level = models.Field.objects.filter(
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


class RuleSerializer(serializers.ModelSerializer):
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
        model = models.Rule
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

    def get_required_dimensions(self, obj) -> Dict[str, List[str]]:
        """Get required dimensions by field."""
        result = {}
        for field in obj.get_fields_with_rules():
            field_obj = models.Field.objects.get(id=field)
            result[field_obj.name] = list(
                obj.get_required_dimensions(field_obj))
        return result

    def get_fields_with_rules(self, obj) -> List[Dict[str, Any]]:
        """Get all fields that have rule details configured."""
        field_ids = obj.get_fields_with_rules()
        fields = models.Field.objects.filter(id__in=field_ids)
        return [{"id": f.id, "name": f.name, "field_level": f.field_level} for f in fields]


class RuleNestedSerializer(serializers.ModelSerializer):
    field_details = serializers.SerializerMethodField()
    configuration_errors = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    platform_slug = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Rule
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
            "configuration_errors",
            "field_details",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

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
                    'field': field,
                    'field_name': detail.field.name,
                    'field_level': detail.field.field_level,
                    'next_field': detail.field.next_field,
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
                'parent_dimension': detail.dimension.parent,
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
            field_obj = models.Field.objects.get(id=field.id)
            field_data['required_dimensions'] = list(
                obj.get_required_dimensions(field_obj))

        # Convert dictionary to list and sort by field level
        result = list(grouped_details.values())
        result.sort(key=lambda x: x['field_level'])

        return result


class RulePreviewRequestSerializer(serializers.Serializer):
    """Serializer for rule preview requests."""
    field = serializers.IntegerField()
    sample_values = serializers.DictField(
        child=serializers.CharField(),
        help_text="Sample dimension values for preview generation"
    )

    def validate_field(self, value):
        """Validate that field exists."""
        try:
            models.Field.objects.get(id=value)
        except models.Field.DoesNotExist:
            raise serializers.ValidationError("Field does not exist")
        return value


class RuleValidationSerializer(serializers.ModelSerializer):
    """Serializer for rule validation results."""
    configuration_errors = serializers.SerializerMethodField()
    can_generate_for_fields = serializers.SerializerMethodField()
    required_dimensions_by_field = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Rule
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "status",
            "is_default",
            "platform",
            "configuration_errors",
            "can_generate_for_fields",
            "required_dimensions_by_field",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_configuration_errors(self, obj) -> List[str]:
        """Get detailed configuration validation errors."""
        return obj.validate_configuration()

    def get_can_generate_for_fields(self, obj) -> Dict[str, bool]:
        """Get fields this rule can generate strings for."""
        fields = models.Field.objects.filter(platform=obj.platform)
        result = {}
        for field in fields:
            result[field.name] = obj.can_generate_for_field(field)
        return result

    def get_required_dimensions_by_field(self, obj) -> Dict[str, Dict[str, List[str]]]:
        """Get required dimensions organized by field."""
        result = {}
        fields = models.Field.objects.filter(platform=obj.platform)
        for field in fields:
            if obj.can_generate_for_field(field):
                result[field.name] = {
                    "dimensions": list(obj.get_required_dimensions(field)),
                    "generation_order": obj.get_generation_order(field)
                }
        return result

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None


class RuleDetailCreateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating rule details with validation."""

    class Meta:
        model = models.RuleDetail
        fields = [
            'rule',
            'field',
            'dimension',
            'prefix',
            'suffix',
            'delimiter',
            'dimension_order',
            'is_required',
        ]

    def validate(self, attrs):
        """Enhanced validation for rule detail creation."""
        rule = attrs['rule']
        field = attrs['field']
        dimension = attrs['dimension']

        # Validate rule and field belong to same platform
        if rule.platform != field.platform:
            raise serializers.ValidationError(
                "Rule and field must belong to the same platform"
            )

        # Check for duplicate dimension in same rule+field
        if models.RuleDetail.objects.filter(
            rule=rule,
            field=field,
            dimension=dimension
        ).exists():
            raise serializers.ValidationError(
                f"Dimension '{dimension.name}' already exists for this rule and field"
            )

        return attrs


class DefaultRuleRequestSerializer(serializers.Serializer):
    """Serializer for setting default rule."""
    rule = serializers.IntegerField()

    def validate_rule(self, value):
        """Validate that rule exists."""
        try:
            models.Rule.objects.get(id=value)
        except models.Rule.DoesNotExist:
            raise serializers.ValidationError("Rule does not exist")
        return value
