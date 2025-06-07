"""
Naming pattern validation services.
"""

from typing import Dict, List
from ..models import Rule
from .string_generation_service import StringGenerationService


class NamingPatternValidator:
    """Validates naming patterns and rule configurations."""

    @staticmethod
    def validate_rule_configuration(rule: Rule) -> List[str]:
        """
        Validate that a rule has proper configuration.

        Returns:
            List of validation error messages
        """
        errors = []

        rule_details = rule.rule_details.all()

        if not rule_details.exists():
            errors.append("Rule has no rule details configured")
            return errors

        # Check for missing dimension orders
        orders = list(rule_details.values_list('dimension_order', flat=True))
        expected_orders = list(range(1, len(orders) + 1))

        if sorted(orders) != expected_orders:
            errors.append(
                "Rule details have gaps or duplicates in dimension_order")

        # Check for delimiter consistency
        delimiters = set(rule_details.values_list('delimiter', flat=True))
        delimiters.discard(None)
        delimiters.discard('')

        if len(delimiters) > 1:
            errors.append("Rule details have inconsistent delimiters")

        return errors

    @staticmethod
    def get_naming_preview(rule: Rule, field, sample_values: Dict[str, str]) -> str:
        """
        Generate a preview of what the naming would look like with sample values.
        """
        try:
            return StringGenerationService.generate_string_value(rule, field, sample_values)
        except Exception as e:
            return f"Preview failed: {str(e)}"
