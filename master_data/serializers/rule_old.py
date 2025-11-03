from rest_framework import serializers
from django.db.models import Max
from .. import models
from typing import Optional, Dict, List, Any
from .base import WorkspaceOwnedSerializer


# =============================================================================
# WRITE SERIALIZERS (for creating/updating data)
# =============================================================================

class RuleDetailCreateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating rule details with validation."""

    class Meta:
        model = models.RuleDetail
        fields = [
            'field',
            'dimension',
            'prefix',
            'suffix',
            'delimiter',
            'dimension_order',
            'is_required',
        ]
        extra_kwargs = {
            'rule': {'required': False, 'write_only': True}
        }

    def validate(self, attrs):
        """Enhanced validation for rule detail creation."""
        field = attrs['field']
        dimension = attrs['dimension']

        # Note: rule validation is handled at the RuleNestedSerializer level
        # since the rule doesn't exist yet when this serializer validates

        return attrs


class RuleCreateUpdateSerializer(WorkspaceOwnedSerializer):
    """Serializer for creating and updating rules."""

    workspace = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()

    class Meta(WorkspaceOwnedSerializer.Meta):
        model = models.Rule
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "status",
            "is_default",
            "platform",
            "workspace",
            "workspace_name",
            "created_by",
            "created",
            "last_updated",
        ]

        # Extend parent read_only_fields with slug (auto-generated)
        read_only_fields = WorkspaceOwnedSerializer.Meta.read_only_fields + ['slug']

    def get_workspace(self, obj) -> int:
        return obj.workspace.id

    def get_workspace_name(self, obj) -> Optional[str]:
        return obj.workspace.name if obj.workspace else None


class RuleNestedSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating rules with nested rule details."""

    field_details = serializers.SerializerMethodField()
    name = serializers.CharField()
    platform = serializers.PrimaryKeyRelatedField(
        queryset=models.Platform.objects.all())
    platform_name = serializers.CharField(
        source='platform.name', read_only=True)
    platform_slug = serializers.CharField(
        source='platform.slug', read_only=True)
    rule_details = RuleDetailCreateSerializer(many=True, write_only=True)
    description = serializers.CharField(allow_blank=True, required=False)
    workspace_name = serializers.SerializerMethodField()
    workspace = serializers.IntegerField(
        write_only=True, required=False, allow_null=True)

    def validate_workspace(self, value):
        """Validate workspace field"""
        if value is not None:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                # Check workspace access permissions
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    # Check if user has access to this workspace
                    if not request.user.is_superuser and not request.user.has_workspace_access(value):
                        raise serializers.ValidationError(
                            f"Access denied to workspace {value}")
                    return workspace  # Return workspace object for access later
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
            else:
                # No request context - allow during testing
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    return workspace  # Return workspace object for access later
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
        return value

    def validate_platform(self, value):
        """Validate platform field"""
        try:
            # Handle both formats: direct ID or dict with ID
            platform_id = value.id if hasattr(value, 'id') else value
            platform = models.Platform.objects.get(id=platform_id)
            return platform  # Return platform object for access later
        except models.Platform.DoesNotExist:
            raise serializers.ValidationError(
                f"Platform {value} does not exist")
        except AttributeError:
            raise serializers.ValidationError(
                "Invalid platform format. Expected an ID or a Platform instance.")

    def validate(self, attrs):
        """Validate that all fields in rule_details belong to the same platform."""
        platform = attrs.get('platform')
        rule_details = attrs.get('rule_details', [])

        if platform and rule_details:
            for detail in rule_details:
                field = detail.get('field')
                if field and hasattr(field, 'platform') and field.platform != platform:
                    raise serializers.ValidationError(
                        f"Field '{field.name}' belongs to platform '{field.platform.name}' "
                        f"but the rule is for platform '{platform.name}'. "
                        "All fields must belong to the same platform."
                    )

        return attrs

    class Meta:
        model = models.Rule
        fields = ['id', 'name', 'description', 'status', 'platform',
                  'platform_name', 'platform_slug', 'field_details', 'rule_details',
                  'workspace', 'workspace_name']

    def create(self, validated_data):
        rule_details_data = validated_data.pop('rule_details')
        # This is a Workspace instance from validation
        workspace = validated_data.pop('workspace')

        # Create the Rule instance - explicitly set workspace and platform
        rule = models.Rule.objects.create(
            workspace=workspace,  # Workspace instance is used directly
            **validated_data  # platform is included here since it's already a Platform instance
        )

        # Create RuleDetail instances with the same workspace
        for detail_data in rule_details_data:
            models.RuleDetail.objects.create(
                rule=rule,
                workspace=workspace,
                **detail_data
            )

        return rule

    def update(self, instance, validated_data):
        rule_details_data = validated_data.pop('rule_details', [])
        platform_data = validated_data.pop('platform', None)
        workspace = validated_data.pop('workspace', None)

        # Update rule instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle platform update
        if platform_data:
            platform = platform_data['id'] if isinstance(
                platform_data, dict) else platform_data
            instance.platform = platform

        # Handle workspace update
        if workspace:
            instance.workspace = workspace

        instance.save()

        # Handle rule_details update
        if rule_details_data:
            # Delete existing rule details
            instance.rule_details.all().delete()

            # Create new rule details
            for detail_data in rule_details_data:
                models.RuleDetail.objects.create(
                    rule=instance,
                    workspace=workspace or instance.workspace,
                    **detail_data
                )

        return instance

    def get_field_details(self, obj):
        # Get all rule details for this rule
        rule_details = obj.rule_details.all()

        # Create a dictionary to group by field
        grouped_details = {}

        for detail in rule_details:
            if not detail.field:
                continue

            field = detail.field.id

            if field not in grouped_details:
                # Initialize the field group with field information safely
                next_field_name = None
                if detail.field and detail.field.next_field:
                    next_field_name = detail.field.next_field.name

                grouped_details[field] = {
                    'field': field,
                    'field_name': detail.field.name if detail.field else None,
                    'field_level': detail.field.field_level if detail.field else None,
                    'next_field': next_field_name,
                    'dimensions': []
                }

            # Add dimension information safely
            if not detail.dimension:
                continue

            dimension_info = {
                'id': detail.id,
                'dimension': detail.dimension.id if detail.dimension else None,
                'dimension_name': detail.dimension.name if detail.dimension else None,
                'dimension_type': detail.dimension.type if detail.dimension else None,
                'dimension_order': detail.dimension_order,
                'prefix': detail.prefix or '',  # Convert None to empty string
                'suffix': detail.suffix or '',  # Convert None to empty string
                'delimiter': detail.delimiter or '',  # Convert None to empty string
                'parent_dimension_name': (detail.dimension.parent.name
                                          if detail.dimension and detail.dimension.parent
                                          else None),
                'parent_dimension': (detail.dimension.parent.id
                                     if detail.dimension and detail.dimension.parent
                                     else None),
                'dimension_values': []
            }

            # Safely get dimension values
            if detail.dimension:
                try:
                    dimension_info['dimension_values'] = [
                        {
                            'id': value.id,
                            'value': value.value,
                            'label': value.label,
                            'utm': value.utm,
                        } for value in detail.dimension.dimension_values.all()
                        if value is not None  # Extra safety check
                    ]
                except Exception:
                    # If there's any error getting dimension values, use empty list
                    dimension_info['dimension_values'] = []

            grouped_details[field]['dimensions'].append(dimension_info)

            # combine dimensions to form field_rule safely
            try:
                dimension_names = [
                    (dim.get('prefix', '') or '') +  # Handle None values
                    (dim.get('dimension_name', '') or '') +
                    (dim.get('suffix', '') or '') +
                    (dim.get('delimiter', '') or '')
                    for dim in sorted(
                        grouped_details[field]['dimensions'],
                        # Default to 0 if missing
                        key=lambda x: x.get('dimension_order', 0)
                    )
                ]
                field_rule = ''.join(dimension_names)
                grouped_details[field]['field_rule'] = field_rule
            except Exception:
                # If there's any error forming the field_rule, use empty string
                grouped_details[field]['field_rule'] = ''

        # Convert dictionary to list
        return list(grouped_details.values())

    def get_workspace_name(self, obj):
        if obj.workspace:
            return obj.workspace.name
        return None


