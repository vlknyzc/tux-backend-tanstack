"""
Validation serializers for Rule validation and configuration checking.

This module contains serializers responsible for validating rules
and providing detailed validation feedback.
"""

from rest_framework import serializers
from typing import Optional, List, Dict
from ...models import Rule, Field


class RuleValidationSerializer(serializers.ModelSerializer):
    """Serializer for rule validation results."""
    configuration_errors = serializers.SerializerMethodField()
    can_generate_for_fields = serializers.SerializerMethodField()
    required_dimensions_by_field = serializers.SerializerMethodField()
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
            "can_generate_for_fields",
            "required_dimensions_by_field",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_configuration_errors(self, obj) -> List[str]:
        """Get detailed configuration validation errors."""
        return obj.validate_configuration()

    def get_can_generate_for_fields(self, obj) -> Dict[str, bool]:
        """Get fields this rule can generate strings for."""
        fields = Field.objects.filter(platform=obj.platform)
        result = {}
        for field in fields:
            result[field.name] = obj.can_generate_for_field(field)
        return result

    def get_required_dimensions_by_field(self, obj) -> Dict[str, Dict[str, List[str]]]:
        """Get required dimensions organized by field."""
        result = {}
        fields = Field.objects.filter(platform=obj.platform)
        for field in fields:
            if obj.can_generate_for_field(field):
                result[field.name] = {
                    "dimensions": list(obj.get_required_dimensions(field)),
                    "generation_order": obj.get_generation_order(field)
                }
        return result

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None
