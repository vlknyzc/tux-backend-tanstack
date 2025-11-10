"""
Business logic services for string generation.
Handles string generation, validation, and naming conventions.
"""

import uuid
from typing import Dict, List, Optional, Tuple
from django.core.exceptions import ValidationError
from django.db import transaction
from ..models import String, StringDetail, Rule, RuleDetail, DimensionValue


class NamingConventionError(Exception):
    """Custom exception for naming convention errors."""
    pass


class StringGenerationService:
    """
    Service class for generating strings based on naming rules.

    Handles the core business logic of combining dimension values
    according to rule configurations to create standardized naming strings.
    """

    @staticmethod
    def generate_string_value(rule: Rule, entity, dimension_values: Dict[str, str]) -> str:
        """
        Generate a string value based on rule configuration and dimension values.

        Args:
            rule: The naming rule to apply
            entity: The entity this string belongs to
            dimension_values: Dict mapping dimension names to their values

        Returns:
            Generated string value

        Raises:
            NamingConventionError: If generation fails due to missing values or invalid config
        """
        try:
            # Get rule details for this entity, ordered by dimension_order
            rule_details = RuleDetail.objects.filter(
                rule=rule,
                entity=entity
            ).select_related('dimension').order_by('dimension_order')

            if not rule_details.exists():
                raise NamingConventionError(
                    f"No rule details found for rule '{rule.name}' and entity '{entity.name}'"
                )

            # Validate dimension order sequence to ensure data integrity
            orders = [detail.dimension_order for detail in rule_details]
            expected_orders = list(range(1, len(orders) + 1))
            if sorted(orders) != expected_orders:
                raise NamingConventionError(
                    f"Invalid dimension order sequence for rule '{rule.name}' entity '{entity.name}': "
                    f"expected {expected_orders}, got {sorted(orders)}"
                )

            parts = []

            for detail in rule_details:
                dimension_name = detail.dimension.name

                # Get the value for this dimension
                if dimension_name not in dimension_values:
                    raise NamingConventionError(
                        f"Missing value for required dimension '{dimension_name}'"
                    )

                value = dimension_values[dimension_name]

                # Apply prefix and suffix
                formatted_value = StringGenerationService._format_dimension_value(
                    value, detail.prefix, detail.suffix
                )

                parts.append(formatted_value)

                # Add delimiter if it exists (including for the last part)
                if detail.delimiter:
                    parts.append(detail.delimiter)

            # Join all parts (values + delimiters)
            return ''.join(parts)

        except Exception as e:
            raise NamingConventionError(f"String generation failed: {str(e)}")

    @staticmethod
    def _format_dimension_value(value: str, prefix: Optional[str], suffix: Optional[str]) -> str:
        """Format a dimension value with optional prefix and suffix."""
        formatted = value
        if prefix:
            formatted = f"{prefix}{formatted}"
        if suffix:
            formatted = f"{formatted}{suffix}"
        return formatted

    @staticmethod
    def validate_dimension_values(rule: Rule, entity, dimension_values: Dict[str, str]) -> List[str]:
        """
        Validate that all required dimension values are provided and valid.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Get required dimensions for this rule and entity
        required_dimensions = RuleDetail.objects.filter(
            rule=rule, entity=entity
        ).values_list('dimension__name', flat=True)

        # Check for missing dimensions
        for dimension_name in required_dimensions:
            if dimension_name not in dimension_values:
                errors.append(f"Missing required dimension: {dimension_name}")
                continue

            value = dimension_values[dimension_name]
            if not value or not value.strip():
                errors.append(f"Empty value for dimension: {dimension_name}")

        # Validate dimension values exist in the system
        for dimension_name, value in dimension_values.items():
            if not StringGenerationService._is_valid_dimension_value(dimension_name, value):
                errors.append(
                    f"Invalid value '{value}' for dimension '{dimension_name}'")

        return errors

    @staticmethod
    def _is_valid_dimension_value(dimension_name: str, value: str) -> bool:
        """Check if a dimension value is valid (exists in DimensionValue table)."""
        from ..models import Dimension, DimensionValue

        try:
            dimension = Dimension.objects.get(name=dimension_name)

            # For LIST type dimensions, check if value exists
            if dimension.type == 'list':
                return DimensionValue.objects.filter(
                    dimension=dimension,
                    value=value
                ).exists()

            # For FREE_TEXT type, any non-empty value is valid
            return bool(value and value.strip())

        except Dimension.DoesNotExist:
            return False

    @staticmethod
    def check_naming_conflicts(rule: Rule, entity, proposed_value: str, exclude_string: Optional[int] = None) -> List[str]:
        """
        Check for naming conflicts with existing strings.

        Returns:
            List of conflict descriptions (empty if no conflicts)
        """
        conflicts = []

        # Check for exact duplicates
        existing_query = String.objects.filter(
            rule=rule,
            entity=entity,
            value=proposed_value
        )

        if exclude_string:
            existing_query = existing_query.exclude(id=exclude_string.id)

        if existing_query.exists():
            conflicts.append(
                f"String value '{proposed_value}' already exists for this rule and entity")

        # Check for similar strings (optional - for warnings)
        similar_strings = String.objects.filter(
            rule=rule,
            entity=entity,
            value__icontains=proposed_value[:10]  # Check first 10 chars
        )

        if exclude_string:
            similar_strings = similar_strings.exclude(id=exclude_string.id)

        if similar_strings.exists():
            # Limit to 3 examples
            similar_values = [s.value for s in similar_strings[:3]]
            conflicts.append(
                f"Similar strings exist: {', '.join(similar_values)}")

        return conflicts

    @staticmethod
    @transaction.atomic
    def create_string_with_details(submission, entity, dimension_values: Dict[str, str]) -> String:
        """
        Create a new String with auto-generated value and associated StringDetails.

        DEPRECATED: The 'submission' parameter is deprecated. Use Projects instead.
        This method is kept for backward compatibility with existing code.

        Args:
            submission: [DEPRECATED] Submission instance (use Projects instead)
            entity: Entity instance
            dimension_values: Dict of dimension values

        Returns:
            Created String instance
        """
        rule = submission.rule

        # Validate dimension values
        validation_errors = StringGenerationService.validate_dimension_values(
            rule, entity, dimension_values
        )
        if validation_errors:
            raise ValidationError(validation_errors)

        # Generate string value
        generated_value = StringGenerationService.generate_string_value(
            rule, entity, dimension_values
        )

        # Check for conflicts
        conflicts = StringGenerationService.check_naming_conflicts(
            rule, entity, generated_value
        )
        if any('already exists' in conflict for conflict in conflicts):
            raise NamingConventionError(conflicts[0])

        # Create the String (submission is optional now)
        string = String.objects.create(
            submission=submission,  # Legacy support
            entity=entity,
            rule=rule,
            value=generated_value,
            string_uuid=uuid.uuid4()
        )

        # Create StringDetails for each dimension
        for dimension_name, value in dimension_values.items():
            dimension = rule.rule_details.filter(
                entity=entity,
                dimension__name=dimension_name
            ).first().dimension

            # Get DimensionValue if it's a list type
            dimension_value = None
            dimension_value_freetext = None

            if dimension.type == 'list':
                dimension_value = DimensionValue.objects.filter(
                    dimension=dimension,
                    value=value
                ).first()
            else:
                dimension_value_freetext = value

            StringDetail.objects.create(
                string=string,
                dimension=dimension,
                dimension_value=dimension_value,
                dimension_value_freetext=dimension_value_freetext
            )

        return string
