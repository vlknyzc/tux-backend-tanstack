from typing import Dict, List, Optional
from django.core.cache import cache
from django.utils import timezone
import logging
from .dimension_catalog_service import DimensionCatalogService
from .inheritance_matrix_service import InheritanceMatrixService
from .field_template_service import FieldTemplateService
from .rule_cache_service import RuleCacheService
from .rule_validation_service import RuleValidationService
from .rule_metrics_service import RuleMetricsService
from ..models import Rule, Field

logger = logging.getLogger(__name__)


class RuleService:
    """
    Facade service that coordinates between specialized rule services.

    This service acts as a unified interface for rule operations,
    delegating to specialized services:
    - DimensionCatalogService: Dimension catalog operations
    - InheritanceMatrixService: Inheritance matrix operations
    - FieldTemplateService: Field template operations
    - RuleCacheService: Cache management
    - RuleValidationService: Validation and scoring
    - RuleMetricsService: Performance metrics

    Refactored from God Class (Issue #13) to follow Single Responsibility Principle.
    """

    def __init__(self):
        # Core data services
        self.dimension_catalog = DimensionCatalogService()
        self.inheritance_matrix = InheritanceMatrixService()
        self.field_template = FieldTemplateService()

        # Supporting services (extracted from God Class refactoring)
        self.cache = RuleCacheService()
        self.validation = RuleValidationService()
        self.metrics = RuleMetricsService()

        self.cache_timeout = 30 * 60  # 30 minutes

    def _calculate_performance_metrics(self, field_templates, dimension_catalog):
        """
        Calculate performance metrics for the rule data.

        Delegates to RuleMetricsService for metrics calculation.

        Args:
            field_templates: List of field templates
            dimension_catalog: Dictionary containing dimension catalog data

        Returns:
            Dictionary containing performance metrics
        """
        return self.metrics.calculate_performance_metrics(
            field_templates,
            dimension_catalog
        )

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

        Delegates to RuleValidationService for validation logic.

        Args:
            rule: Rule instance or rule ID

        Returns:
            Dictionary containing validation summary
        """
        # Get data from specialized services
        field_templates = self.field_template.get_templates_for_rule(rule.id if hasattr(rule, 'id') else rule)
        inheritance_summary = self.inheritance_matrix.get_field_inheritance_summary(
            rule.id if hasattr(rule, 'id') else rule
        )

        # Delegate validation to validation service
        return self.validation.get_rule_validation_summary(
            rule,
            field_templates,
            inheritance_summary
        )

    def invalidate_all_caches(self, rule: Rule):
        """
        Invalidate all caches for a rule across all services.

        Delegates to RuleCacheService for cache management.

        Args:
            rule: Rule instance or rule ID
        """
        self.cache.invalidate_all_caches(rule)

    def bulk_invalidate_caches(self, rules: List[Rule]):
        """
        Invalidate caches for multiple rules.

        Delegates to RuleCacheService for cache management.

        Args:
            rules: List of Rule instances or rule IDs
        """
        self.cache.bulk_invalidate_caches(rules)

    def clear_rule_configuration_cache(self, rule_id: int):
        """
        Clear cache specifically for rule configuration endpoint.

        Delegates to RuleCacheService for cache management.

        Args:
            rule_id: ID of the rule
        """
        self.cache.clear_rule_configuration_cache(rule_id)

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
