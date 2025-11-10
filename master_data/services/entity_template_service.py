from typing import Dict, List, Optional
from django.core.cache import cache
from django.utils import timezone
from django.db.models import QuerySet, Q
from ..models import Rule, RuleDetail, Entity, Dimension
from .constants import CACHE_TIMEOUT_DEFAULT


class EntityTemplateService:
    """Service for building entity templates and managing entity-level operations"""

    def __init__(self):
        self.cache_timeout = CACHE_TIMEOUT_DEFAULT

    def get_templates_for_rule(self, rule: Rule) -> List[Dict]:
        """Get entity templates for a rule with comprehensive entity data"""
        cache_key = f"entity_templates:{rule.id}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            rule = Rule.objects.get(id=rule.id)
        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule.id} does not exist")

        templates = self._build_templates(rule)

        cache.set(cache_key, templates, self.cache_timeout)

        return templates

    def _build_templates(self, rule: Rule) -> List[Dict]:
        """Build entity templates with optimized queries"""
        rule_details = RuleDetail.objects.filter(rule=rule).select_related(
            'entity', 'dimension', 'dimension__parent'
        ).prefetch_related(
            'dimension__dimension_values'
        ).order_by('entity__entity_level', 'dimension_order')

        # Group by entity
        entities_map = {}
        for detail in rule_details:
            entity = detail.entity
            if entity not in entities_map:
                entities_map[entity] = {
                    'entity': entity,
                    'entity_name': detail.entity.name,
                    'entity_level': detail.entity.entity_level,
                    'next_entity': getattr(detail.entity, 'next_entity', None),
                    'next_entity_name': getattr(detail.entity, 'next_entity', None).name if getattr(detail.entity, 'next_entity', None) else None,
                    'can_generate': self._check_can_generate(rule, detail.entity),
                    'dimensions': [],
                    'validation_rules': [],
                    'generation_metadata': {},
                }

            # Add dimension information
            dimension_info = self._build_dimension_info(detail, rule)
            entities_map[entity]['dimensions'].append(dimension_info)

        # Process each entity to add computed information
        for entity_data in entities_map.values():
            self._enrich_entity_template(entity_data, rule)

        # Convert to list and sort by entity level
        result = list(entities_map.values())
        result.sort(key=lambda x: x['entity_level'])

        return result

    def _build_dimension_info(self, detail: RuleDetail, rule: Rule) -> Dict:
        """Build comprehensive dimension information for a rule detail"""
        # Check for inheritance
        inheritance_info = self._check_dimension_inheritance(detail, rule)

        return {
            'rule_detail': detail.id,  # Store ID instead of object
            'dimension': detail.dimension.id,  # Store ID instead of object
            'dimension_name': detail.dimension.name,
            'dimension_type': detail.dimension.type,
            'dimension_description': detail.dimension.description or '',
            'dimension_order': detail.dimension_order,
            'is_required': getattr(detail, 'is_required', True),

            # Formatting
            'prefix': detail.prefix or '',
            'suffix': detail.suffix or '',
            'delimiter': detail.delimiter or '',
            'effective_delimiter': detail.get_effective_delimiter() if hasattr(detail, 'get_effective_delimiter') else (detail.delimiter or ''),

            # Parent-child relationships
            # Store ID instead of object
            'parent_dimension': detail.dimension.parent.id if detail.dimension.parent else None,
            'parent_dimension_name': detail.dimension.parent.name if detail.dimension.parent else None,

            # Inheritance information
            'inheritance': inheritance_info,

            # Values
            'dimension_values': [
                {
                    'id': value.id,
                    'value': value.value,
                    'label': value.label or value.value,
                    'utm': getattr(value, 'utm', ''),
                    'description': value.description or '',
                    'is_active': getattr(value, 'is_active', True),
                    'order': getattr(value, 'order', 0),
                } for value in detail.dimension.dimension_values.all()
            ],
            'dimension_value_count': detail.dimension.dimension_values.count(),
            'active_value_count': detail.dimension.dimension_values.filter(
                **({'is_active': True} if hasattr(detail.dimension.dimension_values.model, 'is_active') else {})
            ).count(),

            # Behavior flags
            'allows_freetext': detail.dimension.type == 'text',
            'is_dropdown': detail.dimension.type in ['list', 'combobox'],
            'has_constraints': bool(detail.dimension.parent_id),
        }

    def _check_dimension_inheritance(self, detail: RuleDetail, rule: Rule) -> Dict:
        """Check if this dimension is inherited from a parent entity"""
        current_entity_level = detail.entity.entity_level

        if current_entity_level <= 1:
            return {
                'is_inherited': False,
                'parent_rule_detail': None,
                'parent_entity_level': None,
                'parent_entity_name': None,
                'inherits_formatting': False,
            }

        # Look for the same dimension in previous entity levels
        parent_detail = RuleDetail.objects.filter(
            rule=rule,
            dimension=detail.dimension,
            entity__entity_level__lt=current_entity_level
        ).select_related('entity').order_by('-entity__entity_level').first()

        if parent_detail:
            return {
                'is_inherited': True,
                'parent_rule_detail': parent_detail.id,  # Store ID instead of object
                'parent_entity_level': parent_detail.entity.entity_level,
                'parent_entity_name': parent_detail.entity.name,
                'inherits_formatting': self._check_formatting_inheritance(detail, parent_detail),
            }

        return {
            'is_inherited': False,
            'parent_rule_detail': None,
            'parent_entity_level': None,
            'parent_entity_name': None,
            'inherits_formatting': False,
        }

    def _check_formatting_inheritance(self, child_detail: RuleDetail, parent_detail: RuleDetail) -> bool:
        """Check if formatting rules are inherited from parent"""
        return (
            (child_detail.prefix or '') == (parent_detail.prefix or '') and
            (child_detail.suffix or '') == (parent_detail.suffix or '') and
            (child_detail.delimiter or '') == (parent_detail.delimiter or '')
        )

    def _check_can_generate(self, rule: Rule, entity: Entity) -> bool:
        """Check if the rule can generate strings for this entity"""
        # Check if there are any rule details for this entity
        has_rule_details = RuleDetail.objects.filter(
            rule=rule, entity=entity).exists()

        if not has_rule_details:
            return False

        # Check if all required dimensions have values or are optional
        rule_details = RuleDetail.objects.filter(
            rule=rule, entity=entity).select_related('dimension')

        for detail in rule_details:
            is_required = getattr(detail, 'is_required', True)
            if is_required:
                # For required dimensions, check if they have values or allow freetext
                if detail.dimension.type == 'text':
                    continue  # Freetext dimensions can always be filled
                elif detail.dimension.type in ['list', 'combobox']:
                    # Check if there are active dimension values
                    has_values = detail.dimension.dimension_values.filter(
                        **({'is_active': True} if hasattr(detail.dimension.dimension_values.model, 'is_active') else {})
                    ).exists()
                    if not has_values:
                        return False

        return True

    def _enrich_entity_template(self, entity_data: Dict, rule: Rule):
        """Enrich entity template with computed information"""
        # Sort dimensions by order
        entity_data['dimensions'].sort(key=lambda x: x['dimension_order'])

        # Update counts
        entity_data['dimension_count'] = len(entity_data['dimensions'])
        entity_data['required_dimension_count'] = sum(
            1 for d in entity_data['dimensions'] if d['is_required']
        )
        entity_data['inherited_dimension_count'] = sum(
            1 for d in entity_data['dimensions'] if d['inheritance']['is_inherited']
        )

        # Generate entity rule preview
        preview_parts = []
        for dim in entity_data['dimensions']:
            part = (dim['prefix'] +
                    f"[{dim['dimension_name']}]" +
                    dim['suffix'] +
                    dim['effective_delimiter'])
            preview_parts.append(part)

        entity_data['entity_rule_preview'] = ''.join(preview_parts)

        # Add validation rules
        entity_data['validation_rules'] = self._build_validation_rules(
            entity_data)

        # Add generation metadata
        entity_data['generation_metadata'] = self._build_generation_metadata(
            entity_data, rule)

        # Calculate completeness score
        entity_data['completeness_score'] = self._calculate_completeness_score(
            entity_data)

    def _build_validation_rules(self, entity_data: Dict) -> List[Dict]:
        """Build validation rules for the entity"""
        rules = []

        # Required dimension validation
        required_dims = [
            d for d in entity_data['dimensions'] if d['is_required']]
        if required_dims:
            rules.append({
                'type': 'required_dimensions',
                'message': f"Required dimensions: {', '.join(d['dimension_name'] for d in required_dims)}",
                'dimensions': [d['dimension_name'] for d in required_dims]
            })

        # Constraint validation (parent-child relationships)
        constrained_dims = [
            d for d in entity_data['dimensions'] if d['has_constraints']]
        for dim in constrained_dims:
            rules.append({
                'type': 'parent_constraint',
                'message': f"'{dim['dimension_name']}' depends on '{dim['parent_dimension_name']}'",
                'dimension': dim['dimension_name'],
                'parent_dimension': dim['parent_dimension_name']
            })

        return rules

    def _build_generation_metadata(self, entity_data: Dict, rule: Rule) -> Dict:
        """Build metadata for string generation"""
        return {
            'can_generate': entity_data['can_generate'],
            'generation_order': [d['dimension_name'] for d in entity_data['dimensions']],
            'required_for_generation': [d['dimension_name'] for d in entity_data['dimensions'] if d['is_required']],
            'optional_for_generation': [d['dimension_name'] for d in entity_data['dimensions'] if not d['is_required']],
            'total_possible_combinations': self._calculate_possible_combinations(entity_data),
        }

    def _calculate_possible_combinations(self, entity_data: Dict) -> int:
        """Calculate total possible string combinations for this entity"""
        total = 1

        for dim in entity_data['dimensions']:
            if dim['allows_freetext']:
                # For freetext, assume infinite possibilities
                return -1  # Represents infinite
            elif dim['is_dropdown']:
                active_count = dim['active_value_count']
                if active_count == 0:
                    return 0  # No combinations possible
                total *= active_count

        return total

    def _calculate_completeness_score(self, entity_data: Dict) -> float:
        """Calculate completeness score for the entity (0-100)"""
        total_score = 0
        max_score = 0

        for dim in entity_data['dimensions']:
            max_score += 10  # Each dimension contributes max 10 points

            # Has values
            if dim['dimension_value_count'] > 0:
                total_score += 5

            # Has active values
            if dim['active_value_count'] > 0:
                total_score += 3

            # Has proper formatting
            if dim['prefix'] or dim['suffix'] or dim['delimiter']:
                total_score += 2

        return (total_score / max_score * 100) if max_score > 0 else 0

    def get_template_for_entity(self, rule: Rule, entity: Entity) -> Dict:
        """Get template for a specific entity within a rule"""
        templates = self.get_templates_for_rule(rule)

        for template in templates:
            if template['entity'] == entity:
                return template

        raise ValueError(f"Entity {entity} not found in rule {rule.id}")

    def get_generation_preview(self, rule: Rule, entity: Entity, sample_values: Dict[str, str]) -> Dict:
        """Generate a preview of what a string would look like with sample values"""
        template = self.get_template_for_entity(rule, entity)

        if not template['can_generate']:
            return {
                'success': False,
                'error': 'Entity cannot generate strings',
                'preview': None
            }

        # Build preview string
        parts = []
        missing_required = []

        for dim in template['dimensions']:
            dim_name = dim['dimension_name']

            if dim_name in sample_values:
                value = sample_values[dim_name]
                formatted_value = dim['prefix'] + value + dim['suffix']
                parts.append(formatted_value)
            elif dim['is_required']:
                missing_required.append(dim_name)
                parts.append(f"[{dim_name}]")  # Placeholder
            else:
                # Optional dimension, skip
                continue

        # Join with effective delimiters
        preview = ''
        for i, part in enumerate(parts):
            preview += part
            if i < len(parts) - 1:  # Not the last part
                # Use the delimiter from the current dimension
                dim_delimiter = template['dimensions'][i]['effective_delimiter']
                if dim_delimiter:
                    preview += dim_delimiter

        return {
            'success': len(missing_required) == 0,
            'preview': preview,
            'missing_required': missing_required,
            'used_dimensions': list(sample_values.keys()),
            'template_used': template['entity_rule_preview']
        }

    def invalidate_cache(self, rule: Rule):
        """Invalidate entity templates cache for a rule"""
        cache_key = f"entity_templates:{rule.id}"
        cache.delete(cache_key)

    def bulk_invalidate_cache(self, rules: List[Rule]):
        """Invalidate cache for multiple rules"""
        for rule in rules:
            self.invalidate_cache(rule)

    def get_optimized_templates_for_rule(self, rule: Rule) -> List[Dict]:
        """
        Get optimized entity templates with minimal data duplication.
        Returns dimension references by ID instead of full dimension data.
        """
        cache_key = f"optimized_entity_templates:{rule.id}"
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            return cached_result

        try:
            rule = Rule.objects.get(id=rule.id)
        except Rule.DoesNotExist:
            raise ValueError(f"Rule with id {rule.id} does not exist")

        templates = self._build_optimized_templates(rule)

        # Cache for 30 minutes
        cache.set(cache_key, templates, self.cache_timeout)
        return templates

    def _build_optimized_templates(self, rule: Rule) -> List[Dict]:
        """Build optimized entity templates with dimension references only"""
        rule_details = RuleDetail.objects.filter(rule=rule).select_related(
            'entity', 'dimension'
        ).prefetch_related(
            'dimension__dimension_values'
        ).order_by('entity__entity_level', 'dimension_order')

        if not rule_details.exists():
            return []

        # Group by entity ID instead of entity object
        entities_map = {}
        for detail in rule_details:
            entity_id = detail.entity.id
            if entity_id not in entities_map:
                entities_map[entity_id] = {
                    'entity': detail.entity.id,  # Store entity ID instead of object
                    'entity_name': detail.entity.name,
                    'entity_level': detail.entity.entity_level,
                    # Store next entity ID
                    'next_entity': getattr(detail.entity.next_entity, 'id', None) if getattr(detail.entity, 'next_entity', None) else None,
                    'can_generate': self._check_can_generate(rule, detail.entity),
                    'dimensions': [],
                }

            # Add minimal dimension reference
            dimension_ref = self._build_dimension_reference(detail, rule)
            entities_map[entity_id]['dimensions'].append(dimension_ref)

        # Process each entity to add computed information
        for entity_data in entities_map.values():
            self._enrich_optimized_entity_template(entity_data, rule)

        # Convert to list and sort by entity level
        result = list(entities_map.values())
        result.sort(key=lambda x: x['entity_level'])

        return result

    def _build_dimension_reference(self, detail: RuleDetail, rule: Rule) -> Dict:
        """Build minimal dimension reference for optimized templates"""
        # Check for inheritance
        inheritance_info = self._check_dimension_inheritance(detail, rule)

        # Only include formatting overrides if they differ from dimension defaults
        dimension_prefix = getattr(detail.dimension, 'default_prefix', '')
        dimension_suffix = getattr(detail.dimension, 'default_suffix', '')
        dimension_delimiter = getattr(
            detail.dimension, 'default_delimiter', '')

        prefix_override = None
        suffix_override = None
        delimiter_override = None

        if (detail.prefix or '') != dimension_prefix:
            prefix_override = detail.prefix or ''
        if (detail.suffix or '') != dimension_suffix:
            suffix_override = detail.suffix or ''
        if (detail.delimiter or '') != dimension_delimiter:
            delimiter_override = detail.delimiter or ''

        return {
            'dimension': detail.dimension.id,
            'dimension_name': detail.dimension.name,
            'dimension_order': detail.dimension_order,
            'is_required': getattr(detail, 'is_required', True),
            'is_inherited': inheritance_info['is_inherited'],
            'inherits_from_entity_level': inheritance_info['parent_entity_level'],
            'prefix_override': prefix_override,
            'suffix_override': suffix_override,
            'delimiter_override': delimiter_override,
        }

    def _calculate_optimized_completeness_score(self, entity_data: Dict) -> float:
        """Calculate completeness score for the entity using optimized data (0-100)"""
        total_score = 0
        max_score = 0

        for dim in entity_data['dimensions']:
            max_score += 10  # Each dimension contributes max 10 points

            # Basic dimension setup (5 points)
            total_score += 5

            # Has proper formatting (5 points)
            if dim.get('prefix_override') or dim.get('suffix_override') or dim.get('delimiter_override'):
                total_score += 5

        return (total_score / max_score * 100) if max_score > 0 else 0

    def _enrich_optimized_entity_template(self, entity_data: Dict, rule: Rule):
        """Enrich optimized entity template with computed information"""
        # Sort dimensions by order
        entity_data['dimensions'].sort(key=lambda x: x['dimension_order'])

        # Update counts
        entity_data['dimension_count'] = len(entity_data['dimensions'])
        entity_data['required_dimension_count'] = sum(
            1 for d in entity_data['dimensions'] if d['is_required']
        )
        entity_data['inherited_dimension_count'] = sum(
            1 for d in entity_data['dimensions'] if d['is_inherited']
        )

        # Generate entity rule preview (need to lookup dimension names)
        entity_data['entity_rule_preview'] = self._generate_optimized_preview(
            entity_data['dimensions'], rule)

        # Calculate completeness score using the optimized method
        entity_data['completeness_score'] = self._calculate_optimized_completeness_score(
            entity_data)

    def _generate_optimized_preview(self, dimension_refs: List[Dict], rule: Rule) -> str:
        """Generate entity rule preview from dimension references"""
        preview_parts = []

        for dim_ref in dimension_refs:
            # Use override formatting if provided, otherwise use dimension defaults
            prefix = dim_ref.get('prefix_override', '')
            suffix = dim_ref.get('suffix_override', '')
            delimiter = dim_ref.get('delimiter_override', '')

            part = f"{prefix}[{dim_ref['dimension_name']}]{suffix}{delimiter}"
            preview_parts.append(part)

        return ''.join(preview_parts)
