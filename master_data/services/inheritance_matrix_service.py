from ..models import Rule, RuleDetail, Field
from django.db.models import QuerySet
from django.utils import timezone
from django.core.cache import cache
from typing import Dict, List, Optional, Tuple


class InheritanceMatrixService:
    """Service for building inheritance matrices and analyzing parent-child relationships"""

    def __init__(self):
        self.cache_timeout = 30 * 60  # 30 minutes

    def get_matrix_for_rule(self, rule_id: int) -> Dict:
        """Get inheritance matrix for a rule"""
        cache_key = f"inheritance_matrix:{rule_id}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            rule = Rule.objects.get(id=rule_id)
            if (hasattr(rule, 'needs_inheritance_refresh') and
                not rule.needs_inheritance_refresh and
                hasattr(rule, 'inheritance_matrix_cache') and
                    rule.inheritance_matrix_cache):
                cache.set(cache_key, rule.inheritance_matrix_cache,
                          self.cache_timeout)
                return rule.inheritance_matrix_cache
        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule_id} does not exist")

        matrix = self._build_matrix(rule)

        cache.set(cache_key, matrix, self.cache_timeout)

        # Update model cache if fields exist
        if hasattr(rule, 'inheritance_matrix_cache'):
            rule.inheritance_matrix_cache = matrix
            if hasattr(rule, 'inheritance_matrix_updated'):
                rule.inheritance_matrix_updated = timezone.now()
                rule.save(update_fields=[
                          'inheritance_matrix_cache', 'inheritance_matrix_updated'])
            else:
                rule.save(update_fields=['inheritance_matrix_cache'])

        return matrix

    def _build_matrix(self, rule: Rule) -> Dict:
        """Build inheritance matrix using optimized queries"""
        rule_details = list(
            RuleDetail.objects.filter(rule=rule).select_related(
                'dimension', 'field', 'dimension__parent'
            ).order_by('field__field_level', 'dimension_order')
        )

        # Convert to format for analysis
        rule_details_data = [
            {
                'id': detail.id,
                'rule': detail.rule.id,
                'field_level': detail.field.field_level,
                'field_id': detail.field.id,
                'field_name': detail.field.name,
                'dimension': detail.dimension.id,
                'dimension_name': detail.dimension.name,
                'dimension_type': detail.dimension.type,
                'dimension_order': detail.dimension_order,
                'parent_dimension_id': detail.dimension.parent_id,
                'parent_dimension_name': detail.dimension.parent.name if detail.dimension.parent_id else None,
                'is_required': getattr(detail, 'is_required', True),
                'prefix': detail.prefix or '',
                'suffix': detail.suffix or '',
                'delimiter': detail.delimiter or '',
            }
            for detail in rule_details
        ]

        # Analyze inheritance patterns
        inheritance_analysis = self._analyze_inheritance_patterns(
            rule_details_data)

        return {
            'rule_id': rule.id,
            'rule_name': rule.name,
            'inheritance_matrix': inheritance_analysis,
            'generated_at': timezone.now().isoformat(),
        }

    def _analyze_inheritance_patterns(self, rule_details_data: List[Dict]) -> Dict:
        """Analyze inheritance patterns between field levels"""
        # Group by field level and dimension
        field_levels = {}
        # Maps (dimension_id, field_level) -> rule_detail
        dimension_field_map = {}

        for detail in rule_details_data:
            field_level = detail['field_level']
            dimension_id = detail['dimension']

            # Group by field level
            if field_level not in field_levels:
                field_levels[field_level] = []
            field_levels[field_level].append(detail)

            # Create lookup map
            key = (dimension_id, field_level)
            dimension_field_map[key] = detail

        # Find inheritance relationships
        inheritance_relationships = []
        inherited_dimensions = set()

        # Sort field levels to process in order
        sorted_levels = sorted(field_levels.keys())

        for i, current_level in enumerate(sorted_levels):
            if i == 0:  # Skip first level (no inheritance possible)
                continue

            current_details = field_levels[current_level]

            for detail in current_details:
                dimension_id = detail['dimension']

                # Look for this dimension in previous field levels
                inherited_from = []
                for prev_level in sorted_levels[:i]:  # All previous levels
                    prev_key = (dimension_id, prev_level)
                    if prev_key in dimension_field_map:
                        parent_detail = dimension_field_map[prev_key]
                        inherited_from.append({
                            'parent_field_level': prev_level,
                            'parent_field_name': parent_detail['field_name'],
                            'parent_rule_detail_id': parent_detail['id'],
                            'inherits_formatting': self._check_formatting_inheritance(detail, parent_detail),
                        })
                        inherited_dimensions.add(dimension_id)

                if inherited_from:
                    # Take the most immediate parent (highest field level)
                    immediate_parent = max(
                        inherited_from, key=lambda x: x['parent_field_level'])

                    inheritance_relationships.append({
                        'child_rule_detail_id': detail['id'],
                        'child_field_level': detail['field_level'],
                        'child_field_name': detail['field_name'],
                        'dimension_id': dimension_id,
                        'dimension_name': detail['dimension_name'],
                        'immediate_parent': immediate_parent,
                        'all_parents': inherited_from,
                        'is_inherited': True,
                    })

        # Find field level dependencies
        field_dependencies = self._analyze_field_dependencies(
            field_levels, sorted_levels)

        # Build dimension inheritance tree
        inheritance_tree = self._build_inheritance_tree(
            inheritance_relationships)

        return {
            'field_levels': field_levels,
            'inheritance_relationships': inheritance_relationships,
            'inherited_dimensions': list(inherited_dimensions),
            'field_dependencies': field_dependencies,
            'inheritance_tree': inheritance_tree,
            'total_inherited_dimensions': len(inherited_dimensions),
            'inheritance_coverage': len(inherited_dimensions) / len(rule_details_data) if rule_details_data else 0,
        }

    def _check_formatting_inheritance(self, child_detail: Dict, parent_detail: Dict) -> bool:
        """Check if formatting rules are inherited from parent"""
        return (
            child_detail['prefix'] == parent_detail['prefix'] and
            child_detail['suffix'] == parent_detail['suffix'] and
            child_detail['delimiter'] == parent_detail['delimiter']
        )

    def _analyze_field_dependencies(self, field_levels: Dict, sorted_levels: List[int]) -> Dict:
        """Analyze dependencies between field levels"""
        dependencies = {}

        for level in sorted_levels:
            dependencies[level] = {
                'field_level': level,
                'dimension_count': len(field_levels[level]),
                'unique_dimensions': len(set(d['dimension'] for d in field_levels[level])),
                'required_dimensions': len([d for d in field_levels[level] if d['is_required']]),
                'depends_on_levels': [],
            }

            # Find which previous levels this level depends on
            current_dimensions = set(d['dimension']
                                     for d in field_levels[level])

            for prev_level in sorted_levels:
                if prev_level >= level:
                    break

                prev_dimensions = set(d['dimension']
                                      for d in field_levels[prev_level])
                common_dimensions = current_dimensions.intersection(
                    prev_dimensions)

                if common_dimensions:
                    dependencies[level]['depends_on_levels'].append({
                        'field_level': prev_level,
                        'shared_dimensions': len(common_dimensions),
                        'dimension_names': [d['dimension_name'] for d in field_levels[level]
                                            if d['dimension'] in common_dimensions]
                    })

        return dependencies

    def _build_inheritance_tree(self, inheritance_relationships: List[Dict]) -> Dict:
        """Build a tree structure showing inheritance hierarchy"""
        tree = {}

        # Group by dimension
        by_dimension = {}
        for rel in inheritance_relationships:
            dim_id = rel['dimension_id']
            if dim_id not in by_dimension:
                by_dimension[dim_id] = []
            by_dimension[dim_id].append(rel)

        # Build tree for each dimension
        for dim_id, rels in by_dimension.items():
            # Sort by field level
            rels.sort(key=lambda x: x['child_field_level'])

            tree[dim_id] = {
                'dimension_id': dim_id,
                'dimension_name': rels[0]['dimension_name'],
                'inheritance_chain': rels,
                'total_levels': len(rels) + 1,  # +1 for the root level
                'max_field_level': max(r['child_field_level'] for r in rels),
            }

        return tree

    def get_inheritance_for_dimension(self, rule_id: int, dimension_id: int) -> Dict:
        """Get detailed inheritance information for a specific dimension"""
        matrix = self.get_matrix_for_rule(rule_id)
        inheritance_matrix = matrix['inheritance_matrix']

        # Find all relationships for this dimension
        dimension_relationships = [
            rel for rel in inheritance_matrix['inheritance_relationships']
            if rel['dimension_id'] == dimension_id
        ]

        if not dimension_relationships:
            return {
                'dimension_id': dimension_id,
                'has_inheritance': False,
                'inheritance_chain': [],
            }

        return {
            'dimension_id': dimension_id,
            'has_inheritance': True,
            'inheritance_chain': dimension_relationships,
            'inheritance_tree': inheritance_matrix['inheritance_tree'].get(dimension_id, {}),
        }

    def get_field_inheritance_summary(self, rule_id: int) -> Dict:
        """Get a summary of inheritance patterns by field level"""
        matrix = self.get_matrix_for_rule(rule_id)
        inheritance_matrix = matrix['inheritance_matrix']

        summary = {}
        for level, deps in inheritance_matrix['field_dependencies'].items():
            summary[level] = {
                'field_level': level,
                'total_dimensions': deps['dimension_count'],
                'inherited_dimensions': len([
                    rel for rel in inheritance_matrix['inheritance_relationships']
                    if rel['child_field_level'] == level
                ]),
                'original_dimensions': deps['dimension_count'] - len([
                    rel for rel in inheritance_matrix['inheritance_relationships']
                    if rel['child_field_level'] == level
                ]),
                'inheritance_percentage': 0,
            }

            if summary[level]['total_dimensions'] > 0:
                summary[level]['inheritance_percentage'] = (
                    summary[level]['inherited_dimensions'] /
                    summary[level]['total_dimensions'] * 100
                )

        return summary

    def invalidate_cache(self, rule_id: int):
        """Invalidate inheritance matrix cache for a rule"""
        cache_key = f"inheritance_matrix:{rule_id}"
        cache.delete(cache_key)

        try:
            rule = Rule.objects.get(id=rule_id)
            if hasattr(rule, 'needs_inheritance_refresh'):
                rule.needs_inheritance_refresh = True
                rule.save(update_fields=['needs_inheritance_refresh'])
        except Rule.DoesNotExist:
            pass
