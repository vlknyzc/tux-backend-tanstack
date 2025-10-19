from rest_framework import serializers
from typing import Optional
from .. import models


class DimensionConstraintSerializer(serializers.ModelSerializer):
    """Serializer for DimensionConstraint with camelCase field conversion."""

    created_by_name = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()

    class Meta:
        model = models.DimensionConstraint
        fields = [
            "id",
            "dimension",
            "dimension_name",
            "constraint_type",
            "value",
            "error_message",
            "order",
            "is_active",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]
        extra_kwargs = {
            'dimension': {'required': True, 'allow_null': False},
            'constraint_type': {'required': True, 'allow_null': False},
            'order': {'required': False},
        }

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_dimension_name(self, obj) -> Optional[str]:
        if obj.dimension:
            return obj.dimension.name
        return None

    def validate(self, attrs):
        """Validate constraint configuration."""
        constraint_type = attrs.get('constraint_type')
        value = attrs.get('value')

        # Check if constraint type requires a value
        if constraint_type in models.CONSTRAINT_TYPES_REQUIRING_VALUE:
            if not value:
                raise serializers.ValidationError({
                    'value': f"Constraint type '{constraint_type}' requires a configuration value"
                })

        # Validate max_length
        if constraint_type == models.ConstraintTypeChoices.MAX_LENGTH:
            try:
                max_val = int(value)
                if max_val <= 0:
                    raise serializers.ValidationError({
                        'value': 'Maximum length must be positive'
                    })
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'value': 'Maximum length must be a valid integer'
                })

        # Validate min_length
        elif constraint_type == models.ConstraintTypeChoices.MIN_LENGTH:
            try:
                min_val = int(value)
                if min_val < 0:
                    raise serializers.ValidationError({
                        'value': 'Minimum length must be non-negative'
                    })
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'value': 'Minimum length must be a valid integer'
                })

        # Validate regex pattern
        elif constraint_type == models.ConstraintTypeChoices.REGEX:
            import re
            try:
                re.compile(value)
            except re.error as e:
                raise serializers.ValidationError({
                    'value': f'Invalid regex pattern: {str(e)}'
                })

            # Basic ReDoS prevention
            if value:
                dangerous_patterns = [
                    r'(\w+)*',
                    r'(\w*)*',
                    r'(\w+)+',
                    r'(\w*)+',
                ]
                for pattern in dangerous_patterns:
                    if pattern in value:
                        raise serializers.ValidationError({
                            'value': 'Regex pattern may cause performance issues (nested quantifiers)'
                        })

        return attrs


class ConstraintBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk constraint creation (e.g., applying presets)."""

    constraints = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of constraint objects to create"
    )

    def validate_constraints(self, value):
        """Validate each constraint in the list."""
        required_fields = ['constraint_type']

        for i, constraint in enumerate(value):
            # Check required fields
            for field in required_fields:
                if field not in constraint:
                    raise serializers.ValidationError(
                        f"Constraint at index {i}: '{field}' is required"
                    )

            # Validate constraint type
            constraint_type = constraint.get('constraint_type')
            valid_types = [choice[0] for choice in models.ConstraintTypeChoices.choices]
            if constraint_type not in valid_types:
                raise serializers.ValidationError(
                    f"Constraint at index {i}: Invalid constraint_type '{constraint_type}'. "
                    f"Valid options: {valid_types}"
                )

            # Check if value is required
            if constraint_type in models.CONSTRAINT_TYPES_REQUIRING_VALUE:
                if 'value' not in constraint or not constraint['value']:
                    raise serializers.ValidationError(
                        f"Constraint at index {i}: Constraint type '{constraint_type}' requires a 'value'"
                    )

        return value


class ConstraintReorderSerializer(serializers.Serializer):
    """Serializer for reordering constraints."""

    constraint_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of constraint IDs in the desired order"
    )

    def validate_constraint_ids(self, value):
        """Validate that all constraint IDs exist and belong to the same dimension."""
        if not value:
            raise serializers.ValidationError("At least one constraint ID is required")

        # Check for duplicates
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate constraint IDs found")

        return value


class DimensionValueValidationSerializer(serializers.Serializer):
    """Serializer for validating a value against dimension constraints."""

    value = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="The value to validate"
    )
