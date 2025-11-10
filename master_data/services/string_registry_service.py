"""
String Registry Service for validating external platform strings.

This service handles validation of strings imported from external advertising platforms
(Meta, Google Ads, TikTok, etc.) against Tuxonomy naming rules.
"""

import csv
import io
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import (
    String, StringDetail, Rule, RuleDetail, Entity, Platform,
    Dimension, DimensionValue, Workspace
)
from .dimension_catalog_service import DimensionCatalogService


class StringRegistryValidationError(Exception):
    """Custom exception for string registry validation errors."""
    pass


class StringRegistryService:
    """
    Service for validating and importing external platform strings.

    Provides functionality to:
    - Parse external strings using rule patterns (reverse of generation)
    - Validate dimension values against catalogs
    - Check entity hierarchy relationships
    - Detect conflicts between Tuxonomy and external hierarchies
    """

    @staticmethod
    def validate_external_string(
        workspace: Workspace,
        platform: Platform,
        rule: Rule,
        entity_name: str,
        string_value: str,
        external_platform_id: Optional[str] = None,
        parent_external_id: Optional[str] = None
    ) -> Dict:
        """
        Validate a single external string against a rule.

        Args:
            workspace: Workspace context
            platform: Selected platform
            rule: Rule to validate against
            entity_name: Entity name from CSV
            string_value: The string to validate
            external_platform_id: Optional platform identifier
            parent_external_id: Optional parent platform identifier

        Returns:
            Dict with validation results:
            {
                'is_valid': bool,
                'entity': Entity or None,
                'parsed_dimension_values': Dict,
                'errors': List[Dict],
                'warnings': List[Dict],
                'expected_string': str or None
            }
        """
        errors = []
        warnings = []
        parsed_values = {}
        entity = None

        # 1. Validate entity exists and belongs to platform
        try:
            entity = Entity.objects.get(name=entity_name, platform=platform)
        except Entity.DoesNotExist:
            valid_entities = list(Entity.objects.filter(
                platform=platform
            ).values_list('name', flat=True))
            errors.append({
                'type': 'entity_platform_mismatch',
                'field': 'entity_name',
                'message': f"Entity '{entity_name}' not found for platform '{platform.name}'",
                'expected': valid_entities,
                'received': entity_name
            })
            return {
                'is_valid': False,
                'entity': None,
                'parsed_dimension_values': {},
                'errors': errors,
                'warnings': warnings,
                'expected_string': None
            }

        # 2. Check if entity matches rule's entity (or skip if not)
        if entity.id != rule.entity.id:
            return {
                'is_valid': False,
                'entity': entity,
                'parsed_dimension_values': {},
                'errors': [{
                    'type': 'entity_rule_mismatch',
                    'field': 'entity_name',
                    'message': f"Entity '{entity_name}' doesn't match rule entity '{rule.entity.name}'",
                    'expected': rule.entity.name,
                    'received': entity_name,
                    'suggestion': 'This row will be skipped. Select a rule for this entity type.'
                }],
                'warnings': warnings,
                'expected_string': None,
                'should_skip': True  # Special flag for entity mismatch
            }

        # 3. Parse the string using rule pattern
        try:
            parsed_values = StringRegistryService._parse_string_by_rule(
                string_value, rule, entity
            )
        except StringRegistryValidationError as e:
            errors.append({
                'type': 'string_parse_failed',
                'field': 'string_value',
                'message': str(e),
                'received': string_value
            })
            return {
                'is_valid': False,
                'entity': entity,
                'parsed_dimension_values': {},
                'errors': errors,
                'warnings': warnings,
                'expected_string': None
            }

        # 4. Validate dimension values against catalog
        dimension_catalog = DimensionCatalogService.get_optimized_catalog(rule.id)

        for dimension_name, parsed_value in parsed_values.items():
            # Find dimension in catalog
            dimension_data = next(
                (d for d in dimension_catalog['dimensions'] if d['dimension']['name'] == dimension_name),
                None
            )

            if not dimension_data:
                errors.append({
                    'type': 'missing_required_dimension',
                    'field': dimension_name,
                    'message': f"Dimension '{dimension_name}' not found in rule configuration"
                })
                continue

            # For list-type dimensions, validate value exists
            if dimension_data['dimension']['dimension_type'] == 'list':
                valid_values = [v['value'] for v in dimension_data.get('values', [])]
                if parsed_value not in valid_values:
                    errors.append({
                        'type': 'invalid_dimension_value',
                        'field': dimension_name,
                        'message': f"Value '{parsed_value}' not valid for dimension '{dimension_name}'",
                        'expected': valid_values[:10],  # Show first 10
                        'received': parsed_value
                    })

        # 5. Check for missing required dimensions
        rule_details = RuleDetail.objects.filter(
            rule=rule,
            entity=entity,
            is_required=True
        ).select_related('dimension')

        for detail in rule_details:
            if detail.dimension.name not in parsed_values:
                errors.append({
                    'type': 'missing_required_dimension',
                    'field': detail.dimension.name,
                    'message': f"Required dimension '{detail.dimension.name}' is missing"
                })

        # 6. Validate string length
        if len(string_value) > 500:  # STRING_VALUE_LENGTH constant
            errors.append({
                'type': 'string_too_long',
                'field': 'string_value',
                'message': f"String length ({len(string_value)}) exceeds maximum (500)",
                'received': len(string_value),
                'expected': 500
            })

        # Determine if valid
        is_valid = len(errors) == 0

        return {
            'is_valid': is_valid,
            'entity': entity,
            'parsed_dimension_values': parsed_values,
            'errors': errors,
            'warnings': warnings,
            'expected_string': string_value  # TODO: Re-generate to compare
        }

    @staticmethod
    def _parse_string_by_rule(string_value: str, rule: Rule, entity: Entity) -> Dict[str, str]:
        """
        Parse an external string using rule pattern (reverse of generation).

        Args:
            string_value: The string to parse
            rule: Rule with formatting details
            entity: Entity to parse for

        Returns:
            Dict mapping dimension names to parsed values

        Raises:
            StringRegistryValidationError: If parsing fails
        """
        # Get rule details ordered by dimension_order
        rule_details = list(RuleDetail.objects.filter(
            rule=rule,
            entity=entity
        ).select_related('dimension').order_by('dimension_order'))

        if not rule_details:
            raise StringRegistryValidationError(
                f"No rule details found for rule '{rule.name}' and entity '{entity.name}'"
            )

        parsed_values = {}
        remaining_string = string_value

        for i, detail in enumerate(rule_details):
            dimension_name = detail.dimension.name
            is_last = (i == len(rule_details) - 1)

            # Determine the delimiter for this segment
            delimiter = detail.delimiter if detail.delimiter else ''

            try:
                # Extract value based on delimiter
                if not is_last and delimiter:
                    # Split by delimiter
                    if delimiter not in remaining_string:
                        raise StringRegistryValidationError(
                            f"Expected delimiter '{delimiter}' not found after dimension '{dimension_name}'"
                        )
                    parts = remaining_string.split(delimiter, 1)
                    segment = parts[0]
                    remaining_string = parts[1] if len(parts) > 1 else ''
                else:
                    # Last segment or no delimiter - take rest of string
                    segment = remaining_string
                    remaining_string = ''

                # Remove prefix and suffix
                value = StringRegistryService._strip_prefix_suffix(
                    segment, detail.prefix, detail.suffix
                )

                if not value and detail.is_required:
                    raise StringRegistryValidationError(
                        f"Empty value for required dimension '{dimension_name}'"
                    )

                parsed_values[dimension_name] = value

            except Exception as e:
                raise StringRegistryValidationError(
                    f"Failed to parse dimension '{dimension_name}': {str(e)}"
                )

        # Check if there's leftover string (parsing didn't consume everything)
        if remaining_string.strip():
            raise StringRegistryValidationError(
                f"String parsing incomplete. Leftover: '{remaining_string}'"
            )

        return parsed_values

    @staticmethod
    def _strip_prefix_suffix(value: str, prefix: Optional[str], suffix: Optional[str]) -> str:
        """
        Remove prefix and suffix from a value.

        Args:
            value: The value to strip
            prefix: Prefix to remove (if present)
            suffix: Suffix to remove (if present)

        Returns:
            Stripped value
        """
        result = value

        if prefix and result.startswith(prefix):
            result = result[len(prefix):]

        if suffix and result.endswith(suffix):
            result = result[:-len(suffix)]

        return result

    @staticmethod
    def validate_hierarchy_relationship(
        child_entity: Entity,
        parent_external_id: Optional[str],
        workspace: Workspace
    ) -> Dict:
        """
        Validate parent-child hierarchy relationship.

        Args:
            child_entity: Child entity
            parent_external_id: External platform ID of parent
            workspace: Workspace context

        Returns:
            Dict with validation results:
            {
                'parent_string': String or None,
                'errors': List[Dict],
                'warnings': List[Dict]
            }
        """
        errors = []
        warnings = []
        parent_string = None

        if not parent_external_id:
            return {'parent_string': None, 'errors': [], 'warnings': []}

        # Try to find parent string by external_platform_id
        try:
            parent_string = String.objects.get(
                workspace=workspace,
                external_platform_id=parent_external_id
            )

            # Validate entity level hierarchy
            if parent_string.entity.entity_level >= child_entity.entity_level:
                errors.append({
                    'type': 'invalid_entity_level',
                    'message': f"Parent entity level ({parent_string.entity.entity_level}) "
                              f"must be less than child level ({child_entity.entity_level})",
                    'parent_entity': parent_string.entity.name,
                    'child_entity': child_entity.name
                })

            # Check for missing intermediate levels
            if child_entity.entity_level - parent_string.entity.entity_level > 1:
                warnings.append({
                    'type': 'missing_intermediate_level',
                    'message': f"Missing intermediate entity levels between "
                              f"{parent_string.entity.name} (level {parent_string.entity.entity_level}) "
                              f"and {child_entity.name} (level {child_entity.entity_level})"
                })

        except String.DoesNotExist:
            warnings.append({
                'type': 'parent_not_found',
                'message': f"Parent with external ID '{parent_external_id}' not found in workspace",
                'external_parent_id': parent_external_id
            })
        except String.MultipleObjectsReturned:
            errors.append({
                'type': 'multiple_parents_found',
                'message': f"Multiple strings found with external ID '{parent_external_id}'",
                'external_parent_id': parent_external_id
            })

        return {
            'parent_string': parent_string,
            'errors': errors,
            'warnings': warnings
        }
