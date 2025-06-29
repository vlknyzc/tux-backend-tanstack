from typing import Dict, List, Optional
from django.core.cache import cache
from django.utils import timezone
import logging
from .dimension_catalog_service import DimensionCatalogService
from .inheritance_matrix_service import InheritanceMatrixService
from .field_template_service import FieldTemplateService
from ..models import Rule, Field

logger = logging.getLogger(__name__)


class RuleService:
    """
    Unified service that combines all rule optimization services.
    This is the main service to replace the RuleNestedSerializer.
    """

    def __init__(self):
        self.dimension_catalog = DimensionCatalogService()
        self.inheritance_matrix = InheritanceMatrixService()
        self.field_template = FieldTemplateService()
        self.cache_timeout = 30 * 60  # 30 minutes

    def _calculate_performance_metrics(self, field_templates, dimension_catalog):
        """
        Calculate performance metrics for the rule data.

        Args:
            field_templates: List of field templates
            dimension_catalog: Dictionary containing dimension catalog data

        Returns:
            Dictionary containing performance metrics
        """
        total_dimensions = len(dimension_catalog.get('dimensions', {}))
        total_fields = len(field_templates)

        # Calculate completeness scores
        field_completeness_scores = []
        for template in field_templates:
            if template.get('dimensions'):
                required_dims = sum(
                    1 for d in template['dimensions'] if d.get('is_required', False))
                total_dims = len(template['dimensions'])
                score = (required_dims / total_dims) * \
                    100 if total_dims > 0 else 0
                field_completeness_scores.append(score)

        avg_completeness = sum(field_completeness_scores) / \
            len(field_completeness_scores) if field_completeness_scores else 0

        # Get inheritance stats
        inheritance_stats = dimension_catalog.get(
            'inheritance_lookup', {}).get('inheritance_stats', {})
        inheritance_coverage = inheritance_stats.get(
            'inheritance_coverage', 0.0)

        return {
            'total_dimensions': total_dimensions,
            'total_fields': total_fields,
            'average_completeness_score': round(avg_completeness, 2),
            'inheritance_coverage': round(inheritance_coverage * 100, 2),
            'fields_analyzed': len(field_completeness_scores),
            'timestamp': timezone.now().isoformat()
        }

    def get_lightweight_rule_data(self, rule: Rule) -> Dict:
        """
        Get lightweight rule data for list views or when full data isn't needed.
        """
        try:
            rule = Rule.objects.select_related(
                'platform', 'created_by').get(id=rule.id)
        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule.id} does not exist")

        # Get basic field template info
        field_templates = self.field_template.get_templates_for_rule(rule.id)

        return {
            'id': rule.id,
            'name': rule.name,
            'slug': rule.slug,
            'description': rule.description,
            'status': rule.status,
            'is_default': rule.is_default,
            'platform': rule.platform.id,
            'platform_name': rule.platform.name,
            'platform_slug': rule.platform.slug,
            'created_by_name': f"{rule.created_by.first_name} {rule.created_by.last_name}".strip() if rule.created_by else None,
            'created': rule.created.isoformat(),
            'last_updated': rule.last_updated.isoformat(),

            # Summary information
            'total_fields': len(field_templates),
            'fields_with_rules': [{'id': f['field'], 'name': f['field_name'], 'field_level': f['field_level']} for f in field_templates],
            'can_generate_count': sum(1 for f in field_templates if f.get('can_generate', False)),
            'configuration_errors': rule.validate_configuration() if hasattr(rule, 'validate_configuration') else [],
        }

    def get_field_specific_data(self, rule: Rule, field: Field) -> Dict:
        """
        Get data specific to a single field within a rule.
        Useful for field-specific operations or editing.
        """
        field_template = self.field_template.get_template_for_field(
            rule.id, field.id)
        inheritance_info = self.inheritance_matrix.get_inheritance_for_dimension

        # Get inheritance information for all dimensions in this field
        dimension_inheritance = {}
        for dim in field_template['dimensions']:
            dim = dim['dimension']
            dimension_inheritance[dim] = self.inheritance_matrix.get_inheritance_for_dimension(
                rule.id, dim)

        return {
            'field_template': field_template,
            'dimension_inheritance': dimension_inheritance,
            'field_summary': {
                'can_generate': field_template.get('can_generate', False),
                'completeness_score': field_template.get('completeness_score', 0),
                'total_dimensions': field_template.get('dimension_count', 0),
                'inherited_dimensions': field_template.get('inherited_dimension_count', 0),
            }
        }

    def get_generation_preview(self, rule: Rule, field: Field, sample_values: Dict[str, str]) -> Dict:
        """
        Generate a preview using the field template service.
        """
        return self.field_template.get_generation_preview(rule.id, field.id, sample_values)

    def get_rule_validation_summary(self, rule: Rule) -> Dict:
        """
        Get comprehensive validation summary for a rule.
        """
        try:
            rule = Rule.objects.get(id=rule.id)
        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule.id} does not exist")

        field_templates = self.field_template.get_templates_for_rule(rule.id)
        inheritance_summary = self.inheritance_matrix.get_field_inheritance_summary(
            rule.id)

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
                    f"Field '{field_name}' cannot generate strings")

            # Check completeness
            completeness = template.get('completeness_score', 0)
            if completeness < 50:
                warnings.append(
                    f"Field '{field_name}' has low completeness score: {completeness:.1f}%")

            # Check for validation rules
            for rule_item in template.get('validation_rules', []):
                if rule_item['type'] == 'required_dimensions':
                    # This is informational, not an error
                    pass
                elif rule_item['type'] == 'parent_constraint':
                    warnings.append(
                        f"Field '{field_name}': {rule_item['message']}")

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
            'overall_score': self._calculate_overall_rule_score(field_templates, validation_issues, warnings),
        }

    def _calculate_overall_rule_score(self, field_templates: List[Dict], validation_issues: List[str], warnings: List[str]) -> float:
        """
        Calculate an overall rule quality score based on completeness, validation issues, and warnings.
        Returns a score from 0-100.
        """
        if not field_templates:
            return 0.0

        # Base score from field completeness
        completeness_scores = [template.get(
            'completeness_score', 0) for template in field_templates]
        avg_completeness = sum(completeness_scores) / \
            len(completeness_scores) if completeness_scores else 0

        # Penalty for validation issues (critical)
        # 15 points per validation issue
        validation_penalty = len(validation_issues) * 15

        # Penalty for warnings (less critical)
        warning_penalty = len(warnings) * 5  # 5 points per warning

        # Calculate final score
        final_score = avg_completeness - validation_penalty - warning_penalty

        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, final_score))

    def invalidate_all_caches(self, rule: Rule):
        """Invalidate all caches for a rule across all services"""
        self.dimension_catalog.invalidate_cache(rule.id)
        self.inheritance_matrix.invalidate_cache(rule.id)
        self.field_template.invalidate_cache(rule.id)

        # Also invalidate the complete data cache
        cache_key = f"complete_rule_data:{rule.id}"
        cache.delete(cache_key)

    def bulk_invalidate_caches(self, rules: List[Rule]):
        """Invalidate caches for multiple rules"""
        for rule in rules:
            self.invalidate_all_caches(rule)

    def get_complete_rule_data(self, rule: Rule) -> Dict:
        """
        Get complete rule data with optimized lookup tables for O(1) access patterns.
        This provides comprehensive lookup structures for maximum performance.
        """
        try:
            # Convert rule ID to Rule instance if needed
            if isinstance(rule, int):
                rule_id = rule
                rule = Rule.objects.get(id=rule)
            else:
                rule_id = rule.id
                rule = Rule.objects.get(id=rule.id)

            logger.info(
                f"Building complete rule data for rule {rule_id}: {rule.name}")

            # Build optimized field templates (dimension ID references only)
            try:
                field_templates = self.field_template.get_optimized_templates_for_rule(
                    rule)
                logger.info(
                    f"Field templates built successfully: {len(field_templates)} templates")
            except Exception as e:
                logger.error(
                    f"Error building field templates for rule {rule_id}: {str(e)}")
                raise Exception(f"Field template generation failed: {str(e)}")

            # Build enhanced dimension catalog with fast lookups
            try:
                dimension_catalog = self.dimension_catalog.get_optimized_catalog_for_rule(
                    rule.id)
                logger.info(
                    f"Dimension catalog built successfully: {len(dimension_catalog.get('dimensions', {}))} dimensions")
            except Exception as e:
                logger.error(
                    f"Error building dimension catalog for rule {rule_id}: {str(e)}")
                raise Exception(
                    f"Dimension catalog generation failed: {str(e)}")

            # Build metadata
            try:
                metadata = {
                    'generated_at': timezone.now().isoformat(),
                    'total_fields': len(field_templates),
                    'total_dimensions': len(dimension_catalog.get('dimensions', {})),
                    'inheritance_coverage': dimension_catalog.get('inheritance_lookup', {}).get('inheritance_stats', {}).get('inheritance_coverage', 0.0)
                }
            except Exception as e:
                logger.error(
                    f"Error building metadata for rule {rule_id}: {str(e)}")
                raise Exception(f"Metadata generation failed: {str(e)}")

            result = {
                'rule': rule.id,
                'rule_name': rule.name,
                'rule_slug': rule.slug,
                'field_templates': field_templates,
                'dimension_catalog': dimension_catalog,
                'metadata': metadata
            }

            logger.info(
                f"Complete rule data built successfully for rule {rule_id}")
            return result

        except Rule.DoesNotExist:
            logger.error(
                f"Rule with id {rule if isinstance(rule, int) else rule.id} not found")
            raise ValueError(
                f"Rule with id {rule if isinstance(rule, int) else rule.id} not found")
        except Exception as e:
            rule_id = rule if isinstance(rule, int) else (
                rule.id if hasattr(rule, 'id') else 'unknown')
            logger.error(
                f"Error building complete rule data for rule {rule_id}: {str(e)}")
            import traceback
            logger.error("Traceback:")
            logger.error(traceback.format_exc())
            raise Exception(
                f"Error building fast lookup rule data for rule {rule_id}: {str(e)}")
