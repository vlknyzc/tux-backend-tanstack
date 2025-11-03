"""
RuleValidationService: Validates rule structure and constraints.

This service handles all validation logic for rules, including:
- Rule configuration validation
- Field completeness checking
- Validation issue compilation
- Rule quality scoring

Part of the refactoring from God Class (Issue #13) to separate validation
concerns from business logic.
"""

from typing import Dict, List
import logging

from ..models import Rule

logger = logging.getLogger(__name__)


class RuleValidationService:
    """
    Service for validating rule structure and calculating quality scores.

    Responsibilities:
    - Comprehensive rule validation
    - Field-level validation
    - Completeness scoring
    - Overall rule quality assessment
    - Warning and error compilation

    This service focuses solely on validation logic, separated from
    cache management, template generation, and other concerns.
    """

    def __init__(self):
        """Initialize validation service."""
        pass

    def get_rule_validation_summary(
        self,
        rule,
        field_templates: List[Dict],
        inheritance_summary: Dict
    ) -> Dict:
        """
        Get comprehensive validation summary for a rule.

        Args:
            rule: Rule instance or rule ID
            field_templates: List of field templates from FieldTemplateService
            inheritance_summary: Inheritance summary from InheritanceMatrixService

        Returns:
            Dictionary containing:
            - rule: Rule instance
            - rule_name: Name of the rule
            - is_valid: Boolean indicating if rule is valid
            - validation_issues: List of critical issues
            - warnings: List of warnings
            - field_summary: Summary of field validation
            - inheritance_summary: Inheritance information
            - overall_score: Quality score (0-100)
        """
        # Get rule instance if ID provided
        if isinstance(rule, int):
            try:
                rule = Rule.objects.get(id=rule)
            except Rule.DoesNotExist:
                raise ValueError(f"Rule with id {rule} does not exist")
        else:
            try:
                rule = Rule.objects.get(id=rule.id)
            except Rule.DoesNotExist:
                raise ValueError(f"Rule with id {rule.id} does not exist")

        # Compile validation issues
        validation_issues = []
        warnings = []

        # Configuration errors
        config_errors = rule.validate_configuration() if hasattr(
            rule, 'validate_configuration') else []
        validation_issues.extend(config_errors)

        # Field-level validation
        for template in field_templates:
            field_name = template['field_name']

            # Check if field can generate
            if not template.get('can_generate', False):
                validation_issues.append(
                    f"Field '{field_name}' cannot generate strings"
                )

            # Check completeness
            completeness = template.get('completeness_score', 0)
            if completeness < 50:
                warnings.append(
                    f"Field '{field_name}' has low completeness score: {completeness:.1f}%"
                )

            # Check for validation rules
            for rule_item in template.get('validation_rules', []):
                if rule_item['type'] == 'required_dimensions':
                    # This is informational, not an error
                    pass
                elif rule_item['type'] == 'parent_constraint':
                    warnings.append(
                        f"Field '{field_name}': {rule_item['message']}")

        # Calculate overall score
        overall_score = self._calculate_overall_rule_score(
            field_templates,
            validation_issues,
            warnings
        )

        return {
            'rule': rule,
            'rule_name': rule.name,
            'is_valid': len(validation_issues) == 0,
            'validation_issues': validation_issues,
            'warnings': warnings,
            'field_summary': {
                'total_fields': len(field_templates),
                'valid_fields': sum(1 for f in field_templates if f.get('can_generate', False)),
                'fields_with_warnings': sum(1 for f in field_templates if f.get('completeness_score', 0) < 50),
            },
            'inheritance_summary': inheritance_summary,
            'overall_score': overall_score,
        }

    def _calculate_overall_rule_score(
        self,
        field_templates: List[Dict],
        validation_issues: List[str],
        warnings: List[str]
    ) -> float:
        """
        Calculate an overall rule quality score based on completeness,
        validation issues, and warnings.

        Args:
            field_templates: List of field templates
            validation_issues: List of critical validation issues
            warnings: List of warnings

        Returns:
            Score from 0-100, where:
            - 100 = Perfect rule with no issues
            - 0 = Rule with critical issues

        Scoring formula:
        - Base score: Average field completeness
        - Penalties:
          - Validation issues: -15 points each (critical)
          - Warnings: -5 points each (less critical)
        """
        if not field_templates:
            return 0.0

        # Base score from field completeness
        completeness_scores = [
            template.get('completeness_score', 0)
            for template in field_templates
        ]
        avg_completeness = (
            sum(completeness_scores) / len(completeness_scores)
            if completeness_scores else 0
        )

        # Penalty for validation issues (critical)
        validation_penalty = len(validation_issues) * 15  # 15 points per issue

        # Penalty for warnings (less critical)
        warning_penalty = len(warnings) * 5  # 5 points per warning

        # Calculate final score
        final_score = avg_completeness - validation_penalty - warning_penalty

        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, final_score))

    def validate_rule_structure(self, rule) -> List[str]:
        """
        Validate the structure of a rule.

        Args:
            rule: Rule instance or rule ID

        Returns:
            List of validation error messages (empty if valid)
        """
        # Get rule instance if ID provided
        if isinstance(rule, int):
            try:
                rule = Rule.objects.get(id=rule)
            except Rule.DoesNotExist:
                return [f"Rule with id {rule} does not exist"]
        else:
            try:
                rule = Rule.objects.get(id=rule.id)
            except Rule.DoesNotExist:
                return [f"Rule with id {rule.id} does not exist"]

        validation_errors = []

        # Check basic structure
        if not rule.name:
            validation_errors.append("Rule name is required")

        if not rule.platform:
            validation_errors.append("Rule must have a platform")

        if not rule.workspace:
            validation_errors.append("Rule must have a workspace")

        # Check rule details exist
        rule_details_count = rule.rule_details.count()
        if rule_details_count == 0:
            validation_errors.append("Rule must have at least one dimension configured")

        # Use model's validate_configuration if available
        if hasattr(rule, 'validate_configuration'):
            config_errors = rule.validate_configuration()
            validation_errors.extend(config_errors)

        return validation_errors

    def validate_dimension_constraints(self, rule) -> List[str]:
        """
        Validate dimension constraints for a rule.

        Args:
            rule: Rule instance or rule ID

        Returns:
            List of constraint violation messages (empty if valid)
        """
        # Get rule instance if ID provided
        if isinstance(rule, int):
            try:
                rule = Rule.objects.get(id=rule)
            except Rule.DoesNotExist:
                return [f"Rule with id {rule} does not exist"]

        constraint_violations = []

        # Get rule details
        rule_details = rule.rule_details.select_related(
            'dimension', 'field'
        ).order_by('field__field_level', 'dimension_order')

        # Check for duplicate dimensions in same field
        field_dimensions = {}
        for detail in rule_details:
            field_id = detail.field.id
            dim_id = detail.dimension.id

            if field_id not in field_dimensions:
                field_dimensions[field_id] = set()

            if dim_id in field_dimensions[field_id]:
                constraint_violations.append(
                    f"Duplicate dimension '{detail.dimension.name}' in field '{detail.field.name}'"
                )
            else:
                field_dimensions[field_id].add(dim_id)

        # Additional constraint checks could be added here
        # - Parent-child relationships
        # - Required dimension ordering
        # - Circular dependencies

        return constraint_violations

    def get_validation_score_explanation(self, score: float) -> str:
        """
        Get human-readable explanation of validation score.

        Args:
            score: Validation score (0-100)

        Returns:
            String explanation of the score
        """
        if score >= 90:
            return "Excellent: Rule is well-configured with minimal issues"
        elif score >= 75:
            return "Good: Rule is functional with minor warnings"
        elif score >= 50:
            return "Fair: Rule has some issues that should be addressed"
        elif score >= 25:
            return "Poor: Rule has significant issues affecting functionality"
        else:
            return "Critical: Rule has critical issues and may not work correctly"
