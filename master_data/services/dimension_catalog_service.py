from typing import Dict, List, Optional, Set
from django.core.cache import cache
from django.utils import timezone
from django.db.models import QuerySet, Prefetch
from ..models import Rule, RuleDetail, Dimension, DimensionValue


class DimensionCatalogService:
    """Service for generating optimized dimension catalogs"""

    def __init__(self):
        self.cache_timeout = 30 * 60  # 30 minutes

    def get_catalog_for_rule(self, rule: int) -> Dict:
        """Main method to get complete catalog for a rule"""
        cache_key = f"dimension_catalog:{rule}"

        # Check cache first
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Check model cache if it exists
        try:
            rule = Rule.objects.get(id=rule)
            if hasattr(rule, 'needs_inheritance_refresh') and not rule.needs_inheritance_refresh and hasattr(rule, 'dimension_catalog_cache') and rule.dimension_catalog_cache:
                cache.set(cache_key, rule.dimension_catalog_cache,
                          self.cache_timeout)
                return rule.dimension_catalog_cache
        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule} does not exist")

        # Generate fresh catalog
        catalog = self._build_catalog(rule)

        # Cache in both places
        cache.set(cache_key, catalog, self.cache_timeout)

        # Only update model cache if the fields exist
        if hasattr(rule, 'dimension_catalog_cache'):
            rule.dimension_catalog_cache = catalog
            rule.dimension_catalog_updated = timezone.now()
            update_fields = ['dimension_catalog_cache']
            if hasattr(rule, 'dimension_catalog_updated'):
                update_fields.append('dimension_catalog_updated')
            rule.save(update_fields=update_fields)

        return catalog

    def _build_catalog(self, rule: Rule) -> Dict:
        """Build complete catalog from database"""
        # Get all rule details for this rule with optimized queries
        rule_details = RuleDetail.objects.filter(rule=rule).select_related(
            'dimension', 'field', 'dimension__parent'
        ).prefetch_related(
            'dimension__dimension_values'
        ).order_by('field__field_level', 'dimension_order')

        # Build components
        dimensions_map = self._build_dimensions_map(rule_details)
        dimension_values = self._build_dimension_values(
            dimensions_map.keys(), rule)
        constraint_relationships = self._build_constraint_relationships(
            rule_details)
        field_templates = self._build_field_templates(rule_details)

        return {
            'rule': rule.id,
            'rule_name': rule.name,
            'rule_slug': rule.slug,
            'dimensions': dimensions_map,
            'dimension_values': dimension_values,
            'constraint_relationships': constraint_relationships,
            'field_templates': field_templates,
            'generated_at': timezone.now().isoformat(),
        }

    def _build_dimensions_map(self, rule_details: QuerySet) -> Dict:
        """Convert rule details to optimized dimensions map"""
        dimensions = {}

        for detail in rule_details:
            dimension = detail.dimension.id

            if dimension not in dimensions:
                dimensions[dimension] = {
                    'id': dimension,
                    'name': detail.dimension.name,
                    'type': detail.dimension.type,
                    'description': detail.dimension.description or '',

                    # Formatting rules from rule detail
                    'prefix': detail.prefix or '',
                    'suffix': detail.suffix or '',
                    'delimiter': detail.delimiter or '',
                    'effective_delimiter': detail.get_effective_delimiter() if hasattr(detail, 'get_effective_delimiter') else (detail.delimiter or ''),

                    # Behavior flags
                    'is_required': getattr(detail, 'is_required', True),
                    'allows_freetext': detail.dimension.type == 'text',
                    'is_dropdown': detail.dimension.type in ['list', 'combobox'],

                    # Constraint metadata
                    'has_parent_constraint': bool(detail.dimension.parent),
                    # Store ID instead of object
                    'parent_dimension': detail.dimension.parent.id if detail.dimension.parent else None,
                    'parent_dimension_name': detail.dimension.parent.name if detail.dimension.parent else None,

                    # Order and positioning
                    'dimension_order': detail.dimension_order,
                    'field_level': detail.field.field_level,
                    'field_name': detail.field.name,

                    # Value metadata (will be populated from prefetched data)
                    'value_count': 0,
                    'has_active_values': False,
                }

                # Count active values from prefetched data
                active_values = [v for v in detail.dimension.dimension_values.all(
                ) if getattr(v, 'is_active', True)]
                dimensions[dimension]['value_count'] = len(active_values)
                dimensions[dimension]['has_active_values'] = len(
                    active_values) > 0

        return dimensions

    def _build_dimension_values(self, dimensions: Set[int], rule: Rule = None) -> Dict:
        """Build optimized dimension values lookup"""
        if not dimensions:
            return {}

        # Get all dimension values for the dimensions we need, filtered by workspace
        query = DimensionValue.objects.filter(dimension_id__in=dimensions)
        if rule and rule.workspace:
            query = query.filter(workspace=rule.workspace)

        dimension_values = query.select_related('dimension')

        values_map = {}
        for value in dimension_values:
            dim = value.dimension.id
            if dim not in values_map:
                values_map[dim] = []

            values_map[dim].append({
                'id': value.id,
                'value': value.value,
                'label': value.label or value.value,
                'utm': getattr(value, 'utm', ''),
                'description': value.description or '',
                'is_active': getattr(value, 'is_active', True),
                'order': getattr(value, 'order', 0),
            })

        # Sort values within each dimension
        for dim in values_map:
            values_map[dim].sort(key=lambda x: (x['order'], x['label']))

        return values_map

    def _build_constraint_relationships(self, rule_details: QuerySet) -> Dict:
        """Build constraint relationships between dimensions"""
        relationships = {
            'parent_child': {},
            'field_dependencies': {},
            'inheritance_matrix': {}
        }

        # Build parent-child relationships
        for detail in rule_details:
            if detail.dimension.parent:
                parent = detail.dimension.parent
                child = detail.dimension.id

                if parent not in relationships['parent_child']:
                    relationships['parent_child'][parent] = []

                if child not in relationships['parent_child'][parent]:
                    relationships['parent_child'][parent].append(child)

        # Build field dependencies (which dimensions are used in which fields)
        for detail in rule_details:
            field_level = detail.field.field_level
            dim = detail.dimension.id

            if field_level not in relationships['field_dependencies']:
                relationships['field_dependencies'][field_level] = []

            if dim not in relationships['field_dependencies'][field_level]:
                relationships['field_dependencies'][field_level].append(dim)

        return relationships

    def _build_field_templates(self, rule_details: QuerySet) -> List[Dict]:
        """Build field templates for easier frontend consumption"""
        fields_map = {}

        for detail in rule_details:
            field = detail.field.id

            if field not in fields_map:
                fields_map[field] = {
                    'field': field,
                    'field_name': detail.field.name,
                    'field_level': detail.field.field_level,
                    'next_field': getattr(detail.field, 'next_field', None),
                    'next_field_name': getattr(detail.field, 'next_field', None).name if getattr(detail.field, 'next_field', None) else None,
                    'dimensions': [],
                    'dimension_count': 0,
                    'required_dimension_count': 0,
                }

            # Add dimension info
            dim_info = {
                'dimension': detail.dimension.id,
                'dimension_name': detail.dimension.name,
                'dimension_type': detail.dimension.type,
                'dimension_order': detail.dimension_order,
                'is_required': getattr(detail, 'is_required', True),
                'prefix': detail.prefix or '',
                'suffix': detail.suffix or '',
                'delimiter': detail.delimiter or '',
                'effective_delimiter': detail.get_effective_delimiter() if hasattr(detail, 'get_effective_delimiter') else (detail.delimiter or ''),
            }

            fields_map[field]['dimensions'].append(dim_info)

        # Process each field to add computed information
        for field_data in fields_map.values():
            # Sort dimensions by order
            field_data['dimensions'].sort(key=lambda x: x['dimension_order'])

            # Update counts
            field_data['dimension_count'] = len(field_data['dimensions'])
            field_data['required_dimension_count'] = sum(
                1 for d in field_data['dimensions'] if d['is_required']
            )

            # Generate field rule preview
            preview_parts = []
            for dim in field_data['dimensions']:
                part = (dim['prefix'] +
                        f"[{dim['dimension_name']}]" +
                        dim['suffix'] +
                        dim['delimiter'])
                preview_parts.append(part)

            field_data['field_rule_preview'] = ''.join(preview_parts)

        # Convert to list and sort by field level
        result = list(fields_map.values())
        result.sort(key=lambda x: x['field_level'])

        return result

    def invalidate_cache(self, rule: int):
        """Invalidate cache for a specific rule"""
        cache_key = f"dimension_catalog:{rule}"
        cache.delete(cache_key)

        # Also mark model cache as needing refresh if the field exists
        try:
            rule = Rule.objects.get(id=rule)
            if hasattr(rule, 'needs_inheritance_refresh'):
                rule.needs_inheritance_refresh = True
                rule.save(update_fields=['needs_inheritance_refresh'])
        except Rule.DoesNotExist:
            pass

    def bulk_invalidate_cache(self, rule_ids: List[int]):
        """Invalidate cache for multiple rules"""
        for rule in rule_ids:
            self.invalidate_cache(rule)

    def get_optimized_catalog_for_rule(self, rule: int) -> Dict:
        """
        Get optimized dimension catalog with centralized data and improved structure.
        Implements key improvements: centralized values, simplified inheritance, better constraints.
        """
        cache_key = f"optimized_dimension_catalog:{rule}"
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            return cached_result

        try:
            rule = Rule.objects.select_related('platform').get(id=rule)
        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule} does not exist")

        catalog = self._build_optimized_catalog(rule)

        # Cache for 30 minutes
        cache.set(cache_key, catalog, self.cache_timeout)
        return catalog

    def _build_optimized_catalog(self, rule: Rule) -> Dict:
        """Build optimized catalog with centralized data and improved structure"""
        rule_details = RuleDetail.objects.filter(rule=rule).select_related(
            'field', 'dimension', 'dimension__parent'
        ).prefetch_related(
            'dimension__dimension_values'
        ).order_by('field__field_level', 'dimension_order')

        # Get all unique dimensions
        dimensions = set(detail.dimension.id for detail in rule_details)

        # Build centralized components
        dimensions = self._build_centralized_dimensions(
            rule_details, dimensions)
        dimension_values = self._build_centralized_dimension_values(
            dimensions, rule)
        constraints = self._build_optimized_constraints(rule_details)
        inheritance_lookup = self._build_inheritance_lookup(rule_details, rule)

        # Build fast relationship maps
        relationship_maps = self._build_dimension_relationship_maps(
            rule_details)

        # Build metadata indexes
        metadata_indexes = self._build_metadata_indexes(
            rule_details, dimensions)

        return {
            'rule': rule.id,
            'rule_name': rule.name,
            'rule_slug': rule.slug,
            'dimensions': dimensions,
            'dimension_values': dimension_values,
            'constraints': constraints,
            'inheritance_lookup': inheritance_lookup,
            'relationship_maps': relationship_maps,
            'metadata_indexes': metadata_indexes,
            'generated_at': timezone.now().isoformat(),
        }

    def _build_centralized_dimensions(self, rule_details: QuerySet, dimensions: Set[int]) -> Dict:
        """Build centralized dimension definitions"""
        dimensions = {}

        for detail in rule_details:
            dimension = detail.dimension.id

            if dimension not in dimensions:
                dimensions[dimension] = {
                    'id': dimension,
                    'name': detail.dimension.name,
                    'type': detail.dimension.type,
                    'description': detail.dimension.description or '',

                    # Default formatting rules (can be overridden in field templates)
                    'default_prefix': getattr(detail.dimension, 'default_prefix', ''),
                    'default_suffix': getattr(detail.dimension, 'default_suffix', ''),
                    'default_delimiter': getattr(detail.dimension, 'default_delimiter', ''),

                    # Behavior flags
                    'allows_freetext': detail.dimension.type == 'text',
                    'is_dropdown': detail.dimension.type in ['list', 'combobox'],

                    # Constraint metadata
                    'has_parent_constraint': bool(detail.dimension.parent),
                    # Store ID instead of object
                    'parent_dimension': detail.dimension.parent.id if detail.dimension.parent else None,
                    'parent_dimension_name': detail.dimension.parent.name if detail.dimension.parent else None,

                    # Value metadata
                    'value_count': detail.dimension.dimension_values.count(),
                    'has_active_values': detail.dimension.dimension_values.filter(
                        **({'is_active': True} if hasattr(detail.dimension.dimension_values.model, 'is_active') else {})
                    ).exists(),
                }

        return dimensions

    def _build_centralized_dimension_values(self, dimensions: Set[int], rule: Rule = None) -> Dict:
        """Build centralized dimension values lookup with parent-child relationships"""
        if not dimensions:
            return {}

        # Get dimension values filtered by workspace
        query = DimensionValue.objects.filter(dimension_id__in=dimensions)
        if rule and rule.workspace:
            query = query.filter(workspace=rule.workspace)

        dimension_values = query.select_related(
            'dimension', 'parent', 'parent__dimension')

        values_map = {}
        for value in dimension_values:
            dim = value.dimension_id
            if dim not in values_map:
                values_map[dim] = []

            # Build parent relationship data
            parent_data = None
            if value.parent:
                parent_data = {
                    'parent': value.parent.id,  # Store ID instead of object
                    'parent_value': value.parent.value,
                    'parent_label': value.parent.label,
                    'parent_dimension': value.parent.dimension.id,  # Store ID instead of object
                    'parent_dimension_name': value.parent.dimension.name,
                }

            values_map[dim].append({
                'id': value.id,
                'value': value.value,
                'label': value.label or value.value,
                'utm': getattr(value, 'utm', ''),
                'description': value.description or '',
                'is_active': getattr(value, 'is_active', True),
                'order': getattr(value, 'order', 0),

                # Parent-child relationship data
                'parent': parent_data,
                'has_parent': value.parent is not None,

                # For backward compatibility and easier access
                'parent': value.parent.id if value.parent else None,  # Store ID instead of object
                'parent_value': value.parent.value if value.parent else None,
                'parent_label': value.parent.label if value.parent else None,
                # Store ID instead of object
                'parent_dimension': value.parent.dimension.id if value.parent else None,
                'parent_dimension_name': value.parent.dimension.name if value.parent else None,
            })

        # Sort values within each dimension
        for dim in values_map:
            values_map[dim].sort(key=lambda x: (x['order'], x['label']))

        return values_map

    def _build_optimized_constraints(self, rule_details: QuerySet) -> Dict:
        """Build optimized constraint structure with arrays and pre-computed lookups"""
        constraints = {
            'parent_child_constraints': [],
            'field_level_constraints': {},
            'value_constraints': {},

            # Fast lookup tables
            'parent_to_children_map': {},
            'child_to_parent_map': {},
            'constraint_coverage_map': {},
            'validation_lookup': {},

            # Statistics
            'constraint_stats': {}
        }

        # Build parent-child constraint arrays
        parent_child_map = {}
        for detail in rule_details:
            if detail.dimension.parent:
                parent_id = detail.dimension.parent.id  # Store ID instead of object
                child_id = detail.dimension.id

                constraint_key = f"{parent_id}_{child_id}"
                if constraint_key not in parent_child_map:
                    constraints['parent_child_constraints'].append({
                        'parent_dimension': parent_id,
                        'child_dimension': child_id,
                        'parent_dimension_name': detail.dimension.parent.name,
                        'child_dimension_name': detail.dimension.name,
                        'constraint_type': 'parent_child'
                    })
                    parent_child_map[constraint_key] = True

        # Build field-level constraints
        for detail in rule_details:
            field_level = detail.field.field_level
            dim = detail.dimension.id

            if field_level not in constraints['field_level_constraints']:
                constraints['field_level_constraints'][field_level] = {
                    'field': detail.field.id,
                    'field_name': detail.field.name,
                    'required_dimensions': [],
                    'optional_dimensions': []
                }

            dim_info = {
                'dimension': detail.dimension.id,
                'dimension_name': detail.dimension.name,
                'dimension_order': detail.dimension_order
            }

            is_required = getattr(detail, 'is_required', True)
            if is_required:
                constraints['field_level_constraints'][field_level]['required_dimensions'].append(
                    dim_info)
            else:
                constraints['field_level_constraints'][field_level]['optional_dimensions'].append(
                    dim_info)

        # Build value constraints with actual parent-child value mappings
        self._build_value_level_constraints(constraints, rule_details)

        # Build fast lookup tables
        self._build_constraint_lookup_tables(constraints, rule_details)

        return constraints

    def _build_value_level_constraints(self, constraints: Dict, rule_details: QuerySet):
        """Build value-level parent-child constraint mappings"""
        from ..models import DimensionValue

        # Get all dimensions that have parent relationships
        parent_child_dimensions = {}
        for detail in rule_details:
            if detail.dimension.parent:
                parent = detail.dimension.parent.id  # Store ID instead of object
                child = detail.dimension.id
                parent_child_dimensions[child] = parent

        if not parent_child_dimensions:
            return

        # Get dimension values for involved dimensions
        all_involved_dims = set(parent_child_dimensions.keys()) | set(
            parent_child_dimensions.values())

        # Filter by workspace context if available (get from rule_details)
        query = DimensionValue.objects.filter(dimension__in=all_involved_dims)
        if rule_details and rule_details.exists():
            # Get workspace from first rule detail
            workspace = rule_details.first().workspace
            query = query.filter(workspace=workspace)

        dimension_values = query.select_related('dimension', 'parent')

        # Build parent-to-children value mappings
        for child_dim, parent_dim in parent_child_dimensions.items():
            if parent_dim not in constraints['value_constraints']:
                constraints['value_constraints'][parent_dim] = {}

            # Get actual value mappings
            child_values = [
                v for v in dimension_values if v.dimension == child_dim]
            parent_values = [
                v for v in dimension_values if v.dimension == parent_dim]

            # Build value cascade mapping
            value_mappings = {}
            parent_to_children = {}

            for child_value in child_values:
                if child_value.parent:
                    parent_value_id = child_value.parent.id  # Use ID as key instead of object
                    if parent_value_id not in parent_to_children:
                        parent_to_children[parent_value_id] = []
                    parent_to_children[parent_value_id].append({
                        'child_value_id': child_value.id,
                        'child_value': child_value.value,
                        'child_label': child_value.label
                    })

            # Build reverse mapping (child to parent)
            child_to_parent = {}
            for child_value in child_values:
                if child_value.parent:
                    parent_value = next(
                        (v for v in parent_values if v == child_value.parent), None)
                    if parent_value:
                        child_to_parent[child_value.id] = {  # Use ID as key instead of object
                            'parent_value': parent_value.id,  # Store ID instead of object
                            'parent_value_value': parent_value.value,
                            'parent_value_label': parent_value.label,
                            'parent_value_dimension': parent_value.dimension.id  # Store ID instead of object
                        }

            constraints['value_constraints'][parent_dim][child_dim] = {
                'constraint_type': 'value_cascade',
                'parent_dimension': parent_dim,
                'child_dimension': child_dim,
                'parent_to_children_values': parent_to_children,
                'child_to_parent_values': child_to_parent,
                'total_parent_values': len(parent_values),
                'total_child_values': len(child_values),
                'constrained_child_values': len([v for v in child_values if v.parent]),
                'cascade_coverage': (len([v for v in child_values if v.parent]) / len(child_values) * 100) if child_values else 0.0
            }

    def _build_constraint_lookup_tables(self, constraints: Dict, rule_details: QuerySet):
        """Build fast constraint lookup tables for O(1) access"""

        # 1. Parent-to-children mapping
        for constraint in constraints['parent_child_constraints']:
            parent = constraint['parent_dimension']
            child = constraint['child_dimension']

            if parent not in constraints['parent_to_children_map']:
                constraints['parent_to_children_map'][parent] = {
                    'parent_dimension': parent,
                    'parent_dimension_name': constraint['parent_dimension_name'],
                    'child_dimensions': [],
                    'child_count': 0
                }

            constraints['parent_to_children_map'][parent]['child_dimensions'].append({
                'child_dimension': child,
                'child_dimension_name': constraint['child_dimension_name'],
                'constraint_type': constraint['constraint_type']
            })

        # 2. Child-to-parent mapping
        for constraint in constraints['parent_child_constraints']:
            parent = constraint['parent_dimension']
            child = constraint['child_dimension']

            constraints['child_to_parent_map'][child] = {
                'child_dimension': child,
                'child_dimension_name': constraint['child_dimension_name'],
                'parent_dimension': parent,
                'parent_dimension_name': constraint['parent_dimension_name'],
                'constraint_type': constraint['constraint_type']
            }

        # Update counts
        for parent_data in constraints['parent_to_children_map'].values():
            parent_data['child_count'] = len(parent_data['child_dimensions'])

        # 3. Constraint coverage mapping
        all_dimensions = set()
        constrained_dimensions = set()

        for detail in rule_details:
            all_dimensions.add(detail.dimension.id)
            if detail.dimension.parent:
                constrained_dimensions.add(detail.dimension.id)

        for dimension in all_dimensions:
            has_parent_constraint = dimension in constrained_dimensions
            provides_child_constraint = dimension in constraints['parent_to_children_map']

            constraints['constraint_coverage_map'][dimension] = {
                'dimension': dimension,
                'has_parent_constraint': has_parent_constraint,
                'provides_child_constraint': provides_child_constraint,
                'constraint_level': 'both' if has_parent_constraint and provides_child_constraint else
                'child' if has_parent_constraint else
                'parent' if provides_child_constraint else 'none'
            }

        # 4. Validation lookup for quick constraint checks
        for detail in rule_details:
            field_level = detail.field.field_level
            dimension = detail.dimension.id

            validation_key = f"{field_level}_{dimension}"
            constraints['validation_lookup'][validation_key] = {
                'field_level': field_level,
                'dimension': dimension,
                'has_constraints': dimension in constrained_dimensions,
                # Store ID instead of object
                'parent_dimension': detail.dimension.parent.id if detail.dimension.parent else None,
                'validation_required': bool(detail.dimension.parent),
                'quick_check': {
                    'is_constrained': dimension in constrained_dimensions,
                    # Store ID instead of object
                    'parent': detail.dimension.parent.id if detail.dimension.parent else None,
                    'constraint_type': 'parent_child' if detail.dimension.parent else 'none'
                }
            }

        # 5. Calculate constraint statistics
        total_dimensions = len(all_dimensions)
        constrained_count = len(constrained_dimensions)
        parent_dimensions = len(constraints['parent_to_children_map'])

        constraints['constraint_stats'] = {
            'total_dimensions': total_dimensions,
            'constrained_dimensions': constrained_count,
            'parent_dimensions': parent_dimensions,
            'constraint_coverage': (constrained_count / total_dimensions * 100) if total_dimensions > 0 else 0.0,
            'constraint_density': (len(constraints['parent_child_constraints']) / total_dimensions) if total_dimensions > 0 else 0.0,
            'dimensions_by_constraint_level': {
                'none': len([d for d in constraints['constraint_coverage_map'].values() if d['constraint_level'] == 'none']),
                'child': len([d for d in constraints['constraint_coverage_map'].values() if d['constraint_level'] == 'child']),
                'parent': len([d for d in constraints['constraint_coverage_map'].values() if d['constraint_level'] == 'parent']),
                'both': len([d for d in constraints['constraint_coverage_map'].values() if d['constraint_level'] == 'both'])
            }
        }

    def _build_inheritance_lookup(self, rule_details: QuerySet, rule: Rule) -> Dict:
        """Build comprehensive inheritance lookup tables for O(1) access"""
        lookup = {
            # Fast lookups by dimension ID
            'by_dimension': {},

            # Fast lookups by field levels
            'by_target_field_level': {},
            'by_source_field_level': {},

            # Reverse lookups
            'inherits_from_dimension': {},
            'provides_inheritance_to': {},

            # Quick access maps
            'inherited_dimensions': set(),
            'source_dimensions': set(),

        }

        # Build primary inheritance data
        dimension_inheritance_map = {}
        for detail in rule_details:
            dimension = detail.dimension.id
            current_field_level = detail.field.field_level

            # Check for inheritance from previous field levels
            parent_detail = RuleDetail.objects.filter(
                rule=rule,
                dimension=detail.dimension,
                field__field_level__lt=current_field_level
            ).select_related('field').order_by('-field__field_level').first()

            inheritance_chain = []
            field_level_inherited_from = None
            inherits_formatting = False

            if parent_detail:
                field_level_inherited_from = parent_detail.field.field_level
                inherits_formatting = self._check_formatting_inheritance(
                    detail, parent_detail)
                inheritance_chain = self._build_inheritance_chain(
                    rule, detail.dimension, current_field_level)

            dimension_inheritance_map[dimension] = {
                'dimension': dimension,
                'current_field_level': current_field_level,
                'field_level_inherited_from': field_level_inherited_from,
                'inherits_formatting': inherits_formatting,
                'inheritance_chain': inheritance_chain,
                'is_inherited': field_level_inherited_from is not None,
                'is_source': False  # Will be updated below
            }

        # Build fast lookup tables
        self._build_fast_inheritance_lookups(lookup, dimension_inheritance_map)

        return lookup

    def _build_fast_inheritance_lookups(self, lookup: Dict, inheritance_map: Dict):
        """Build O(1) inheritance lookup tables"""

        # 1. By Dimension ID lookup
        for dim, data in inheritance_map.items():
            lookup['by_dimension'][dim] = {
                'dimension': dim,
                'current_field_level': data['current_field_level'],
                'inherits_from_field_level': data['field_level_inherited_from'],
                'inherits_formatting': data['inherits_formatting'],
                'inheritance_chain': data['inheritance_chain'],
                'is_inherited': data['is_inherited']
            }

            if data['is_inherited']:
                lookup['inherited_dimensions'].add(dim)

        # 2. By Target Field Level (what each field level inherits)
        for dim, data in inheritance_map.items():
            target_level = data['current_field_level']
            if target_level not in lookup['by_target_field_level']:
                lookup['by_target_field_level'][target_level] = {
                    'field_level': target_level,
                    'inherited_dimensions': [],
                    'non_inherited_dimensions': [],
                    'inheritance_sources': {}
                }

            if data['is_inherited']:
                lookup['by_target_field_level'][target_level]['inherited_dimensions'].append({
                    'dimension': dim,
                    'inherits_from_field_level': data['field_level_inherited_from'],
                    'inherits_formatting': data['inherits_formatting']
                })

                # Track inheritance sources
                source_level = data['field_level_inherited_from']
                if source_level not in lookup['by_target_field_level'][target_level]['inheritance_sources']:
                    lookup['by_target_field_level'][target_level]['inheritance_sources'][source_level] = [
                    ]
                lookup['by_target_field_level'][target_level]['inheritance_sources'][source_level].append(
                    dim)
            else:
                lookup['by_target_field_level'][target_level]['non_inherited_dimensions'].append(
                    dim)

        # 3. By Source Field Level (what each field level provides)
        for dim, data in inheritance_map.items():
            if data['field_level_inherited_from'] is not None:
                source_level = data['field_level_inherited_from']
                if source_level not in lookup['by_source_field_level']:
                    lookup['by_source_field_level'][source_level] = {
                        'field_level': source_level,
                        'provides_inheritance_to': [],
                        'target_field_levels': set()
                    }

                lookup['by_source_field_level'][source_level]['provides_inheritance_to'].append({
                    'dimension': dim,
                    'target_field_level': data['current_field_level'],
                    'inherits_formatting': data['inherits_formatting']
                })
                lookup['by_source_field_level'][source_level]['target_field_levels'].add(
                    data['current_field_level'])

                # Update source dimensions
                lookup['source_dimensions'].add(dim)
                inheritance_map[dim]['is_source'] = True

        # 4. Reverse Lookups - Inherits From Dimension
        for dim, data in inheritance_map.items():
            if data['is_inherited']:
                source_level = data['field_level_inherited_from']

                # Find the source dimension at the source field level
                for source_dim, source_data in inheritance_map.items():
                    if (source_data['current_field_level'] == source_level and
                            source_dim == dim):  # Same dimension at different levels

                        if source_dim not in lookup['inherits_from_dimension']:
                            lookup['inherits_from_dimension'][source_dim] = []

                        lookup['inherits_from_dimension'][source_dim].append({
                            'target_dimension': dim,
                            'target_field_level': data['current_field_level'],
                            'inherits_formatting': data['inherits_formatting']
                        })

        # 5. Reverse Lookups - Provides Inheritance To
        for source_dim, targets in lookup['inherits_from_dimension'].items():
            lookup['provides_inheritance_to'][source_dim] = targets

        # 6. Convert sets to lists for JSON serialization
        lookup['inherited_dimensions'] = list(lookup['inherited_dimensions'])
        lookup['source_dimensions'] = list(lookup['source_dimensions'])

        # Convert target_field_levels sets to lists
        for source_level_data in lookup['by_source_field_level'].values():
            source_level_data['target_field_levels'] = list(
                source_level_data['target_field_levels'])

        # 7. Calculate statistics
        total_dimensions = len(inheritance_map)
        inherited_count = len(lookup['inherited_dimensions'])
        source_count = len(lookup['source_dimensions'])

        lookup['inheritance_stats'] = {
            'total_dimensions': total_dimensions,
            'inherited_count': inherited_count,
            'source_count': source_count,
            'inheritance_coverage': (inherited_count / total_dimensions * 100) if total_dimensions > 0 else 0.0,
            'field_levels_with_inheritance': list(lookup['by_target_field_level'].keys()),
            'field_levels_providing_inheritance': list(lookup['by_source_field_level'].keys())
        }

    def _build_inheritance_chain(self, rule: Rule, dimension: Dimension, current_field_level: int) -> List[int]:
        """Build the inheritance chain for a dimension up to the current field level"""
        chain = []

        # Get all rule details for this dimension in previous field levels
        previous_details = RuleDetail.objects.filter(
            rule=rule,
            dimension=dimension,
            field__field_level__lt=current_field_level
        ).select_related('field').order_by('field__field_level')

        for detail in previous_details:
            chain.append(detail.field.field_level)

        return chain

    def _check_formatting_inheritance(self, child_detail: RuleDetail, parent_detail: RuleDetail) -> bool:
        """Check if formatting rules are inherited from parent"""
        return (
            (child_detail.prefix or '') == (parent_detail.prefix or '') and
            (child_detail.suffix or '') == (parent_detail.suffix or '') and
            (child_detail.delimiter or '') == (parent_detail.delimiter or '')
        )

    def _build_dimension_relationship_maps(self, rule_details: QuerySet) -> Dict:
        """Build O(1) dimension relationship lookup maps"""
        maps = {
            # Field-to-Dimensions mappings
            'field_to_dimensions': {},
            'field_to_required_dimensions': {},
            'field_to_optional_dimensions': {},

            # Dimension-to-Fields mappings (reverse)
            'dimension_to_fields': {},
            'dimension_to_required_fields': {},
            'dimension_to_optional_fields': {},

            # Quick access arrays
            'field_levels': [],
            'all_dimensions': [],
            'required_dimensions': [],
            'optional_dimensions': [],

            # Statistics
            'relationship_stats': {}
        }

        # Build primary mappings
        field_dimension_map = {}
        dimension_field_map = {}

        for detail in rule_details:
            field_level = detail.field.field_level
            field = detail.field.id
            field_name = detail.field.name
            dimension = detail.dimension.id
            dimension_name = detail.dimension.name
            is_required = getattr(detail, 'is_required', True)

            # Build field-to-dimensions mapping
            if field_level not in field_dimension_map:
                field_dimension_map[field_level] = {
                    'field': field,
                    'field_name': field_name,
                    'field_level': field_level,
                    'all_dimensions': [],
                    'required_dimensions': [],
                    'optional_dimensions': [],
                    'dimension_count': 0,
                    'required_count': 0,
                    'optional_count': 0
                }

            dimension_info = {
                'dimension': dimension,
                'dimension_name': dimension_name,
                'dimension_order': detail.dimension_order,
                'is_required': is_required
            }

            field_dimension_map[field_level]['all_dimensions'].append(
                dimension_info)
            if is_required:
                field_dimension_map[field_level]['required_dimensions'].append(
                    dimension_info)
            else:
                field_dimension_map[field_level]['optional_dimensions'].append(
                    dimension_info)

            # Build dimension-to-fields mapping
            if dimension not in dimension_field_map:
                dimension_field_map[dimension] = {
                    'dimension': dimension,
                    'dimension_name': dimension_name,
                    'used_in_fields': [],
                    'required_in_fields': [],
                    'optional_in_fields': [],
                    'field_count': 0,
                    'required_field_count': 0,
                    'optional_field_count': 0
                }

            field_info = {
                'field': field,
                'field_name': field_name,
                'field_level': field_level,
                'dimension_order': detail.dimension_order,
                'is_required': is_required
            }

            dimension_field_map[dimension]['used_in_fields'].append(
                field_info)
            if is_required:
                dimension_field_map[dimension]['required_in_fields'].append(
                    field_info)
            else:
                dimension_field_map[dimension]['optional_in_fields'].append(
                    field_info)

        # Populate fast lookup maps
        self._populate_relationship_maps(
            maps, field_dimension_map, dimension_field_map)

        return maps

    def _populate_relationship_maps(self, maps: Dict, field_dimension_map: Dict, dimension_field_map: Dict):
        """Populate the relationship maps with computed data"""

        # 1. Field-to-Dimensions mappings
        for field_level, field_data in field_dimension_map.items():
            # Update counts
            field_data['dimension_count'] = len(field_data['all_dimensions'])
            field_data['required_count'] = len(
                field_data['required_dimensions'])
            field_data['optional_count'] = len(
                field_data['optional_dimensions'])

            # Store in maps
            maps['field_to_dimensions'][field_level] = field_data
            maps['field_to_required_dimensions'][field_level] = {
                'field_level': field_level,
                'field_name': field_data['field_name'],
                'required_dimensions': field_data['required_dimensions'],
                'count': field_data['required_count']
            }
            maps['field_to_optional_dimensions'][field_level] = {
                'field_level': field_level,
                'field_name': field_data['field_name'],
                'optional_dimensions': field_data['optional_dimensions'],
                'count': field_data['optional_count']
            }

        # 2. Dimension-to-Fields mappings
        for dimension, dimension_data in dimension_field_map.items():
            # Update counts
            dimension_data['field_count'] = len(
                dimension_data['used_in_fields'])
            dimension_data['required_field_count'] = len(
                dimension_data['required_in_fields'])
            dimension_data['optional_field_count'] = len(
                dimension_data['optional_in_fields'])

            # Store in maps
            maps['dimension_to_fields'][dimension] = dimension_data
            maps['dimension_to_required_fields'][dimension] = {
                'dimension': dimension,
                'dimension_name': dimension_data['dimension_name'],
                'required_in_fields': dimension_data['required_in_fields'],
                'count': dimension_data['required_field_count']
            }
            maps['dimension_to_optional_fields'][dimension] = {
                'dimension': dimension,
                'dimension_name': dimension_data['dimension_name'],
                'optional_in_fields': dimension_data['optional_in_fields'],
                'count': dimension_data['optional_field_count']
            }

        # 3. Quick access arrays
        maps['field_levels'] = sorted(field_dimension_map.keys())
        maps['all_dimensions'] = list(dimension_field_map.keys())

        # Required/Optional dimension lists
        for dimension, dimension_data in dimension_field_map.items():
            if dimension_data['required_field_count'] > 0:
                maps['required_dimensions'].append(dimension)
            if dimension_data['optional_field_count'] > 0:
                maps['optional_dimensions'].append(dimension)

        # 4. Calculate statistics
        total_field_levels = len(field_dimension_map)
        total_dimensions = len(dimension_field_map)
        total_required_dimensions = len(maps['required_dimensions'])
        total_optional_dimensions = len(maps['optional_dimensions'])

        maps['relationship_stats'] = {
            'total_field_levels': total_field_levels,
            'total_dimensions': total_dimensions,
            'required_dimensions_count': total_required_dimensions,
            'optional_dimensions_count': total_optional_dimensions,
            'avg_dimensions_per_field': total_dimensions / total_field_levels if total_field_levels > 0 else 0,
            'fields_with_required_only': sum(1 for f in field_dimension_map.values() if f['required_count'] > 0 and f['optional_count'] == 0),
            'fields_with_optional_only': sum(1 for f in field_dimension_map.values() if f['optional_count'] > 0 and f['required_count'] == 0),
            'fields_with_mixed': sum(1 for f in field_dimension_map.values() if f['required_count'] > 0 and f['optional_count'] > 0)
        }

    def _build_metadata_indexes(self, rule_details: QuerySet, dimensions: Dict) -> Dict:
        """Build fast metadata indexes for O(1) access to dimension properties"""
        indexes = {
            # Type-based groupings
            'dimension_type_groups': {
                'text': [],
                'list': [],
                'combobox': [],
                'all_types': []
            },

            # Formatting rule indexes
            'formatting_patterns': {},
            'delimiter_groups': {},
            'prefix_groups': {},
            'suffix_groups': {},

            # Validation flag indexes
            'validation_flags': {
                'required_dimensions': [],
                'optional_dimensions': [],
                'constrained_dimensions': [],
                'freetext_dimensions': [],
                'dropdown_dimensions': []
            },

            # Quick access indexes
            'dimension_to_type': {},
            'dimension_to_name': {},
            'dimension_name_to_id': {},
            'field_level_to_dimensions': {},
            'dimension_order_index': {},

            # Performance indexes
            'fast_lookups': {
                'by_dimension_id': {},
                'by_field_level': {},
                'by_dimension_type': {},
                'by_requirement_status': {},
                'by_constraint_status': {}
            },

            # Statistics
            'metadata_stats': {}
        }

        # Build primary data maps
        dimension_metadata = {}
        field_metadata = {}

        for detail in rule_details:
            dimension = detail.dimension.id
            dimension_name = detail.dimension.name
            dimension_type = detail.dimension.type
            field_level = detail.field.field_level
            is_required = getattr(detail, 'is_required', True)

            # Build dimension metadata
            if dimension not in dimension_metadata:
                dimension_metadata[dimension] = {
                    'dimension': dimension,
                    'dimension_name': dimension_name,
                    'dimension_type': dimension_type,
                    'allows_freetext': dimension_type == 'text',
                    'is_dropdown': dimension_type in ['list', 'combobox'],
                    'has_parent_constraint': bool(detail.dimension.parent),
                    'used_in_field_levels': [],
                    'formatting_patterns': [],
                    'is_required_anywhere': False,
                    'is_optional_anywhere': False
                }

            dimension_metadata[dimension]['used_in_field_levels'].append(
                field_level)

            # Track requirement status
            if is_required:
                dimension_metadata[dimension]['is_required_anywhere'] = True
            else:
                dimension_metadata[dimension]['is_optional_anywhere'] = True

            # Build formatting pattern
            formatting_pattern = {
                'field_level': field_level,
                'prefix': detail.prefix or '',
                'suffix': detail.suffix or '',
                'delimiter': detail.delimiter or '',
                'effective_delimiter': detail.get_effective_delimiter() if hasattr(detail, 'get_effective_delimiter') else (detail.delimiter or '')
            }
            dimension_metadata[dimension]['formatting_patterns'].append(
                formatting_pattern)

            # Build field metadata
            if field_level not in field_metadata:
                field_metadata[field_level] = {
                    'field_level': field_level,
                    'field_name': detail.field.name,
                    'dimensions': [],
                    'dimension_types': set(),
                    'has_required_dimensions': False,
                    'has_optional_dimensions': False,
                    'has_constrained_dimensions': False
                }

            field_metadata[field_level]['dimensions'].append(dimension)
            field_metadata[field_level]['dimension_types'].add(dimension_type)

            if is_required:
                field_metadata[field_level]['has_required_dimensions'] = True
            else:
                field_metadata[field_level]['has_optional_dimensions'] = True

            if detail.dimension.parent:
                field_metadata[field_level]['has_constrained_dimensions'] = True

        # Populate indexes
        self._populate_metadata_indexes(
            indexes, dimension_metadata, field_metadata)

        return indexes

    def _populate_metadata_indexes(self, indexes: Dict, dimension_metadata: Dict, field_metadata: Dict):
        """Populate the metadata indexes with computed data"""

        # 1. Dimension type groups
        for dim, dim_data in dimension_metadata.items():
            dim_type = dim_data['dimension_type']
            indexes['dimension_type_groups']['all_types'].append(dim)

            if dim_type in indexes['dimension_type_groups']:
                indexes['dimension_type_groups'][dim_type].append(dim)

            # Type mapping
            indexes['dimension_to_type'][dim] = dim_type
            indexes['dimension_to_name'][dim] = dim_data['dimension_name']
            indexes['dimension_name_to_id'][dim_data['dimension_name']] = dim

        # 2. Formatting pattern indexes
        for dim, dim_data in dimension_metadata.items():
            for pattern in dim_data['formatting_patterns']:
                # Group by delimiter
                delimiter = pattern['delimiter']
                if delimiter not in indexes['delimiter_groups']:
                    indexes['delimiter_groups'][delimiter] = []
                indexes['delimiter_groups'][delimiter].append(dim)

                # Group by prefix
                prefix = pattern['prefix']
                if prefix not in indexes['prefix_groups']:
                    indexes['prefix_groups'][prefix] = []
                indexes['prefix_groups'][prefix].append(dim)

                # Group by suffix
                suffix = pattern['suffix']
                if suffix not in indexes['suffix_groups']:
                    indexes['suffix_groups'][suffix] = []
                indexes['suffix_groups'][suffix].append(dim)

                # Create formatting pattern key
                pattern_key = f"{prefix}|{suffix}|{delimiter}"
                if pattern_key not in indexes['formatting_patterns']:
                    indexes['formatting_patterns'][pattern_key] = {
                        'pattern': pattern_key,
                        'prefix': prefix,
                        'suffix': suffix,
                        'delimiter': delimiter,
                        'dimensions': []
                    }
                indexes['formatting_patterns'][pattern_key]['dimensions'].append(
                    dim)

        # 3. Validation flag indexes
        for dim, dim_data in dimension_metadata.items():
            if dim_data['is_required_anywhere']:
                indexes['validation_flags']['required_dimensions'].append(
                    dim)
            if dim_data['is_optional_anywhere']:
                indexes['validation_flags']['optional_dimensions'].append(
                    dim)
            if dim_data['has_parent_constraint']:
                indexes['validation_flags']['constrained_dimensions'].append(
                    dim)
            if dim_data['allows_freetext']:
                indexes['validation_flags']['freetext_dimensions'].append(
                    dim)
            if dim_data['is_dropdown']:
                indexes['validation_flags']['dropdown_dimensions'].append(
                    dim)

        # 4. Field level to dimensions mapping
        for field_level, field_data in field_metadata.items():
            field_data['dimension_types'] = list(
                field_data['dimension_types'])  # Convert set to list
            indexes['field_level_to_dimensions'][field_level] = field_data

        # 5. Fast lookup indexes
        for dim, dim_data in dimension_metadata.items():
            indexes['fast_lookups']['by_dimension_id'][dim] = {
                'dimension': dim,
                'name': dim_data['dimension_name'],
                'type': dim_data['dimension_type'],
                'allows_freetext': dim_data['allows_freetext'],
                'is_dropdown': dim_data['is_dropdown'],
                'has_constraints': dim_data['has_parent_constraint'],
                'used_in_fields': dim_data['used_in_field_levels'],
                'is_required_anywhere': dim_data['is_required_anywhere'],
                'is_optional_anywhere': dim_data['is_optional_anywhere']
            }

            # By dimension type
            dim_type = dim_data['dimension_type']
            if dim_type not in indexes['fast_lookups']['by_dimension_type']:
                indexes['fast_lookups']['by_dimension_type'][dim_type] = []
            indexes['fast_lookups']['by_dimension_type'][dim_type].append(
                dim)

            # By requirement status
            if dim_data['is_required_anywhere']:
                if 'required' not in indexes['fast_lookups']['by_requirement_status']:
                    indexes['fast_lookups']['by_requirement_status']['required'] = []
                indexes['fast_lookups']['by_requirement_status']['required'].append(
                    dim)

            if dim_data['is_optional_anywhere']:
                if 'optional' not in indexes['fast_lookups']['by_requirement_status']:
                    indexes['fast_lookups']['by_requirement_status']['optional'] = []
                indexes['fast_lookups']['by_requirement_status']['optional'].append(
                    dim)

            # By constraint status
            if dim_data['has_parent_constraint']:
                if 'constrained' not in indexes['fast_lookups']['by_constraint_status']:
                    indexes['fast_lookups']['by_constraint_status']['constrained'] = []
                indexes['fast_lookups']['by_constraint_status']['constrained'].append(
                    dim)
            else:
                if 'unconstrained' not in indexes['fast_lookups']['by_constraint_status']:
                    indexes['fast_lookups']['by_constraint_status']['unconstrained'] = []
                indexes['fast_lookups']['by_constraint_status']['unconstrained'].append(
                    dim)

        # By field level
        for field_level, field_data in field_metadata.items():
            indexes['fast_lookups']['by_field_level'][field_level] = {
                'field_level': field_level,
                'field_name': field_data['field_name'],
                'dimensions': field_data['dimensions'],
                'dimension_types': field_data['dimension_types'],
                'dimension_count': len(field_data['dimensions']),
                'has_required': field_data['has_required_dimensions'],
                'has_optional': field_data['has_optional_dimensions'],
                'has_constrained': field_data['has_constrained_dimensions']
            }

        # 6. Calculate metadata statistics
        total_dimensions = len(dimension_metadata)
        total_fields = len(field_metadata)

        type_counts = {dim_type: len(
            dims) for dim_type, dims in indexes['dimension_type_groups'].items() if dim_type != 'all_types'}
        validation_counts = {
            flag: len(dims) for flag, dims in indexes['validation_flags'].items()}

        indexes['metadata_stats'] = {
            'total_dimensions': total_dimensions,
            'total_fields': total_fields,
            'dimension_type_distribution': type_counts,
            'validation_flag_distribution': validation_counts,
            'unique_formatting_patterns': len(indexes['formatting_patterns']),
            'unique_delimiters': len(indexes['delimiter_groups']),
            'unique_prefixes': len(indexes['prefix_groups']),
            'unique_suffixes': len(indexes['suffix_groups']),
            'avg_dimensions_per_field': total_dimensions / total_fields if total_fields > 0 else 0,
            'most_common_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None,
            'constraint_coverage': (validation_counts.get('constrained_dimensions', 0) / total_dimensions * 100) if total_dimensions > 0 else 0.0
        }

    def _build_field_rule_preview(self, detail: RuleDetail) -> str:
        """Build field rule preview for a given rule detail"""
        prefix = detail.prefix or ''
        suffix = detail.suffix or ''
        delimiter = detail.delimiter or ''
        return f"{prefix}[{detail.dimension.name}]{suffix}{delimiter}"
