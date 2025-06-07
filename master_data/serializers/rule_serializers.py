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
    parent_dimension_id = serializers.IntegerField(allow_null=True)
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
    parent_id = serializers.IntegerField(allow_null=True)
    parent_value = serializers.CharField(allow_null=True)
    parent_label = serializers.CharField(allow_null=True)
    parent_dimension_id = serializers.IntegerField(allow_null=True)
    parent_dimension_name = serializers.CharField(allow_null=True)


class DimensionReferenceSerializer(serializers.Serializer):
    """Minimal dimension reference for field templates"""
    dimension_id = serializers.IntegerField()
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
    field_id = serializers.IntegerField()
    field_name = serializers.CharField()
    field_level = serializers.IntegerField()
    next_field_id = serializers.IntegerField(allow_null=True)
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
    """Simplified inheritance lookup table"""
    dimension_id = serializers.IntegerField()
    field_level_inherited_from = serializers.IntegerField(allow_null=True)
    inherits_formatting = serializers.BooleanField()
    inheritance_chain = serializers.ListField(child=serializers.IntegerField())


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
    parent_dimension_id = serializers.IntegerField(allow_null=True)
    parent_dimension_name = serializers.CharField(
        allow_null=True, allow_blank=True)

    # Value metadata
    value_count = serializers.IntegerField()
    has_active_values = serializers.BooleanField()


class OptimizedDimensionCatalogSerializer(serializers.Serializer):
    """Centralized dimension catalog with all dimension data"""
    rule_id = serializers.IntegerField()
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
        help_text="All dimension values organized by dimension_id"
    )

    # Constraint relationships
    constraints = ConstraintRelationshipSerializer()

    # Inheritance lookup table
    inheritance_lookup = serializers.DictField(
        child=InheritanceLookupSerializer(),
        help_text="Inheritance rules by dimension_id"
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
    parent_rule_detail_id = serializers.IntegerField(allow_null=True)
    parent_field_level = serializers.IntegerField(allow_null=True)
    parent_field_name = serializers.CharField(allow_null=True)
    inherits_formatting = serializers.BooleanField()


class FieldDimensionSerializer(serializers.Serializer):
    """Serializer for dimension information within a field template"""
    rule_detail_id = serializers.IntegerField()
    dimension_id = serializers.IntegerField()
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
    parent_dimension_id = serializers.IntegerField(allow_null=True)
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
    field_id = serializers.IntegerField()
    field_name = serializers.CharField()
    field_level = serializers.IntegerField()
    next_field_id = serializers.IntegerField(allow_null=True)
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
    dimension_id = serializers.IntegerField()
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
    field_id = serializers.IntegerField()
    field_name = serializers.CharField()
    field_level = serializers.IntegerField()
    next_field_id = serializers.IntegerField(allow_null=True)
    next_field_name = serializers.CharField(allow_null=True, allow_blank=True)
    dimensions = CatalogDimensionSerializer(many=True)
    dimension_count = serializers.IntegerField()
    required_dimension_count = serializers.IntegerField()
    field_rule_preview = serializers.CharField()


class DimensionCatalogSerializer(serializers.Serializer):
    """Complete dimension catalog serializer"""
    rule_id = serializers.IntegerField()
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
    cache_status = serializers.CharField()


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
    rule_id = serializers.IntegerField()
    rule_name = serializers.CharField()
    is_valid = serializers.BooleanField()
    validation_issues = serializers.ListField(child=serializers.CharField())
    warnings = serializers.ListField(child=serializers.CharField())
    field_summary = serializers.DictField()
    inheritance_summary = serializers.DictField()
    overall_score = serializers.FloatField()


class PerformanceMetricsSerializer(serializers.Serializer):
    """Serializer for performance metrics"""
    rule_id = serializers.IntegerField()
    cache_status = serializers.DictField()
    services_initialized = serializers.DictField()


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
    rule_id = serializers.IntegerField()
    field_id = serializers.IntegerField()
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


class InheritanceLookupSerializer(serializers.Serializer):
    """Serializer for inheritance lookup tables"""
    by_dimension_id = serializers.DictField()
    by_target_field_level = serializers.DictField()
    by_source_field_level = serializers.DictField()
    inherits_from_dimension = serializers.DictField()
    provides_inheritance_to = serializers.DictField()
    inherited_dimensions = serializers.ListField(
        child=serializers.IntegerField())
    source_dimensions = serializers.ListField(child=serializers.IntegerField())
    inheritance_stats = serializers.DictField()


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
    dimension_id_to_type = serializers.DictField()
    dimension_id_to_name = serializers.DictField()
    dimension_name_to_id = serializers.DictField()
    field_level_to_dimensions = serializers.DictField()
    dimension_order_index = serializers.DictField()
    fast_lookups = serializers.DictField()
    metadata_stats = serializers.DictField()


class EnhancedDimensionCatalogSerializer(serializers.Serializer):
    """Enhanced dimension catalog serializer with lookup tables"""
    rule_id = serializers.IntegerField()
    rule_name = serializers.CharField()
    rule_slug = serializers.CharField()
    dimensions = serializers.DictField()
    dimension_values = serializers.DictField()
    constraints = ConstraintLookupSerializer()
    inheritance_lookup = InheritanceLookupSerializer()
    relationship_maps = DimensionRelationshipMapsSerializer()
    metadata_indexes = MetadataIndexesSerializer()
    generated_at = serializers.DateTimeField()


class PerformanceMetricsSerializer(serializers.Serializer):
    """Serializer for performance metrics of fast lookups"""
    total_dimensions = serializers.IntegerField()
    total_field_levels = serializers.IntegerField()
    lookup_tables_count = serializers.IntegerField()
    index_structures_count = serializers.IntegerField()
    inheritance_coverage_percent = serializers.FloatField()
    constraint_coverage_percent = serializers.FloatField()
    avg_dimensions_per_field = serializers.FloatField()
    optimization_score = serializers.FloatField()
    cache_efficiency = serializers.DictField()


class CompleteRuleSerializer(serializers.Serializer):
    """Complete rule serializer with optimized lookup structures"""
    rule_id = serializers.IntegerField()
    rule_name = serializers.CharField()
    rule_slug = serializers.CharField()

    # Optimized field templates with dimension ID references only
    field_templates = OptimizedFieldTemplateSerializer(many=True)

    # Centralized dimension catalog with lookup tables
    dimension_catalog = EnhancedDimensionCatalogSerializer()

    # Metadata and performance metrics
    metadata = MetadataSerializer()
    performance_metrics = PerformanceMetricsSerializer()
