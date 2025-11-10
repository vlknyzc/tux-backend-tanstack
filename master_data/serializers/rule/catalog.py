"""
Catalog serializers for rule configuration and dimension catalogs.

This module contains serializers responsible for formatting
rule catalog data, configuration data, and lightweight rule representations.
"""

from rest_framework import serializers
from .dimension_ref import DimensionDefinitionSerializer, DimensionValueSerializer
from .field_template import OptimizedEntityTemplateSerializer, EntityTemplateSerializer
from .metadata import (
    ConstraintRelationshipSerializer,
    ConstraintLookupSerializer,
    InheritanceLookupSerializer,
    MetadataIndexesSerializer
)


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
    total_entities = serializers.IntegerField()
    entities_with_rules = serializers.ListField(child=serializers.DictField())
    can_generate_count = serializers.IntegerField()
    configuration_errors = serializers.ListField(child=serializers.CharField())


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

    # Entities as array - exactly as shown in redocs
    entities = serializers.ListField(child=serializers.DictField())

    # Dimensions object keyed by dimension ID - exactly as shown in redocs
    dimensions = serializers.DictField(child=serializers.DictField())

    # Dimension values object keyed by dimension ID - exactly as shown in redocs
    dimension_values = serializers.DictField(
        child=serializers.ListField(child=serializers.DictField()))

    # Metadata - exactly as shown in redocs
    generated_at = serializers.CharField()
    created_by = serializers.DictField(
        child=serializers.CharField(allow_null=True))


class DimensionRelationshipMapsSerializer(serializers.Serializer):
    """Serializer for dimension relationship lookup maps"""
    entity_to_dimensions = serializers.DictField()
    entity_to_required_dimensions = serializers.DictField()
    entity_to_optional_dimensions = serializers.DictField()
    dimension_to_entities = serializers.DictField()
    dimension_to_required_entities = serializers.DictField()
    dimension_to_optional_entities = serializers.DictField()
    entity_levels = serializers.ListField(child=serializers.IntegerField())
    all_dimensions = serializers.ListField(child=serializers.IntegerField())
    required_dimensions = serializers.ListField(
        child=serializers.IntegerField())
    optional_dimensions = serializers.ListField(
        child=serializers.IntegerField())
    relationship_stats = serializers.DictField()


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

    # Optimized entity templates with dimension ID references only
    entity_templates = OptimizedEntityTemplateSerializer(many=True)

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
    entity_templates = EntityTemplateSerializer(many=True)
    generated_at = serializers.CharField()
