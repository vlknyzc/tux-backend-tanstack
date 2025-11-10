"""
Validation serializers for Rule validation and configuration checking.

This module contains serializers responsible for validating rules
and providing detailed validation feedback.
"""

from rest_framework import serializers
from typing import Optional, List, Dict
from ...models import Rule, Entity


class RuleValidationSerializer(serializers.ModelSerializer):
    """Serializer for rule validation results."""
    configuration_errors = serializers.SerializerMethodField()
    can_generate_for_entities = serializers.SerializerMethodField()
    required_dimensions_by_entity = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Rule
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "status",
            "is_default",
            "platform",
            "configuration_errors",
            "can_generate_for_entities",
            "required_dimensions_by_entity",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_configuration_errors(self, obj) -> List[str]:
        """Get detailed configuration validation errors."""
        return obj.validate_configuration()

    def get_can_generate_for_entities(self, obj) -> Dict[str, bool]:
        """Get entities this rule can generate strings for."""
        entities = Entity.objects.filter(platform=obj.platform)
        result = {}
        for entity in entities:
            result[entity.name] = obj.can_generate_for_entity(entity)
        return result

    def get_required_dimensions_by_entity(self, obj) -> Dict[str, Dict[str, List[str]]]:
        """Get required dimensions organized by entity."""
        result = {}
        entities = Entity.objects.filter(platform=obj.platform)
        for entity in entities:
            if obj.can_generate_for_entity(entity):
                result[entity.name] = {
                    "dimensions": list(obj.get_required_dimensions(entity)),
                    "generation_order": obj.get_generation_order(entity)
                }
        return result

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None