# =============================================================================
# READ SERIALIZERS (for displaying/retrieving data)
# =============================================================================

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
        fields = models.Field.objects.filter(id__in=field_ids)
        return [{"id": f.id, "name": f.name, "field_level": f.field_level} for f in fields]

    def get_required_dimensions(self, obj) -> Dict[str, List[str]]:
        """Get required dimensions by field."""
        result = {}
        # Convert to list to avoid multiple evaluations
        field_ids = list(obj.get_fields_with_rules())
        fields = models.Field.objects.filter(id__in=field_ids)
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
        model = models.Rule
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
            field_obj = models.Field.objects.get(id=field.id)
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


# =============================================================================
# REQUEST/RESPONSE SERIALIZERS (for API interactions)
# =============================================================================

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


# =============================================================================
# SPECIALIZED CATALOG SERIALIZERS (from rule_serializers.py)
# =============================================================================

class DimensionDefinitionSerializer(serializers.Serializer):
    """Serializer for individual dimension definitions"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()
    description = serializers.CharField(allow_blank=True)

    # Formatting rules
    prefix = serializers.CharField(allow_blank=True)
    suffix = serializers.CharField(allow_blank=True)
    delimiter = serializers.CharField(allow_blank=True)
    effective_delimiter = serializers.CharField(allow_blank=True)

    # Behavior flags
    is_required = serializers.BooleanField()
    allows_freetext = serializers.BooleanField()
    is_dropdown = serializers.BooleanField()

    # Constraint metadata
    has_parent_constraint = serializers.BooleanField()
    parent_dimension = serializers.IntegerField(allow_null=True)
    parent_dimension_name = serializers.CharField(allow_null=True)

    # Order and positioning
    dimension_order = serializers.IntegerField()
    field_level = serializers.IntegerField()
    field_name = serializers.CharField()

    # Value metadata
    value_count = serializers.IntegerField()
    has_active_values = serializers.BooleanField()


class DimensionValueSerializer(serializers.Serializer):
    """Serializer for dimension values/options with parent-child relationships"""
    id = serializers.IntegerField()
    value = serializers.CharField()
    label = serializers.CharField()
    utm = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    is_active = serializers.BooleanField()
    order = serializers.IntegerField()

    # Parent-child relationship fields
    parent = serializers.DictField(allow_null=True)
    has_parent = serializers.BooleanField()

    # Flattened parent fields for easier access
    parent = serializers.IntegerField(allow_null=True)
    parent_value = serializers.CharField(allow_null=True)
    parent_label = serializers.CharField(allow_null=True)
    parent_dimension = serializers.IntegerField(allow_null=True)
    parent_dimension_name = serializers.CharField(allow_null=True)


class LightweightRuleSerializer(serializers.Serializer):
    """Lightweight rule serializer for list views"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    is_default = serializers.BooleanField()
    platform = serializers.IntegerField()
    platform_name = serializers.CharField()
    platform_slug = serializers.CharField()
    created_by_name = serializers.CharField(allow_null=True)
    created = serializers.CharField()
    last_updated = serializers.CharField()

    # Summary information
    total_fields = serializers.IntegerField()
    fields_with_rules = serializers.ListField(child=serializers.DictField())
    can_generate_count = serializers.IntegerField()
    configuration_errors = serializers.ListField(child=serializers.CharField())


