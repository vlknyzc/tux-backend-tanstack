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
    Dimension, DimensionValue, Workspace, ExternalString,
    ExternalStringBatch, String, StringDetail, Project
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

        # 0. Validate string length
        MAX_STRING_LENGTH = 500
        if len(string_value) > MAX_STRING_LENGTH:
            errors.append({
                'type': 'string_too_long',
                'field': 'string_value',
                'message': f"String exceeds maximum length of {MAX_STRING_LENGTH} characters",
                'received': len(string_value),
                'expected': f"≤ {MAX_STRING_LENGTH}"
            })
            return {
                'is_valid': False,
                'entity': None,
                'parsed_dimension_values': {},
                'errors': errors,
                'warnings': warnings,
                'expected_string': None
            }

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
        # Get the rule's entity from its RuleDetails
        rule_entity = rule.rule_details.first().entity if rule.rule_details.exists() else None
        if not rule_entity:
            errors.append({
                'type': 'rule_configuration_error',
                'field': 'rule',
                'message': f"Rule '{rule.name}' has no RuleDetails configured",
                'received': rule.name
            })
            return {
                'is_valid': False,
                'entity': entity,
                'parsed_dimension_values': {},
                'errors': errors,
                'warnings': warnings,
                'expected_string': None
            }

        if entity.id != rule_entity.id:
            return {
                'is_valid': False,
                'entity': entity,
                'parsed_dimension_values': {},
                'errors': [{
                    'type': 'entity_rule_mismatch',
                    'field': 'entity_name',
                    'message': f"Entity '{entity_name}' doesn't match rule entity '{rule_entity.name}'",
                    'expected': rule_entity.name,
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

        # 4. Validate dimension values exist in database
        from master_data.models import Dimension, DimensionValue

        for dimension_name, parsed_value in parsed_values.items():
            # Get the dimension
            try:
                dimension = Dimension.objects.get(
                    name=dimension_name,
                    workspace=workspace
                )
            except Dimension.DoesNotExist:
                errors.append({
                    'type': 'missing_required_dimension',
                    'field': dimension_name,
                    'message': f"Dimension '{dimension_name}' not found in workspace"
                })
                continue

            # For list-type dimensions, validate value exists
            if dimension.type == 'list':
                try:
                    DimensionValue.objects.get(
                        dimension=dimension,
                        value=parsed_value,
                        workspace=workspace
                    )
                except DimensionValue.DoesNotExist:
                    # Get valid values for error message
                    valid_values = list(DimensionValue.objects.filter(
                        dimension=dimension,
                        workspace=workspace
                    ).values_list('value', flat=True)[:10])

                    errors.append({
                        'type': 'invalid_dimension_value',
                        'field': dimension_name,
                        'message': f"Value '{parsed_value}' not valid for dimension '{dimension_name}'",
                        'expected': valid_values,
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

    # ==========================================
    # ExternalString Methods
    # ==========================================

    @staticmethod
    def create_external_string(
        workspace: Workspace,
        platform: Platform,
        rule: Rule,
        entity: Entity,
        batch: ExternalStringBatch,
        string_value: str,
        external_platform_id: str,
        external_parent_id: Optional[str],
        validation_result: Dict,
        created_by
    ) -> ExternalString:
        """
        Create an ExternalString record from validation result.

        Args:
            workspace: Workspace context
            platform: Platform
            rule: Rule used for validation
            entity: Entity
            batch: ExternalStringBatch this string belongs to
            string_value: The string value
            external_platform_id: Platform-specific identifier
            external_parent_id: Parent's platform identifier
            validation_result: Result from validate_external_string()
            created_by: User who created this

        Returns:
            ExternalString instance
        """
        # Check if this external_platform_id exists in this batch
        existing = ExternalString.objects.filter(
            workspace=workspace,
            external_platform_id=external_platform_id,
            batch=batch
        ).first()

        if existing:
            # Update existing (shouldn't happen in same batch, but handle it)
            existing.value = string_value
            existing.external_parent_id = external_parent_id
            existing.validation_status = 'valid' if validation_result['is_valid'] else 'invalid'
            if validation_result.get('warnings'):
                existing.validation_status = 'warning'
            existing.validation_metadata = {
                'parsed_dimension_values': validation_result.get('parsed_dimension_values', {}),
                'errors': validation_result.get('errors', []),
                'warnings': validation_result.get('warnings', [])
            }
            existing.save()
            return existing

        # Determine validation status
        if validation_result.get('should_skip'):
            validation_status = 'skipped'
        elif not validation_result['is_valid']:
            validation_status = 'invalid'
        elif validation_result.get('warnings'):
            validation_status = 'warning'
        else:
            validation_status = 'valid'

        # Create new ExternalString
        external_string = ExternalString.objects.create(
            workspace=workspace,
            platform=platform,
            rule=rule,
            entity=entity,
            batch=batch,
            value=string_value,
            external_platform_id=external_platform_id,
            external_parent_id=external_parent_id,
            validation_status=validation_status,
            validation_metadata={
                'parsed_dimension_values': validation_result.get('parsed_dimension_values', {}),
                'errors': validation_result.get('errors', []),
                'warnings': validation_result.get('warnings', [])
            },
            created_by=created_by,
            version=1
        )

        return external_string

    @staticmethod
    def find_or_create_external_string_version(
        workspace: Workspace,
        external_platform_id: str,
        new_batch: ExternalStringBatch,
        **string_data
    ) -> Tuple[ExternalString, bool]:
        """
        Find existing ExternalString and create new version, or create new.

        Args:
            workspace: Workspace context
            external_platform_id: Platform identifier
            new_batch: New batch for this version
            **string_data: String data (value, validation_result, etc.)

        Returns:
            Tuple of (ExternalString, created: bool)
        """
        # Find latest version of this external_platform_id
        latest = ExternalString.objects.filter(
            workspace=workspace,
            external_platform_id=external_platform_id,
            superseded_by__isnull=True
        ).order_by('-version').first()

        if latest:
            # Create new version
            new_version = StringRegistryService.create_external_string(
                workspace=workspace,
                external_platform_id=external_platform_id,
                batch=new_batch,
                **string_data
            )
            new_version.version = latest.version + 1
            new_version.save()

            # Link versions
            latest.superseded_by = new_version
            latest.save()

            return new_version, False
        else:
            # Create first version
            new_string = StringRegistryService.create_external_string(
                workspace=workspace,
                external_platform_id=external_platform_id,
                batch=new_batch,
                **string_data
            )
            return new_string, True

    # ==========================================
    # String Methods
    # ==========================================

    @staticmethod
    def import_external_string_to_project(
        project: Project,
        external_string: ExternalString,
        created_by
    ) -> String:
        """
        Import an ExternalString into a String.

        Args:
            project: Target project
            external_string: Source ExternalString
            created_by: User performing the import

        Returns:
            String instance

        Raises:
            ValidationError: If import fails validation
        """
        # Validate external_string is importable
        if not external_string.is_importable():
            raise ValidationError(
                f"ExternalString {external_string.external_platform_id} cannot be imported "
                f"(status: {external_string.validation_status}, "
                f"already imported: {external_string.imported_at is not None})"
            )

        # Validate platform is assigned to project
        if not project.platforms.filter(id=external_string.platform_id).exists():
            raise ValidationError(
                f"Platform '{external_string.platform.name}' is not assigned to project '{project.name}'"
            )

        # Check if already exists by external_platform_id
        existing = String.objects.filter(
            workspace=external_string.workspace,
            external_platform_id=external_string.external_platform_id,
            validation_source='external'
        ).first()

        if existing:
            # Update existing String
            existing.value = external_string.value
            existing.external_parent_id = external_string.external_parent_id
            existing.validation_metadata = external_string.validation_metadata
            existing.source_external_string = external_string
            existing.sync_status = 'in_sync'
            existing.save()

            # Mark external_string as imported
            external_string.imported_to_project_string = existing
            external_string.imported_at = timezone.now()
            external_string.save()

            return existing

        # Create new String
        from django.utils import timezone

        project_string = String.objects.create(
            workspace=external_string.workspace,
            project=project,
            platform=external_string.platform,
            entity=external_string.entity,
            rule=external_string.rule,
            value=external_string.value,
            created_by=created_by,
            # External validation fields
            validation_source='external',
            external_platform_id=external_string.external_platform_id,
            external_parent_id=external_string.external_parent_id,
            validation_metadata=external_string.validation_metadata,
            source_external_string=external_string,
            sync_status='in_sync',
            last_synced_at=timezone.now()
        )

        # Mark external_string as imported
        external_string.imported_to_project_string = project_string
        external_string.imported_at = timezone.now()
        external_string.save()

        # TODO: Create StringDetail records from parsed dimension values
        # This would involve creating StringDetail for each dimension
        # from validation_metadata['parsed_dimension_values']

        return project_string

    @staticmethod
    def find_external_string_parent(
        workspace: Workspace,
        parent_external_id: str,
        created_strings: Dict[str, ExternalString] = None
    ) -> Optional[ExternalString]:
        """
        Find parent ExternalString by external_platform_id.

        Checks both newly created strings in current batch and existing strings.

        Args:
            workspace: Workspace context
            parent_external_id: Parent's platform identifier
            created_strings: Dict of external_platform_id -> ExternalString for current batch

        Returns:
            ExternalString if found, None otherwise
        """
        if not parent_external_id:
            return None

        # Check in newly created strings first
        if created_strings and parent_external_id in created_strings:
            return created_strings[parent_external_id]

        # Check in existing ExternalStrings
        return ExternalString.objects.filter(
            workspace=workspace,
            external_platform_id=parent_external_id
        ).order_by('-created').first()

    @staticmethod
    def find_project_string_parent(
        workspace: Workspace,
        parent_external_id: str,
        created_strings: Dict[str, String] = None
    ) -> Optional[String]:
        """
        Find parent String by external_platform_id.

        Args:
            workspace: Workspace context
            parent_external_id: Parent's platform identifier
            created_strings: Dict of external_platform_id -> String for current batch

        Returns:
            String if found, None otherwise
        """
        if not parent_external_id:
            return None

        # Check in newly created strings first
        if created_strings and parent_external_id in created_strings:
            return created_strings[parent_external_id]

        # Check in existing Strings
        return String.objects.filter(
            workspace=workspace,
            external_platform_id=parent_external_id,
            validation_source='external'
        ).first()
