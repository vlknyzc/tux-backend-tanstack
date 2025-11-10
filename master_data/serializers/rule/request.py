"""
Request serializers for API request data validation.

This module contains serializers responsible for validating
incoming API requests related to rules.
"""

from rest_framework import serializers
from ...models import Entity, Rule


class RulePreviewRequestSerializer(serializers.Serializer):
    """Serializer for rule preview requests."""
    entity = serializers.IntegerField()
    sample_values = serializers.DictField(
        child=serializers.CharField(),
        help_text="Sample dimension values for preview generation"
    )

    def validate_entity(self, value):
        """Validate that entity exists."""
        try:
            Entity.objects.get(id=value)
        except Entity.DoesNotExist:
            raise serializers.ValidationError("Entity does not exist")
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
    entity_id = serializers.IntegerField(required=False)


class CacheInvalidationRequestSerializer(serializers.Serializer):
    """Serializer for cache invalidation requests."""
    rule_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of rule IDs to invalidate cache for"
    )