# =============================================================================
# OPTIMIZED CATALOG SERIALIZERS
# =============================================================================

class OptimizedDimensionCatalogSerializer(serializers.Serializer):
    """Centralized dimension catalog with all dimension data"""
    rule = serializers.IntegerField()
    rule_name = serializers.CharField()
    rule_slug = serializers.CharField()

    # All dimension definitions (centralized)
    dimensions = serializers.DictField(
        child=DimensionDefinitionSerializer(),
        help_text="Complete dimension definitions by ID"
    )

    # All dimension values (centralized)
    dimension_values = serializers.DictField(
        child=DimensionValueSerializer(many=True),
        help_text="All dimension values organized by dimension"
    )

    generated_at = serializers.CharField()


class RuleConfigurationSerializer(serializers.Serializer):
    """Serializer that matches the exact structure shown in the redocs documentation"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()

    # Platform object - exactly as shown in redocs
    platform = serializers.DictField(child=serializers.CharField())

    # Workspace object - exactly as shown in redocs
    workspace = serializers.DictField(child=serializers.CharField())

    # Fields as array - exactly as shown in redocs
    fields = serializers.ListField(child=serializers.DictField())

    # Dimensions object keyed by dimension ID - exactly as shown in redocs
    dimensions = serializers.DictField(child=serializers.DictField())

    # Dimension values object keyed by dimension ID - exactly as shown in redocs
    dimension_values = serializers.DictField(
        child=serializers.ListField(child=serializers.DictField()))

    # Metadata - exactly as shown in redocs
    generated_at = serializers.CharField()
    created_by = serializers.DictField(
        child=serializers.CharField(allow_null=True))


# =============================================================================
# API RESPONSE SERIALIZERS
# =============================================================================

class APIVersionResponseSerializer(serializers.Serializer):
    """Serializer for API version responses"""
    version = serializers.CharField()
    message = serializers.CharField()
    features = serializers.ListField(child=serializers.CharField())
    deprecated_features = serializers.ListField(
        child=serializers.CharField(), required=False)
    breaking_changes = serializers.ListField(
        child=serializers.CharField(), required=False)
    debug_info = serializers.DictField(required=False)


class APIHealthResponseSerializer(serializers.Serializer):
    """Serializer for API health check responses"""
    status = serializers.CharField()
    version = serializers.CharField()
    timestamp = serializers.CharField()
    database = serializers.CharField()
    cache = serializers.CharField()
    workspace_detection = serializers.CharField()
    debug_info = serializers.DictField()


class VersionDemoResponseSerializer(serializers.Serializer):
    """Serializer for version demo responses"""
    message = serializers.CharField()
    timestamp = serializers.CharField()
    version = serializers.CharField()
    data = serializers.DictField()
    debug_info = serializers.DictField()
    links = serializers.DictField(required=False)
    metadata = serializers.DictField(required=False)
    performance_metrics = serializers.DictField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses"""
    error = serializers.CharField()
    supported_versions = serializers.ListField(
        child=serializers.CharField(), required=False)
    debug_info = serializers.DictField(required=False)


