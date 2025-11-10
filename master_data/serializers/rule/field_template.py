"""
Entity template serializers for entity templates and entity-specific data.

This module contains serializers responsible for entity templates,
entity dimensions, and entity-specific rule data.
"""

from rest_framework import serializers
from .dimension_ref import DimensionReferenceSerializer, DimensionValueSerializer
from .metadata import (
    InheritanceInfoSerializer,
    ValidationRuleSerializer,
    GenerationMetadataSerializer
)


class OptimizedEntityTemplateSerializer(serializers.Serializer):
    """Optimized entity template with minimal data and ID references"""
    entity = serializers.IntegerField()
    entity_name = serializers.CharField()
    entity_level = serializers.IntegerField()
    next_entity = serializers.IntegerField(allow_null=True)
    can_generate = serializers.BooleanField()

    # Dimension references (not full data)
    dimensions = DimensionReferenceSerializer(many=True)
    dimension_count = serializers.IntegerField()
    required_dimension_count = serializers.IntegerField()
    inherited_dimension_count = serializers.IntegerField()

    # Computed metadata
    entity_rule_preview = serializers.CharField()
    completeness_score = serializers.FloatField()


class EntityDimensionSerializer(serializers.Serializer):
    """Serializer for dimension information within an entity template"""
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


class EntityTemplateSerializer(serializers.Serializer):
    """Serializer for entity templates"""
    entity = serializers.IntegerField()
    entity_name = serializers.CharField()
    entity_level = serializers.IntegerField()
    next_entity = serializers.IntegerField(allow_null=True)
    next_entity_name = serializers.CharField(allow_null=True, allow_blank=True)
    can_generate = serializers.BooleanField()

    # Dimensions
    dimensions = EntityDimensionSerializer(many=True)
    dimension_count = serializers.IntegerField()
    required_dimension_count = serializers.IntegerField()
    inherited_dimension_count = serializers.IntegerField()

    # Preview and metadata
    entity_rule_preview = serializers.CharField()
    validation_rules = ValidationRuleSerializer(many=True)
    generation_metadata = GenerationMetadataSerializer()
    completeness_score = serializers.FloatField()


class EntitySpecificDataSerializer(serializers.Serializer):
    """Serializer for entity-specific rule data"""
    entity_template = EntityTemplateSerializer()
    dimension_inheritance = serializers.DictField()
    entity_summary = serializers.DictField()
