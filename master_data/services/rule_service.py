from typing import Dict, List, Optional
from django.core.cache import cache
from django.utils import timezone
from .dimension_catalog_service import DimensionCatalogService
from .inheritance_matrix_service import InheritanceMatrixService
from .field_template_service import FieldTemplateService
from ..models import Rule


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

    def get_lightweight_rule_data(self, rule_id: int) -> Dict:
        """
        Get lightweight rule data for list views or when full data isn't needed.
        """
        try:
            rule = Rule.objects.select_related(
                'platform', 'created_by').get(id=rule_id)
        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule_id} does not exist")

        # Get basic field template info
        field_templates = self.field_template.get_templates_for_rule(rule_id)

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
            'fields_with_rules': [{'id': f['field_id'], 'name': f['field_name'], 'field_level': f['field_level']} for f in field_templates],
            'can_generate_count': sum(1 for f in field_templates if f.get('can_generate', False)),
            'configuration_errors': rule.validate_configuration() if hasattr(rule, 'validate_configuration') else [],
        }

    def get_field_specific_data(self, rule_id: int, field_id: int) -> Dict:
        """
        Get data specific to a single field within a rule.
        Useful for field-specific operations or editing.
        """
        field_template = self.field_template.get_template_for_field(
            rule_id, field_id)
        inheritance_info = self.inheritance_matrix.get_inheritance_for_dimension

        # Get inheritance information for all dimensions in this field
        dimension_inheritance = {}
        for dim in field_template['dimensions']:
            dim_id = dim['dimension_id']
            dimension_inheritance[dim_id] = self.inheritance_matrix.get_inheritance_for_dimension(
                rule_id, dim_id)

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

    def get_generation_preview(self, rule_id: int, field_id: int, sample_values: Dict[str, str]) -> Dict:
        """
        Generate a preview using the field template service.
        """
        return self.field_template.get_generation_preview(rule_id, field_id, sample_values)

    def get_rule_validation_summary(self, rule_id: int) -> Dict:
        """
        Get comprehensive validation summary for a rule.
        """
        try:
            rule = Rule.objects.get(id=rule_id)
        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule_id} does not exist")

        field_templates = self.field_template.get_templates_for_rule(rule_id)
        inheritance_summary = self.inheritance_matrix.get_field_inheritance_summary(
            rule_id)

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
            'rule_id': rule_id,
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

    def _calculate_overall_rule_score(self, field_templates: List[Dict], issues: List[str], warnings: List[str]) -> float:
        """Calculate an overall score for the rule (0-100)"""
        if not field_templates:
            return 0

        # Base score from field completeness
        total_completeness = sum(f.get('completeness_score', 0)
                                 for f in field_templates)
        avg_completeness = total_completeness / len(field_templates)

        # Penalties for issues and warnings
        issue_penalty = len(issues) * 10  # 10 points per critical issue
        warning_penalty = len(warnings) * 2  # 2 points per warning

        # Final score (can't go below 0)
        final_score = max(0, avg_completeness -
                          issue_penalty - warning_penalty)

        return min(100, final_score)  # Cap at 100

    def invalidate_all_caches(self, rule_id: int):
        """Invalidate all caches for a rule across all services"""
        self.dimension_catalog.invalidate_cache(rule_id)
        self.inheritance_matrix.invalidate_cache(rule_id)
        self.field_template.invalidate_cache(rule_id)

        # Also invalidate the complete data cache
        cache_key = f"complete_rule_data:{rule_id}"
        cache.delete(cache_key)

    def bulk_invalidate_caches(self, rule_ids: List[int]):
        """Invalidate caches for multiple rules"""
        for rule_id in rule_ids:
            self.invalidate_all_caches(rule_id)

    def get_performance_metrics(self, rule_id: int) -> Dict:
        """Get performance metrics for the optimization"""
        cache_keys = [
            f"dimension_catalog:{rule_id}",
            f"inheritance_matrix:{rule_id}",
            f"field_templates:{rule_id}",
            f"complete_rule_data:{rule_id}"
        ]

        cache_status = {}
        for key in cache_keys:
            service_name = key.split(':')[0]
            cache_status[service_name] = {
                'cached': cache.get(key) is not None,
                'key': key
            }

        return {
            'rule_id': rule_id,
            'cache_status': cache_status,
            'services_initialized': {
                'dimension_catalog': self.dimension_catalog is not None,
                'inheritance_matrix': self.inheritance_matrix is not None,
                'field_template': self.field_template is not None,
            }
        }

    def get_complete_rule_data(self, rule_id: int) -> Dict:
        """
        Get complete rule data with optimized lookup tables for O(1) access patterns.
        This provides comprehensive lookup structures for maximum performance.
        """
        try:
            rule = Rule.objects.get(id=rule_id)

            # Build optimized field templates (dimension ID references only)
            field_templates = self.field_template.get_optimized_templates_for_rule(
                rule_id)

            # Build enhanced dimension catalog with fast lookups
            dimension_catalog = self.dimension_catalog.get_optimized_catalog_for_rule(
                rule_id)

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
                'rule_id': rule.id,
                'rule_name': rule.name,
                'rule_slug': rule.slug,
                'field_templates': field_templates,
                'dimension_catalog': dimension_catalog,
                'metadata': metadata,
                'performance_metrics': performance_metrics
            }

        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule_id} not found")
        except Exception as e:
            raise Exception(f"Error building fast lookup rule data: {str(e)}")

    def _calculate_performance_metrics(self, field_templates: List[Dict], dimension_catalog: Dict) -> Dict:
        """Calculate comprehensive performance metrics for fast lookup structures"""

        # Basic counts
        total_dimensions = len(dimension_catalog.get('dimensions', {}))
        total_field_levels = len(field_templates)

        # Count lookup tables and indexes
        inheritance_lookup = dimension_catalog.get('inheritance_lookup', {})
        relationship_maps = dimension_catalog.get('relationship_maps', {})
        metadata_indexes = dimension_catalog.get('metadata_indexes', {})
        constraints = dimension_catalog.get('constraints', {})

        lookup_tables_count = (
            len(inheritance_lookup.get('by_dimension_id', {})) +
            len(inheritance_lookup.get('by_target_field_level', {})) +
            len(inheritance_lookup.get('by_source_field_level', {})) +
            len(relationship_maps.get('field_to_dimensions', {})) +
            len(relationship_maps.get('dimension_to_fields', {})) +
            len(constraints.get('parent_to_children_map', {})) +
            len(constraints.get('child_to_parent_map', {}))
        )

        index_structures_count = (
            len(metadata_indexes.get('dimension_type_groups', {})) +
            len(metadata_indexes.get('formatting_patterns', {})) +
            len(metadata_indexes.get('validation_flags', {})) +
            len(metadata_indexes.get('fast_lookups', {}))
        )

        # Coverage percentages
        inheritance_stats = inheritance_lookup.get('inheritance_stats', {})
        constraint_stats = constraints.get('constraint_stats', {})

        inheritance_coverage_percent = inheritance_stats.get(
            'inheritance_coverage', 0.0)
        constraint_coverage_percent = constraint_stats.get(
            'constraint_coverage', 0.0)

        # Relationship metrics
        relationship_stats = relationship_maps.get('relationship_stats', {})
        avg_dimensions_per_field = relationship_stats.get(
            'avg_dimensions_per_field', 0.0)

        # Calculate optimization score (0-100)
        optimization_factors = {
            'lookup_density': min(100, (lookup_tables_count / max(total_dimensions, 1)) * 100),
            # 4 main index types
            'index_coverage': min(100, (index_structures_count / 4) * 25),
            'inheritance_optimization': inheritance_coverage_percent,
            'constraint_optimization': constraint_coverage_percent,
            # Cap at 100
            'relationship_efficiency': min(100, avg_dimensions_per_field * 20)
        }

        optimization_score = sum(
            optimization_factors.values()) / len(optimization_factors)

        # Cache efficiency metrics
        cache_efficiency = {
            'inheritance_cache_hit_rate': min(100, inheritance_coverage_percent),
            'constraint_cache_hit_rate': min(100, constraint_coverage_percent),
            'metadata_index_efficiency': min(100, (index_structures_count / max(total_dimensions, 1)) * 100),
            'relationship_cache_density': min(100, (len(relationship_maps.get('field_to_dimensions', {})) / max(total_field_levels, 1)) * 100),
            'overall_cache_performance': optimization_score
        }

        return {
            'total_dimensions': total_dimensions,
            'total_field_levels': total_field_levels,
            'lookup_tables_count': lookup_tables_count,
            'index_structures_count': index_structures_count,
            'inheritance_coverage_percent': inheritance_coverage_percent,
            'constraint_coverage_percent': constraint_coverage_percent,
            'avg_dimensions_per_field': avg_dimensions_per_field,
            'optimization_score': round(optimization_score, 2),
            'cache_efficiency': cache_efficiency
        }

    def _calculate_rule_complexity(self, rule: Rule) -> float:
        """Calculate rule complexity score based on dimensions, constraints, and inheritance"""
        try:
            rule_details = RuleDetail.objects.filter(rule=rule).select_related(
                'field', 'dimension'
            ).count()

            # Count unique dimensions and field levels
            unique_dimensions = RuleDetail.objects.filter(
                rule=rule).values('dimension').distinct().count()
            unique_field_levels = RuleDetail.objects.filter(
                rule=rule).values('field__field_level').distinct().count()

            # Count constraints (dimensions with parents)
            constrained_dimensions = RuleDetail.objects.filter(
                rule=rule,
                dimension__parent__isnull=False
            ).count()

            # Calculate complexity factors
            detail_complexity = rule_details * 0.1
            dimension_complexity = unique_dimensions * 0.3
            field_complexity = unique_field_levels * 0.2
            constraint_complexity = constrained_dimensions * 0.4

            total_complexity = detail_complexity + dimension_complexity + \
                field_complexity + constraint_complexity

            # Normalize to 0-100 scale
            normalized_complexity = min(100, total_complexity)

            return round(normalized_complexity, 2)

        except Exception:
            return 0.0