class CacheInvalidationResponseSerializer(serializers.Serializer):
    """Serializer for cache invalidation responses"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    rule_ids = serializers.ListField(child=serializers.IntegerField())
    workspace = serializers.IntegerField()
    timestamp = serializers.CharField()


class GenerationPreviewRequestSerializer(serializers.Serializer):
    """Serializer for generation preview requests"""
    rule_id = serializers.IntegerField()
    sample_values = serializers.DictField()
    field_id = serializers.IntegerField(required=False)


class GenerationPreviewResponseSerializer(serializers.Serializer):
    """Serializer for generation preview responses"""
    preview = serializers.CharField()
    rule_id = serializers.IntegerField()
    field_id = serializers.IntegerField(required=False)
    sample_values = serializers.DictField()
    generation_time_ms = serializers.FloatField()
    workspace = serializers.IntegerField()


class CacheInvalidationRequestSerializer(serializers.Serializer):
    """Serializer for cache invalidation requests"""
    rule_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of rule IDs to invalidate cache for"
    )


# =============================================================================
# ADDITIONAL CATALOG SERIALIZERS
# =============================================================================

class DimensionReferenceSerializer(serializers.Serializer):
    """Minimal dimension reference for field templates"""
    dimension = serializers.IntegerField()
    dimension_order = serializers.IntegerField()
    is_required = serializers.BooleanField()
    is_inherited = serializers.BooleanField()
    inherits_from_field_level = serializers.IntegerField(allow_null=True)

    # Formatting overrides (only if different from dimension defaults)
    prefix_override = serializers.CharField(allow_blank=True, allow_null=True)
    suffix_override = serializers.CharField(allow_blank=True, allow_null=True)
    delimiter_override = serializers.CharField(
        allow_blank=True, allow_null=True)


class OptimizedFieldTemplateSerializer(serializers.Serializer):
    """Optimized field template with minimal data and ID references"""
    field = serializers.IntegerField()
    field_name = serializers.CharField()
    field_level = serializers.IntegerField()
    next_field = serializers.IntegerField(allow_null=True)
    can_generate = serializers.BooleanField()

    # Dimension references (not full data)
    dimensions = DimensionReferenceSerializer(many=True)
    dimension_count = serializers.IntegerField()
    required_dimension_count = serializers.IntegerField()
    inherited_dimension_count = serializers.IntegerField()

    # Computed metadata
    field_rule_preview = serializers.CharField()
    completeness_score = serializers.FloatField()


class InheritanceLookupSerializer(serializers.Serializer):
    """Serializer for inheritance lookup tables"""
    dimension = serializers.IntegerField(required=False)
    field_level_inherited_from = serializers.IntegerField(required=False)
    inherits_formatting = serializers.BooleanField(required=False)
    inheritance_chain = serializers.ListField(
        child=serializers.IntegerField(), required=False)
    by_dimension = serializers.DictField(required=False)
    by_target_field_level = serializers.DictField(required=False)
    by_source_field_level = serializers.DictField(required=False)
    inherits_from_dimension = serializers.DictField(required=False)
    provides_inheritance_to = serializers.DictField(required=False)
    inherited_dimensions = serializers.ListField(
        child=serializers.IntegerField(), required=False)
    source_dimensions = serializers.ListField(
        child=serializers.IntegerField(), required=False)
    inheritance_stats = serializers.DictField(required=False)


class ConstraintRelationshipSerializer(serializers.Serializer):
    """Optimized constraint relationships"""
    parent_child_constraints = serializers.ListField(
        child=serializers.DictField(),
        help_text="Array of parent-child dimension constraints"
    )
    field_level_constraints = serializers.DictField(
        help_text="Field-level dimension requirements"
    )
    value_constraints = serializers.DictField(
        help_text="Pre-computed value constraint lookups"
    )


class ValidationRuleSerializer(serializers.Serializer):
    """Serializer for field validation rules"""
    type = serializers.CharField()
    message = serializers.CharField()
    dimensions = serializers.ListField(
        child=serializers.CharField(), required=False)
    dimension = serializers.CharField(required=False)
    parent_dimension = serializers.CharField(required=False)


class GenerationMetadataSerializer(serializers.Serializer):
    """Serializer for generation metadata"""
    can_generate = serializers.BooleanField()
    generation_order = serializers.ListField(child=serializers.CharField())
    required_for_generation = serializers.ListField(
        child=serializers.CharField())
    optional_for_generation = serializers.ListField(
        child=serializers.CharField())
    total_possible_combinations = serializers.IntegerField()


class InheritanceInfoSerializer(serializers.Serializer):
    """Serializer for dimension inheritance information"""
    is_inherited = serializers.BooleanField()
    parent_rule_detail = serializers.IntegerField(allow_null=True)
    parent_field_level = serializers.IntegerField(allow_null=True)
    parent_field_name = serializers.CharField(allow_null=True)
    inherits_formatting = serializers.BooleanField()


class FieldDimensionSerializer(serializers.Serializer):
    """Serializer for dimension information within a field template"""
    rule_detail = serializers.IntegerField()
    dimension = serializers.IntegerField()
    dimension_name = serializers.CharField()
    dimension_type = serializers.CharField()
    dimension_description = serializers.CharField(allow_blank=True)
    dimension_order = serializers.IntegerField()
    is_required = serializers.BooleanField()

    # Formatting
    prefix = serializers.CharField(allow_blank=True)
    suffix = serializers.CharField(allow_blank=True)
    delimiter = serializers.CharField(allow_blank=True)
    effective_delimiter = serializers.CharField(allow_blank=True)

    # Parent-child relationships
    parent_dimension = serializers.IntegerField(allow_null=True)
    parent_dimension_name = serializers.CharField(allow_null=True)

    # Inheritance information
    inheritance = InheritanceInfoSerializer()

    # Values
    dimension_values = DimensionValueSerializer(many=True)
    dimension_value_count = serializers.IntegerField()
    active_value_count = serializers.IntegerField()

    # Behavior flags
    allows_freetext = serializers.BooleanField()
    is_dropdown = serializers.BooleanField()
    has_constraints = serializers.BooleanField()


class FieldTemplateSerializer(serializers.Serializer):
    """Serializer for field templates"""
    field = serializers.IntegerField()
    field_name = serializers.CharField()
    field_level = serializers.IntegerField()
    next_field = serializers.IntegerField(allow_null=True)
    next_field_name = serializers.CharField(allow_null=True, allow_blank=True)
    can_generate = serializers.BooleanField()

    # Dimensions
    dimensions = FieldDimensionSerializer(many=True)
    dimension_count = serializers.IntegerField()
    required_dimension_count = serializers.IntegerField()
    inherited_dimension_count = serializers.IntegerField()

    # Preview and metadata
    field_rule_preview = serializers.CharField()
    validation_rules = ValidationRuleSerializer(many=True)
    generation_metadata = GenerationMetadataSerializer()
    completeness_score = serializers.FloatField()


class FieldSpecificDataSerializer(serializers.Serializer):
    """Serializer for field-specific rule data"""
    field_template = FieldTemplateSerializer()
    dimension_inheritance = serializers.DictField()
    field_summary = serializers.DictField()


class DimensionRelationshipMapsSerializer(serializers.Serializer):
    """Serializer for dimension relationship lookup maps"""
    field_to_dimensions = serializers.DictField()
    field_to_required_dimensions = serializers.DictField()
    field_to_optional_dimensions = serializers.DictField()
    dimension_to_fields = serializers.DictField()
    dimension_to_required_fields = serializers.DictField()
    dimension_to_optional_fields = serializers.DictField()
    field_levels = serializers.ListField(child=serializers.IntegerField())
    all_dimensions = serializers.ListField(child=serializers.IntegerField())
    required_dimensions = serializers.ListField(
        child=serializers.IntegerField())
    optional_dimensions = serializers.ListField(
        child=serializers.IntegerField())
    relationship_stats = serializers.DictField()


class ConstraintLookupSerializer(serializers.Serializer):
    """Serializer for constraint lookup tables"""
    parent_child_constraints = serializers.ListField()
    field_level_constraints = serializers.DictField()
    value_constraints = serializers.DictField()
    parent_to_children_map = serializers.DictField()
    child_to_parent_map = serializers.DictField()
    constraint_coverage_map = serializers.DictField()
    validation_lookup = serializers.DictField()
    constraint_stats = serializers.DictField()


class MetadataIndexesSerializer(serializers.Serializer):
    """Serializer for metadata indexes"""
    dimension_type_groups = serializers.DictField()
    formatting_patterns = serializers.DictField()
    delimiter_groups = serializers.DictField()
    prefix_groups = serializers.DictField()
    suffix_groups = serializers.DictField()
    validation_flags = serializers.DictField()
    dimension_to_type = serializers.DictField()
    dimension_to_name = serializers.DictField()
    dimension_name_to_id = serializers.DictField()
    field_level_to_dimensions = serializers.DictField()
    dimension_order_index = serializers.DictField()
    fast_lookups = serializers.DictField()
    metadata_stats = serializers.DictField()


class EnhancedDimensionCatalogSerializer(serializers.Serializer):
    """Enhanced dimension catalog serializer with lookup tables"""
    rule = serializers.IntegerField()
    rule_name = serializers.CharField()
    rule_slug = serializers.CharField()
    dimensions = serializers.DictField()
    dimension_values = serializers.DictField()
    constraints = ConstraintLookupSerializer(required=False)
    inheritance_lookup = InheritanceLookupSerializer(required=False)
    relationship_maps = DimensionRelationshipMapsSerializer(required=False)
    metadata_indexes = MetadataIndexesSerializer(required=False)
    generated_at = serializers.DateTimeField()


class CompleteRuleSerializer(serializers.Serializer):
    """Complete rule serializer with optimized lookup structures"""
    rule = serializers.IntegerField()
    rule_name = serializers.CharField()
    rule_slug = serializers.CharField()

    # Optimized field templates with dimension ID references only
    field_templates = OptimizedFieldTemplateSerializer(many=True)

    # Centralized dimension catalog with lookup tables
    dimension_catalog = EnhancedDimensionCatalogSerializer()

    # Metadata and performance metrics (optional)
    metadata = serializers.DictField(required=False)
    performance_metrics = serializers.DictField(required=False)


class DimensionCatalogSerializer(serializers.Serializer):
    """Complete dimension catalog serializer"""
    rule = serializers.IntegerField()
    rule_name = serializers.CharField()
    rule_slug = serializers.CharField()
    dimensions = serializers.DictField(child=DimensionDefinitionSerializer())
    dimension_values = serializers.DictField(
        child=DimensionValueSerializer(many=True)
    )
    constraint_relationships = ConstraintRelationshipSerializer()
    field_templates = FieldTemplateSerializer(many=True)
    generated_at = serializers.CharField()


class ValidationSummarySerializer(serializers.Serializer):
    """Serializer for rule validation summary"""
    rule = serializers.IntegerField()
    rule_name = serializers.CharField()
    is_valid = serializers.BooleanField()
    validation_issues = serializers.ListField(child=serializers.CharField())
    warnings = serializers.ListField(child=serializers.CharField())
    field_summary = serializers.DictField()
    inheritance_summary = serializers.DictField()
    overall_score = serializers.FloatField()


class PerformanceMetricsSerializer(serializers.Serializer):
    """Serializer for performance metrics"""
    rule = serializers.IntegerField(required=False)
    cache_status = serializers.DictField(required=False)
    services_initialized = serializers.DictField(required=False)
    generation_time_ms = serializers.FloatField(required=False)
    workspace = serializers.IntegerField(required=False)
    timestamp = serializers.CharField(required=False)


class GenerationPreviewSerializer(serializers.Serializer):
    """Serializer for generation preview responses"""
    success = serializers.BooleanField()
    preview = serializers.CharField(allow_null=True)
    missing_required = serializers.ListField(child=serializers.CharField())
    used_dimensions = serializers.ListField(child=serializers.CharField())
    template_used = serializers.CharField()
    error = serializers.CharField(required=False)
