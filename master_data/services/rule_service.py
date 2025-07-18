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

        # Clear Django's page cache for rule configuration endpoint
        from django.core.cache import cache
        cache_key = f"views.decorators.cache.cache_page.{rule.id}.GET"
        cache.delete(cache_key)

    def bulk_invalidate_caches(self, rules: List[Rule]):
        """Invalidate caches for multiple rules"""
        for rule in rules:
            self.invalidate_all_caches(rule)

    def clear_rule_configuration_cache(self, rule_id: int):
        """Clear cache specifically for rule configuration endpoint"""
        from django.core.cache import cache

        # Clear Django's page cache for rule configuration endpoint
        cache_key = f"views.decorators.cache.cache_page.{rule_id}.GET"
        cache.delete(cache_key)

        logger.info(f"Cleared rule configuration cache for rule {rule_id}")

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

    def get_rule_configuration_data(self, rule_id: int) -> Dict:
        """
        Get rule configuration data that matches the structure of rule_configuration.json.
        This method returns the exact structure shown in the redocs documentation.
        """
        try:
            # Get rule with related data
            rule = Rule.objects.select_related(
                'platform', 'workspace', 'created_by'
            ).get(id=rule_id)

            # Get all rule details with related data in a single query
            rule_details = rule.rule_details.select_related(
                'field', 'dimension', 'dimension__parent'
            ).prefetch_related(
                'dimension__dimension_values'
            ).order_by('field__field_level', 'dimension_order')

            # Pre-build inheritance lookup to avoid N+1 queries
            inheritance_lookup = self._build_inheritance_lookup(rule_details)

            # Build fields as an array instead of object
            fields = []

            # Group rule details by field
            fields_data = {}
            for detail in rule_details:
                field = detail.field
                if field.id not in fields_data:
                    fields_data[field.id] = {
                        'field': field,
                        'field_items': []
                    }
                fields_data[field.id]['field_items'].append(detail)

            # Build fields structure as array - exactly matching redocs format
            for field_id, field_data in fields_data.items():
                field = field_data['field']
                field_obj = {
                    'id': field.id,
                    'name': field.name,
                    'level': field.field_level,
                    'next_field_id': field.next_field.id if field.next_field else None,
                    'next_field_name': field.next_field.name if field.next_field else None,
                    'field_items': []
                }

                # Add field items (rule details) - exactly matching redocs format
                for detail in field_data['field_items']:
                    # Use pre-built inheritance lookup
                    inheritance_info = inheritance_lookup.get(detail.id, {
                        'is_inherited': False,
                        'inherits_from_field_item': None
                    })

                    field_obj['field_items'].append({
                        'id': detail.id,
                        'dimension_id': detail.dimension.id,
                        'order': detail.dimension_order,
                        'is_required': getattr(detail, 'is_required', True),
                        'is_inherited': inheritance_info['is_inherited'],
                        'inherits_from_field_item': inheritance_info['inherits_from_field_item'],
                        'prefix': detail.prefix,
                        'suffix': detail.suffix,
                        'delimiter': detail.delimiter
                    })

                fields.append(field_obj)

            # Sort fields by level to maintain order
            fields.sort(key=lambda x: x['level'])

            # Build dimensions and dimension values - exactly matching redocs format
            dimensions, dimension_values = self._build_dimensions_and_values_for_configuration(
                rule_details)

            # Build the result - exactly matching redocs structure
            result = {
                'id': rule.id,
                'name': rule.name,
                'slug': rule.slug,
                'platform': {
                    'id': rule.platform.id,
                    'name': rule.platform.name,
                    'slug': rule.platform.slug
                },
                'workspace': {
                    'id': rule.workspace.id,
                    'name': rule.workspace.name
                },
                'fields': fields,
                'dimensions': dimensions,
                'dimension_values': dimension_values,
                'generated_at': timezone.now().isoformat(),
                'created_by': {
                    'id': rule.created_by.id if rule.created_by else None,
                    'name': f"{rule.created_by.first_name} {rule.created_by.last_name}".strip() if rule.created_by else None
                }
            }

            return result

        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule_id} not found")

    def _build_inheritance_lookup(self, rule_details) -> Dict:
        """Build inheritance lookup to avoid N+1 queries"""
        inheritance_lookup = {}

        # Group by dimension and field level for efficient lookup
        dimension_field_map = {}
        for detail in rule_details:
            dimension_id = detail.dimension.id
            field_level = detail.field.field_level

            if dimension_id not in dimension_field_map:
                dimension_field_map[dimension_id] = {}

            dimension_field_map[dimension_id][field_level] = detail.id

        # Build inheritance lookup
        for detail in rule_details:
            dimension_id = detail.dimension.id
            current_field_level = detail.field.field_level

            # Check if this dimension exists in previous field levels
            is_inherited = False
            inherits_from_field_item = None

            if current_field_level > 1:
                for level in range(current_field_level - 1, 0, -1):
                    if level in dimension_field_map.get(dimension_id, {}):
                        is_inherited = True
                        inherits_from_field_item = dimension_field_map[dimension_id][level]
                        break

            inheritance_lookup[detail.id] = {
                'is_inherited': is_inherited,
                'inherits_from_field_item': inherits_from_field_item
            }

        return inheritance_lookup

    def _build_dimensions_and_values(self, rule_details) -> tuple:
        """Build dimensions and dimension values from rule details"""
        dimensions = {}
        dimension_values = {}

        # Get all unique dimensions used in this rule
        unique_dimensions = set()
        for detail in rule_details:
            unique_dimensions.add(detail.dimension)

        for dimension in unique_dimensions:
            dimensions[str(dimension.id)] = {
                'id': dimension.id,
                'name': dimension.name,
                'type': dimension.type,
                'description': dimension.description or ''
            }

            # Build dimension values
            values = []
            for value in dimension.dimension_values.all():
                values.append({
                    'id': value.id,
                    'dimension_id': dimension.id,
                    'value': value.value,
                    'label': value.label or value.value,
                    'utm': getattr(value, 'utm', value.value),
                    'description': value.description or '',
                    'parent': value.parent.id if value.parent else None,
                    'has_parent': bool(value.parent),
                    'parent_dimension': value.parent_dimension.id if getattr(value, 'parent_dimension', None) else None
                })

            if values:
                dimension_values[str(dimension.id)] = values

        return dimensions, dimension_values

    def _build_dimensions_and_values_for_configuration(self, rule_details) -> tuple:
        """
        Build dimensions and dimension values specifically for rule configuration format.
        This matches the exact structure shown in the redocs.
        """
        dimensions = {}
        dimension_values = {}

        # Get all unique dimensions used in this rule
        unique_dimensions = set()
        for detail in rule_details:
            unique_dimensions.add(detail.dimension)

        for dimension in unique_dimensions:
            # Build dimension structure - exactly matching redocs format
            dimensions[str(dimension.id)] = {
                'id': dimension.id,
                'name': dimension.name,
                'type': dimension.type,
                'description': dimension.description or ''
            }

            # Build dimension values - exactly matching redocs format
            values = []
            for value in dimension.dimension_values.all():
                values.append({
                    'id': value.id,
                    'dimension_id': dimension.id,
                    'value': value.value,
                    'label': value.label or value.value,
                    'utm': getattr(value, 'utm', value.value),
                    'description': value.description or '',
                    'parent': value.parent.id if value.parent else None,
                    'has_parent': bool(value.parent),
                    'parent_dimension': value.parent_dimension.id if getattr(value, 'parent_dimension', None) else None
                })

            if values:
                dimension_values[str(dimension.id)] = values

        return dimensions, dimension_values
