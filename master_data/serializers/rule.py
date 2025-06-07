from rest_framework import serializers
from django.db.models import Max
from .. import models
from ..services import NamingPatternValidator


# # class ConventionSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = models.Convention
# #         fields = ['id', 'name', 'description',
# #                   'status', 'valid_from', 'valid_until']

# #     def validate(self, data):
# #         """
# #         Check that valid_until is after valid_from if provided
# #         """
# #         if data.get('valid_until') and data['valid_until'] < data['valid_from']:
# #             raise serializers.ValidationError({
# #                 "valid_until": "End date must be after start date"
# #             })
# #         return data


# # class ConventionPlatformSerializer(serializers.ModelSerializer):
# #     name = serializers.SerializerMethodField()
# #     platforms = serializers.SerializerMethodField()
# #     description = serializers.SerializerMethodField()
# #     created = serializers.DateTimeField(format="%Y-%m-%d")
# #     last_updated = serializers.DateTimeField(format="%Y-%m-%d")

# #     class Meta:
# #         model = models.ConventionPlatform
# #         fields = [
# #             'id',
# #             'convention',
# #             'name',
# #             'platforms',
# #             'description',
# #             'created',
# #             'last_updated'
# #         ]

# #     def get_name(self, obj):
# #         return obj.convention.name

# #     def get_description(self, obj):
# #         return obj.convention.description

# #     def get_platforms(self, obj):
# #         return [obj.platform.name]


# # class ConventionPlatformDetailSerializer(serializers.ModelSerializer):
# #     platform_name = serializers.SerializerMethodField()
# #     platform_fields = serializers.SerializerMethodField()
# #     convention_name = serializers.SerializerMethodField()

# #     class Meta:
# #         model = models.ConventionPlatform
# #         fields = [
# #             'id',
# #             'convention',
# #             'convention_name',
# #             'platform',
# #             'platform_name',
# #             'platform_fields',
# #             'created',
# #             'last_updated'
# #         ]

# #     def get_platform_name(self, obj):
# #         return obj.platform.name

# #     def get_platform_fields(self, obj):
# #         from .platform import FieldSerializer
# #         fields = models.Field.objects.filter(
# #             platform=obj.platform).order_by('field_level')
# #         return FieldSerializer(fields, many=True).data

# #     def get_convention_name(self, obj):
# #         return obj.convention.name


# class RuleDetailSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = models.RuleDetail
#         fields = ['id', 'rule', 'field', 'dimension']


