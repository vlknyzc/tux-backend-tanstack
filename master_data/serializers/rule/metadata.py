"""
Metadata serializers for inheritance, constraints, validation, and performance metrics.

This module contains serializers responsible for metadata about rules,
including inheritance lookups, constraint relationships, validation rules,
generation metadata, and performance metrics.
"""

from rest_framework import serializers


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
