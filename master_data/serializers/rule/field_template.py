"""
Field template serializers for field templates and field-specific data.

This module contains serializers responsible for field templates,
field dimensions, and field-specific rule data.
"""

from rest_framework import serializers
from .dimension_ref import DimensionReferenceSerializer, DimensionValueSerializer
from .metadata import (
    InheritanceInfoSerializer,
    ValidationRuleSerializer,
    GenerationMetadataSerializer
)


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
