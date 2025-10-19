"""
Constraint validation service for dimension values.

This service handles validation of dimension values against defined constraints.
"""

import re
from typing import List, Dict, Any, Optional
from django.core.cache import cache

from ..models import DimensionConstraint, ConstraintTypeChoices


class ValidationResult:
    """Result of a constraint validation."""

    def __init__(self, is_valid: bool, error_message: Optional[str] = None, constraint_type: Optional[str] = None):
        self.is_valid = is_valid
        self.error_message = error_message
        self.constraint_type = constraint_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'constraint_type': self.constraint_type,
            'error_message': self.error_message
        }


class ConstraintValidatorService:
    """Service for validating values against dimension constraints."""

    @staticmethod
    def validate_constraint(value: str, constraint: DimensionConstraint) -> ValidationResult:
        """
        Validate a value against a single constraint.

        Args:
            value: The value to validate
            constraint: The constraint to validate against

        Returns:
            ValidationResult indicating if the value is valid
        """
        constraint_type = constraint.constraint_type
        config_value = constraint.value

        is_valid = True

        if constraint_type == ConstraintTypeChoices.NO_SPACES:
            # Check for any whitespace characters
            is_valid = ' ' not in value and '\t' not in value and '\n' not in value and '\r' not in value

        elif constraint_type == ConstraintTypeChoices.LOWERCASE:
            # Must be lowercase and contain at least one letter
            is_valid = value.islower() and any(c.isalpha() for c in value)

        elif constraint_type == ConstraintTypeChoices.UPPERCASE:
            # Must be uppercase and contain at least one letter
            is_valid = value.isupper() and any(c.isalpha() for c in value)

        elif constraint_type == ConstraintTypeChoices.NO_SPECIAL_CHARS:
            # Only alphanumeric and underscore allowed
            is_valid = all(c.isalnum() or c == '_' for c in value)

        elif constraint_type == ConstraintTypeChoices.ALPHANUMERIC:
            # Only letters and numbers
            is_valid = value.isalnum() and len(value) > 0

        elif constraint_type == ConstraintTypeChoices.NUMERIC:
            # Only digits
            is_valid = value.isdigit() and len(value) > 0

        elif constraint_type == ConstraintTypeChoices.MAX_LENGTH:
            # Maximum character length
            try:
                max_len = int(config_value)
                is_valid = len(value) <= max_len
            except (ValueError, TypeError):
                is_valid = False

        elif constraint_type == ConstraintTypeChoices.MIN_LENGTH:
            # Minimum character length
            try:
                min_len = int(config_value)
                is_valid = len(value) >= min_len
            except (ValueError, TypeError):
                is_valid = False

        elif constraint_type == ConstraintTypeChoices.REGEX:
            # Custom regex pattern
            try:
                is_valid = bool(re.match(config_value, value))
            except re.error:
                is_valid = False

        elif constraint_type == ConstraintTypeChoices.STARTS_WITH:
            # Must start with specified string
            is_valid = value.startswith(config_value)

        elif constraint_type == ConstraintTypeChoices.ENDS_WITH:
            # Must end with specified string
            is_valid = value.endswith(config_value)

        elif constraint_type == ConstraintTypeChoices.ALLOWED_CHARS:
            # Only specified characters allowed
            allowed = set(config_value)
            is_valid = all(c in allowed for c in value)

        elif constraint_type == ConstraintTypeChoices.NO_UPPERCASE:
            # No uppercase letters allowed
            is_valid = not any(c.isupper() for c in value)

        elif constraint_type == ConstraintTypeChoices.NO_NUMBERS:
            # No numeric characters allowed
            is_valid = not any(c.isdigit() for c in value)

        elif constraint_type == ConstraintTypeChoices.URL_SAFE:
            # URL-safe characters only (a-z, A-Z, 0-9, -, _, .)
            is_valid = bool(re.match(r'^[a-zA-Z0-9\-_.]+$', value))

        error_message = None if is_valid else (
            constraint.error_message or constraint.get_default_error_message()
        )

        return ValidationResult(
            is_valid=is_valid,
            error_message=error_message,
            constraint_type=constraint_type
        )

    @staticmethod
    def validate_all_constraints(value: str, dimension_id: int, use_cache: bool = True) -> Dict[str, Any]:
        """
        Validate a value against all active constraints for a dimension.

        Args:
            value: The value to validate
            dimension_id: The ID of the dimension
            use_cache: Whether to use cached constraints (default: True)

        Returns:
            Dictionary with 'is_valid' boolean and 'errors' list
        """
        # Try to get constraints from cache
        cache_key = f'dimension_constraints:{dimension_id}'

        if use_cache:
            constraints = cache.get(cache_key)
        else:
            constraints = None

        if constraints is None:
            # Fetch from database
            constraints = list(
                DimensionConstraint.objects.filter(
                    dimension_id=dimension_id,
                    is_active=True
                ).order_by('order')
            )
            # Cache for 15 minutes
            cache.set(cache_key, constraints, 900)

        errors = []

        for constraint in constraints:
            result = ConstraintValidatorService.validate_constraint(value, constraint)
            if not result.is_valid:
                errors.append(result.to_dict())

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    @staticmethod
    def validate_with_constraints(value: str, constraints: List[DimensionConstraint]) -> Dict[str, Any]:
        """
        Validate a value against a specific list of constraints.

        Args:
            value: The value to validate
            constraints: List of constraint objects to validate against

        Returns:
            Dictionary with 'is_valid' boolean and 'errors' list
        """
        # Filter and sort active constraints
        active_constraints = [c for c in constraints if c.is_active]
        active_constraints.sort(key=lambda c: c.order)

        errors = []

        for constraint in active_constraints:
            result = ConstraintValidatorService.validate_constraint(value, constraint)
            if not result.is_valid:
                errors.append(result.to_dict())

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    @staticmethod
    def clear_constraint_cache(dimension_id: int):
        """Clear cached constraints for a dimension."""
        cache_key = f'dimension_constraints:{dimension_id}'
        cache.delete(cache_key)

    @staticmethod
    def get_constraint_violations(dimension_id: int) -> Dict[str, Any]:
        """
        Check existing dimension values for constraint violations.

        This is useful when constraints are added to a dimension that
        already has values, to identify which values would not pass
        the new constraints.

        Args:
            dimension_id: The ID of the dimension to check

        Returns:
            Dictionary with violation details
        """
        from ..models import DimensionValue

        # Get all active constraints for the dimension
        constraints = list(
            DimensionConstraint.objects.filter(
                dimension_id=dimension_id,
                is_active=True
            ).order_by('order')
        )

        if not constraints:
            return {
                'has_violations': False,
                'violations': [],
                'total_values': 0,
                'violating_values': 0
            }

        # Get all dimension values
        dimension_values = DimensionValue.objects.filter(dimension_id=dimension_id)

        violations = []
        for dim_value in dimension_values:
            result = ConstraintValidatorService.validate_with_constraints(
                dim_value.value,
                constraints
            )

            if not result['is_valid']:
                violations.append({
                    'dimension_value_id': dim_value.id,
                    'value': dim_value.value,
                    'label': dim_value.label,
                    'errors': result['errors']
                })

        return {
            'has_violations': len(violations) > 0,
            'violations': violations,
            'total_values': dimension_values.count(),
            'violating_values': len(violations)
        }
