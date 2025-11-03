"""
Dimension reference serializers for dimension definitions and values.

This module contains serializers responsible for dimension
definitions, dimension values, and dimension references.
"""

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
