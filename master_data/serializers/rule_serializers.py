from rest_framework import serializers


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


class OptimizedDimensionDefinitionSerializer(serializers.Serializer):
    """Simplified dimension definition serializer for optimized catalog"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()
    description = serializers.CharField(allow_blank=True)

    # Default formatting rules
    default_prefix = serializers.CharField(allow_blank=True)
    default_suffix = serializers.CharField(allow_blank=True)
    default_delimiter = serializers.CharField(allow_blank=True)

    # Behavior flags
    allows_freetext = serializers.BooleanField()
    is_dropdown = serializers.BooleanField()

    # Constraint metadata
    has_parent_constraint = serializers.BooleanField()
    parent_dimension = serializers.IntegerField(allow_null=True)
    parent_dimension_name = serializers.CharField(
        allow_null=True, allow_blank=True)

    # Value metadata
    value_count = serializers.IntegerField()
    has_active_values = serializers.BooleanField()


class OptimizedDimensionCatalogSerializer(serializers.Serializer):
    """Centralized dimension catalog with all dimension data"""
    rule = serializers.IntegerField()
    rule_name = serializers.CharField()
    rule_slug = serializers.CharField()

    # All dimension definitions (centralized)
    dimensions = serializers.DictField(
        child=OptimizedDimensionDefinitionSerializer(),
        help_text="Complete dimension definitions by ID"
    )

    # All dimension values (centralized)
    dimension_values = serializers.DictField(
        child=DimensionValueSerializer(many=True),
        help_text="All dimension values organized by dimension"
    )

    # Constraint relationships
    constraints = ConstraintRelationshipSerializer()

    # Inheritance lookup table
    inheritance_lookup = serializers.DictField(
        child=InheritanceLookupSerializer(),
        help_text="Inheritance rules by dimension"
    )

    generated_at = serializers.CharField()


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


class CatalogDimensionSerializer(serializers.Serializer):
    """Simplified dimension serializer for catalog field templates"""
    dimension = serializers.IntegerField()
    dimension_name = serializers.CharField()
    dimension_type = serializers.CharField()
    dimension_order = serializers.IntegerField()
    is_required = serializers.BooleanField()
    prefix = serializers.CharField(allow_blank=True)
    suffix = serializers.CharField(allow_blank=True)
    delimiter = serializers.CharField(allow_blank=True)
    effective_delimiter = serializers.CharField(allow_blank=True)


class CatalogFieldTemplateSerializer(serializers.Serializer):
    """Simplified field template serializer for dimension catalog"""
    field = serializers.IntegerField()
    field_name = serializers.CharField()
    field_level = serializers.IntegerField()
    next_field = serializers.IntegerField(allow_null=True)
    next_field_name = serializers.CharField(allow_null=True, allow_blank=True)
    dimensions = CatalogDimensionSerializer(many=True)
    dimension_count = serializers.IntegerField()
    required_dimension_count = serializers.IntegerField()
    field_rule_preview = serializers.CharField()


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
    field_templates = CatalogFieldTemplateSerializer(many=True)
    generated_at = serializers.CharField()


class MetadataSerializer(serializers.Serializer):
    """Serializer for rule metadata"""
    generated_at = serializers.CharField()
    total_fields = serializers.IntegerField()
    total_dimensions = serializers.IntegerField()
    inheritance_coverage = serializers.FloatField()
    cache_status = serializers.CharField(required=False)


class GenerationPreviewSerializer(serializers.Serializer):
    """Serializer for generation preview responses"""
    success = serializers.BooleanField()
    preview = serializers.CharField(allow_null=True)
    missing_required = serializers.ListField(child=serializers.CharField())
    used_dimensions = serializers.ListField(child=serializers.CharField())
    template_used = serializers.CharField()
    error = serializers.CharField(required=False)


class FieldSummarySerializer(serializers.Serializer):
    """Serializer for field summary information"""
    can_generate = serializers.BooleanField()
    completeness_score = serializers.FloatField()
    total_dimensions = serializers.IntegerField()
    inherited_dimensions = serializers.IntegerField()


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


class FieldSpecificDataSerializer(serializers.Serializer):
    """Serializer for field-specific rule data"""
    field_template = FieldTemplateSerializer()
    dimension_inheritance = serializers.DictField()
    field_summary = FieldSummarySerializer()


# Request serializers for input validation
class GenerationPreviewRequestSerializer(serializers.Serializer):
    """Serializer for generation preview requests"""
    rule = serializers.IntegerField()
    field = serializers.IntegerField()
    sample_values = serializers.DictField(
        child=serializers.CharField(),
        help_text="Sample dimension values for preview generation"
    )


class CacheInvalidationRequestSerializer(serializers.Serializer):
    """Serializer for cache invalidation requests"""
    rule_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of rule IDs to invalidate cache for"
    )


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
    metadata = MetadataSerializer(required=False)
    performance_metrics = PerformanceMetricsSerializer(required=False)


class RuleConfigurationSerializer(serializers.Serializer):
    """Serializer that matches the structure of rule_configuration.json"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()

    # Platform object
    platform = serializers.DictField()

    # Workspace object
    workspace = serializers.DictField()

    # Fields as array instead of object
    fields = serializers.ListField()

    # Dimensions object keyed by dimension ID
    dimensions = serializers.DictField()

    # Dimension values object keyed by dimension ID
    dimension_values = serializers.DictField()

    # Metadata
    generated_at = serializers.CharField()
    created_by = serializers.DictField()
