"""
Request serializers for API request data validation.

This module contains serializers responsible for validating
incoming API requests related to rules.
"""

from rest_framework import serializers
from ...models import Field, Rule


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
            Field.objects.get(id=value)
        except Field.DoesNotExist:
            raise serializers.ValidationError("Field does not exist")
        return value


class DefaultRuleRequestSerializer(serializers.Serializer):
    """Serializer for setting default rule."""
    rule = serializers.IntegerField()

    def validate_rule(self, value):
        """Validate that rule exists."""
        try:
            Rule.objects.get(id=value)
        except Rule.DoesNotExist:
            raise serializers.ValidationError("Rule does not exist")
        return value


class GenerationPreviewRequestSerializer(serializers.Serializer):
    """Serializer for generation preview requests."""
    rule_id = serializers.IntegerField()
    sample_values = serializers.DictField()
    field_id = serializers.IntegerField(required=False)


class CacheInvalidationRequestSerializer(serializers.Serializer):
    """Serializer for cache invalidation requests."""
    rule_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of rule IDs to invalidate cache for"
    )