class RuleDetailSerializer(serializers.ModelSerializer):
    platform_id = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    platform_slug = serializers.SerializerMethodField()
    rule_name = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()
    dimension_type = serializers.SerializerMethodField()
    parent_dimension_id = serializers.SerializerMethodField()
    parent_dimension_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    field_id = serializers.SerializerMethodField()
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    next_field = serializers.SerializerMethodField()
    in_parent_field = serializers.SerializerMethodField()
    is_max_field_level = serializers.SerializerMethodField()

    # New business logic fields
    effective_delimiter = serializers.SerializerMethodField()

    class Meta:
        model = models.RuleDetail
        fields = [
            "id",
            "rule",
            "rule_name",
            "platform_id",
            "platform_name",
            "platform_slug",
            "field",
            "field_id",
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
            "effective_delimiter",
            "is_required",
            "parent_dimension_name",
            "parent_dimension_id",
            "in_parent_field",
            "is_max_field_level",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_field_id(self, obj):
        return obj.field.id

    def get_field_name(self, obj):
        return obj.field.name

    def get_field_level(self, obj):
        return obj.field.field_level

    def get_platform_id(self, obj):
        return obj.rule.platform.id

    def get_platform_name(self, obj):
        return obj.rule.platform.name

    def get_platform_slug(self, obj):
        return obj.rule.platform.slug

    def get_dimension_name(self, obj):
        return obj.dimension.name

    def get_dimension_type(self, obj):
        return obj.dimension.type

    def get_parent_dimension_name(self, obj):
        if obj.dimension.parent_id:
            parent = models.Dimension.objects.get(id=obj.dimension.parent_id)
            return parent.name
        else:
            return None

    def get_parent_dimension_id(self, obj):
        if obj.dimension.parent_id:
            parent = models.Dimension.objects.get(id=obj.dimension.parent_id)
            return parent.id
        else:
            return None

    def get_next_field(self, obj):
        if obj.field.next_field_id:
            next_field = models.Field.objects.get(
                id=obj.field.next_field_id)
            return next_field.name
        else:
            return None

    def get_rule_name(self, obj):
        return obj.rule.name

    def get_in_parent_field(self, obj):
        field_level = obj.field.field_level
        if field_level <= 1:
            return False

        parent_exists = models.RuleDetail.objects.filter(
            field__platform=obj.field.platform,
            dimension=obj.dimension,
            field__field_level=field_level - 1
        ).exists()

        return parent_exists

    def get_is_max_field_level(self, obj):
        max_field_level = models.Field.objects.filter(
            platform=obj.field.platform
        ).aggregate(max_level=Max('field_level'))['max_level']

        return obj.field.field_level == max_field_level

    def get_effective_delimiter(self, obj):
        """Get the effective delimiter for this rule detail."""
        return obj.get_effective_delimiter()

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None


class RuleSerializer(serializers.ModelSerializer):
    platform_name = serializers.SerializerMethodField()
    platform_slug = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

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
            "configuration_errors",
            "required_dimensions",
            "fields_with_rules",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_platform_name(self, obj):
        return obj.platform.name

    def get_platform_slug(self, obj):
        return obj.platform.slug

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_configuration_errors(self, obj):
        """Get configuration validation errors."""
        return obj.validate_configuration()

    def get_required_dimensions(self, obj):
        """Get required dimensions by field."""
        result = {}
        for field in obj.get_fields_with_rules():
            field_obj = models.Field.objects.get(id=field)
            result[field_obj.name] = list(
                obj.get_required_dimensions(field_obj))
        return result

    def get_fields_with_rules(self, obj):
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

    def get_platform_name(self, obj):
        return obj.platform.name

    def get_platform_slug(self, obj):
        return obj.platform.slug

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_configuration_errors(self, obj):
        """Get configuration validation errors."""
        return obj.validate_configuration()

    def get_field_details(self, obj):
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
        # Key: (rule_id, dimension_id, field_level), Value: rule_detail
        rule_detail_lookup = {}

        # First pass: build the lookup table
        for detail in rule_details:
            key = (detail.rule_id, detail.dimension_id,
                   detail.field.field_level)
            rule_detail_lookup[key] = detail

        for detail in rule_details:
            field_id = detail.field.id

            if field_id not in grouped_details:
                # Initialize the field group with field information
                grouped_details[field_id] = {
                    'field': field_id,
                    'field_name': detail.field.name,
                    'field_level': detail.field.field_level,
                    'next_field': detail.field.next_field.name if detail.field.next_field_id else None,
                    'next_field_id': detail.field.next_field_id,
                    'can_generate': obj.can_generate_for_field(detail.field),
                    'dimensions': []
                }

            # Check for parent-child relationship
            parent_rule_detail_id = None
            inherits_from_parent = False

            # Look for a rule detail with same rule and dimension but smaller field_level
            current_field_level = detail.field.field_level
            for check_field_level in range(1, current_field_level):
                parent_key = (detail.rule_id, detail.dimension_id,
                              check_field_level)
                if parent_key in rule_detail_lookup:
                    parent_rule_detail = rule_detail_lookup[parent_key]
                    parent_rule_detail_id = parent_rule_detail.id
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
                                          if detail.dimension.parent_id else None),
                'parent_dimension_id': detail.dimension.parent_id,
                # New parent-child relationship fields
                'inherits_from_parent': inherits_from_parent,
                'parent_rule_detail_id': parent_rule_detail_id,
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

            grouped_details[field_id]['dimensions'].append(dimension_info)

        # Process each field group to add computed information
        for field_id, field_data in grouped_details.items():
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
            field_obj = models.Field.objects.get(id=field_id)
            field_data['required_dimensions'] = list(
                obj.get_required_dimensions(field_obj))

        # Convert dictionary to list and sort by field level
        result = list(grouped_details.values())
        result.sort(key=lambda x: x['field_level'])

        return result


class RulePreviewRequestSerializer(serializers.Serializer):
    """Serializer for rule preview requests."""
    field_id = serializers.IntegerField()
    sample_values = serializers.DictField(
        child=serializers.CharField(),
        help_text="Sample dimension values for preview generation"
    )

    def validate_field_id(self, value):
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

    def get_configuration_errors(self, obj):
        """Get detailed configuration validation errors."""
        return obj.validate_configuration()

    def get_can_generate_for_fields(self, obj):
        """Get fields this rule can generate strings for."""
        fields = models.Field.objects.filter(platform=obj.platform)
        result = {}
        for field in fields:
            result[field.name] = obj.can_generate_for_field(field)
        return result

    def get_required_dimensions_by_field(self, obj):
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

    def get_created_by_name(self, obj):
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
    rule_id = serializers.IntegerField()

    def validate_rule_id(self, value):
        """Validate that rule exists."""
        try:
            models.Rule.objects.get(id=value)
        except models.Rule.DoesNotExist:
            raise serializers.ValidationError("Rule does not exist")
        return value
