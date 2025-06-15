from typing import Dict, List, Optional
from django.core.cache import cache
from django.utils import timezone
from .dimension_catalog_service import DimensionCatalogService
from .inheritance_matrix_service import InheritanceMatrixService
from .field_template_service import FieldTemplateService
from ..models import Rule, Field


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
            rule = Rule.objects.get(id=rule.id)

            # Build optimized field templates (dimension ID references only)
            field_templates = self.field_template.get_optimized_templates_for_rule(
                rule.id)

            # Build enhanced dimension catalog with fast lookups
            dimension_catalog = self.dimension_catalog.get_optimized_catalog_for_rule(
                rule.id)

            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                field_templates, dimension_catalog
            )

            # Build metadata (matching MetadataSerializer structure)
            inheritance_stats = dimension_catalog.get(
                'inheritance_lookup', {}).get('inheritance_stats', {})
            inheritance_coverage = inheritance_stats.get(
                'inheritance_coverage', 0.0)

            metadata = {
                'generated_at': timezone.now().isoformat(),
                'total_fields': len(field_templates),
                'total_dimensions': len(dimension_catalog.get('dimensions', {})),
                'inheritance_coverage': inheritance_coverage,
                'cache_status': 'generated'
            }

            return {
                'rule': rule,
                'rule_name': rule.name,
                'rule_slug': rule.slug,
                'field_templates': field_templates,
                'dimension_catalog': dimension_catalog,
                'metadata': metadata,
                'performance_metrics': performance_metrics
            }

        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule.id} not found")
        except Exception as e:
            raise Exception(f"Error building fast lookup rule data: {str(e)}")
