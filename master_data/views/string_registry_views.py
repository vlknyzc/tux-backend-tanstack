"""
String Registry ViewSet for validating and importing external platform strings.

Provides endpoints for CSV upload and validation of strings from advertising platforms
(Meta, Google Ads, TikTok, etc.) against Tuxonomy naming rules.
"""

import csv
import io
import logging
from typing import Dict, List
from collections import defaultdict

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ..models import Platform, Rule, Entity, String, StringDetail, Workspace
from ..services import StringRegistryService, DimensionCatalogService
from ..serializers.string_registry import (
    CSVUploadRequestSerializer,
    BulkValidationResponseSerializer,
    SingleStringValidationRequestSerializer,
    SingleStringValidationResponseSerializer,
)
from .mixins import WorkspaceValidationMixin

logger = logging.getLogger(__name__)


@extend_schema(tags=['String Registry'])
class StringRegistryViewSet(WorkspaceValidationMixin, viewsets.ViewSet):
    """
    ViewSet for external platform string validation and import.

    Provides endpoints to:
    - Upload CSV files with external platform strings
    - Validate strings against workspace naming rules
    - Import validated strings into Tuxonomy
    - Track dual hierarchies (Tuxonomy vs Platform)

    URL: /api/v1/workspaces/{workspace_id}/string-registry/
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["String Registry"],
        methods=['post'],
        request=CSVUploadRequestSerializer,
        responses={200: BulkValidationResponseSerializer},
        summary="Upload and validate CSV of external strings",
        description="""
        Upload a CSV file containing external platform strings for validation and import.

        **Required CSV Columns:**
        - `string_value`: The naming string to validate (required)
        - `external_platform_id`: Platform-specific identifier (required for storage)
        - `entity_name`: Entity name (e.g., 'campaign', 'ad_group') (required)
        - `parent_external_id`: Parent's platform identifier (optional)

        **CSV Example:**
        ```csv
        string_value,external_platform_id,entity_name,parent_external_id
        ACME-2024,account_999,account,
        ACME-2024-US-Q4-Awareness,campaign_123,campaign,account_999
        ACME-2024-US-Q4-Broad-18-35,adgroup_456,ad_group,campaign_123
        ```

        **Request Parameters:**
        - `platform_id`: ID of the platform (Meta, Google Ads, etc.)
        - `rule_id`: ID of the rule to validate against
        - `file`: CSV file (max 5MB, 500 rows)

        **Processing:**
        1. Validates CSV structure and required columns
        2. Sorts rows by entity hierarchy level
        3. Validates each string against rule patterns
        4. Creates/updates String records for valid entries
        5. Links parent-child relationships
        6. Detects hierarchy conflicts

        **Response includes:**
        - Summary statistics (total, processed, valid, failed, warnings)
        - Detailed results for each row with errors/warnings
        - Hierarchy information (conflicts, missing parents)

        **Row Statuses:**
        - `valid`: Passed validation, String created/updated
        - `warning`: Passed but has warnings (conflicts, missing parent)
        - `failed`: Failed validation, not stored
        - `skipped`: Entity doesn't match rule (entity_mismatch)
        - `updated`: Existing String updated
        """,
    )
    @action(detail=False, methods=['post'])
    def upload(self, request, workspace_id=None, **kwargs):
        """Upload and validate CSV file with external strings."""
        # Validate workspace access
        workspace = self.get_validated_workspace()

        # Validate request
        serializer = CSVUploadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        platform_id = serializer.validated_data['platform_id']
        rule_id = serializer.validated_data['rule_id']
        csv_file = serializer.validated_data['file']

        try:
            # Get platform and rule
            platform = Platform.objects.get(id=platform_id)
            rule = Rule.objects.get(id=rule_id, workspace=workspace)

            # Validate rule belongs to platform
            if rule.platform.id != platform.id:
                return Response(
                    {'error': f"Rule does not belong to platform '{platform.name}'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse CSV
            csv_data = self._parse_csv(csv_file)

            if 'error' in csv_data:
                return Response(
                    {'error': csv_data['error'], 'details': csv_data.get('details')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process and validate strings
            result = self._process_csv_rows(
                workspace=workspace,
                platform=platform,
                rule=rule,
                csv_rows=csv_data['rows']
            )

            return Response(result, status=status.HTTP_200_OK)

        except Platform.DoesNotExist:
            return Response(
                {'error': f"Platform with id {platform_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Rule.DoesNotExist:
            return Response(
                {'error': f"Rule with id {rule_id} not found in workspace"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error processing CSV upload: {str(e)}", exc_info=True)
            return Response(
                {'error': f"Upload processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=["String Registry"],
        methods=['post'],
        request=SingleStringValidationRequestSerializer,
        responses={200: SingleStringValidationResponseSerializer},
        summary="Validate a single external string",
        description="""
        Validate a single string without creating a String record.
        Useful for testing strings before bulk upload.

        **Request:**
        ```json
        {
          "rule_id": 5,
          "entity_name": "campaign",
          "string_value": "meta-us-q4-2024-awareness",
          "external_platform_id": "campaign_123"
        }
        ```

        **Response:**
        ```json
        {
          "is_valid": true,
          "entity_name": "campaign",
          "parsed_dimension_values": {
            "platform": "meta",
            "region": "us",
            "quarter": "q4",
            "year": "2024",
            "objective": "awareness"
          },
          "errors": [],
          "warnings": [],
          "string_id": null
        }
        ```
        """,
    )
    @action(detail=False, methods=['post'])
    def validate_single(self, request, workspace_id=None, **kwargs):
        """Validate a single string without creating a record."""
        workspace = self.get_validated_workspace()

        serializer = SingleStringValidationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            rule = Rule.objects.get(id=serializer.validated_data['rule_id'], workspace=workspace)
            platform = rule.platform

            result = StringRegistryService.validate_external_string(
                workspace=workspace,
                platform=platform,
                rule=rule,
                entity_name=serializer.validated_data['entity_name'],
                string_value=serializer.validated_data['string_value'],
                external_platform_id=serializer.validated_data.get('external_platform_id'),
                parent_external_id=serializer.validated_data.get('parent_external_id')
            )

            response_data = {
                'is_valid': result['is_valid'],
                'entity_name': serializer.validated_data['entity_name'],
                'parsed_dimension_values': result['parsed_dimension_values'],
                'errors': result['errors'],
                'warnings': result['warnings'],
                'string_id': None
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Rule.DoesNotExist:
            return Response(
                {'error': 'Rule not found in workspace'},
                status=status.HTTP_404_NOT_FOUND
            )

    def _parse_csv(self, csv_file) -> Dict:
        """
        Parse uploaded CSV file.

        Returns:
            Dict with 'rows' list or 'error' message
        """
        try:
            # Read file content
            content = csv_file.read()

            # Try to decode with different encodings
            try:
                decoded = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    decoded = content.decode('utf-8-sig')  # UTF-8 with BOM
                except UnicodeDecodeError:
                    return {
                        'error': 'File encoding not supported',
                        'details': 'Please ensure file is UTF-8 encoded'
                    }

            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(decoded))

            # Validate required columns
            required_columns = {'string_value', 'external_platform_id', 'entity_name'}
            if not required_columns.issubset(set(csv_reader.fieldnames or [])):
                missing = required_columns - set(csv_reader.fieldnames or [])
                return {
                    'error': 'Missing required columns',
                    'details': {
                        'missing_columns': list(missing),
                        'required_columns': list(required_columns),
                        'found_columns': csv_reader.fieldnames
                    }
                }

            # Read rows
            rows = []
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (row 1 is header)
                # Skip empty rows
                if not any(row.values()):
                    continue

                rows.append({
                    'row_number': row_num,
                    'string_value': row.get('string_value', '').strip(),
                    'external_platform_id': row.get('external_platform_id', '').strip(),
                    'entity_name': row.get('entity_name', '').strip(),
                    'parent_external_id': row.get('parent_external_id', '').strip() or None,
                })

            # Check row count
            if len(rows) > 500:
                return {
                    'error': 'Too many rows',
                    'details': f'File contains {len(rows)} rows, maximum is 500'
                }

            if len(rows) == 0:
                return {
                    'error': 'Empty file',
                    'details': 'CSV file contains no data rows'
                }

            return {'rows': rows}

        except csv.Error as e:
            return {
                'error': 'CSV parsing failed',
                'details': str(e)
            }
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}", exc_info=True)
            return {
                'error': 'File processing failed',
                'details': str(e)
            }

    def _process_csv_rows(
        self,
        workspace: Workspace,
        platform: Platform,
        rule: Rule,
        csv_rows: List[Dict]
    ) -> Dict:
        """
        Process and validate CSV rows, creating String records.

        Returns:
            Dict with summary and detailed results
        """
        # Pre-fetch entities for platform
        entities_by_name = {
            e.name: e for e in Entity.objects.filter(platform=platform)
        }

        # Get all external IDs from CSV to check for existing strings and duplicates
        csv_external_ids = [row['external_platform_id'] for row in csv_rows if row['external_platform_id']]

        # Check for within-file duplicates
        external_id_rows = defaultdict(list)
        for row in csv_rows:
            if row['external_platform_id']:
                external_id_rows[row['external_platform_id']].append(row['row_number'])

        duplicates_in_file = {
            ext_id: rows for ext_id, rows in external_id_rows.items() if len(rows) > 1
        }

        # Lookup existing strings by external_platform_id
        existing_strings = {
            s.external_platform_id: s
            for s in String.objects.filter(
                workspace=workspace,
                external_platform_id__in=csv_external_ids
            ).select_related('entity', 'parent')
        }

        # Sort rows by entity level (for hierarchical processing)
        sorted_rows = self._sort_rows_by_entity_level(csv_rows, entities_by_name)

        # Process rows
        results = []
        created_strings = {}  # Track newly created strings by external_platform_id

        stats = {
            'total_rows': len(csv_rows),
            'uploaded_rows': len(csv_rows),
            'processed_rows': 0,
            'skipped_rows': 0,
            'created': 0,
            'updated': 0,
            'valid': 0,
            'warnings': 0,
            'failed': 0,
            'linked_parents': 0,
            'parent_conflicts': 0,
            'parent_not_found': 0,
        }

        for row in sorted_rows:
            result = self._process_single_row(
                workspace=workspace,
                platform=platform,
                rule=rule,
                row=row,
                existing_strings=existing_strings,
                created_strings=created_strings,
                entities_by_name=entities_by_name,
                duplicates_in_file=duplicates_in_file
            )

            results.append(result)

            # Update stats
            if result['status'] == 'skipped':
                stats['skipped_rows'] += 1
            else:
                stats['processed_rows'] += 1

            if result['status'] in ('valid', 'updated'):
                stats['valid'] += 1
                if result['status'] == 'created':
                    stats['created'] += 1
                elif result['status'] == 'updated':
                    stats['updated'] += 1
            elif result['status'] == 'warning':
                stats['warnings'] += 1
                stats['valid'] += 1  # Still valid, just has warnings
            elif result['status'] == 'failed':
                stats['failed'] += 1

            # Track hierarchy stats
            if result.get('tuxonomy_parent_id'):
                stats['linked_parents'] += 1

            for warning in result['warnings']:
                if warning['type'] == 'hierarchy_conflict':
                    stats['parent_conflicts'] += 1
                elif warning['type'] == 'parent_not_found':
                    stats['parent_not_found'] += 1

        return {
            'success': True,
            'summary': stats,
            'results': results
        }

    def _sort_rows_by_entity_level(self, rows: List[Dict], entities_by_name: Dict) -> List[Dict]:
        """Sort CSV rows by entity hierarchy level."""
        def get_entity_level(row):
            entity = entities_by_name.get(row['entity_name'])
            return entity.entity_level if entity else 999  # Put unknown entities at end

        return sorted(rows, key=get_entity_level)

    def _process_single_row(
        self,
        workspace: Workspace,
        platform: Platform,
        rule: Rule,
        row: Dict,
        existing_strings: Dict,
        created_strings: Dict,
        entities_by_name: Dict,
        duplicates_in_file: Dict
    ) -> Dict:
        """Process and validate a single CSV row."""
        row_result = {
            'row_number': row['row_number'],
            'string_value': row['string_value'],
            'external_platform_id': row['external_platform_id'],
            'entity_name': row['entity_name'],
            'parent_external_id': row['parent_external_id'],
            'status': 'failed',
            'string_id': None,
            'tuxonomy_parent_id': None,
            'errors': [],
            'warnings': []
        }

        # Check for within-file duplicate
        if row['external_platform_id'] and row['external_platform_id'] in duplicates_in_file:
            dup_rows = duplicates_in_file[row['external_platform_id']]
            if row['row_number'] != min(dup_rows):  # Not the first occurrence
                row_result['status'] = 'skipped'
                row_result['warnings'].append({
                    'type': 'duplicate_in_file',
                    'message': f"Duplicate external_platform_id, using row {min(dup_rows)}"
                })
                return row_result

        # Validate the string
        validation_result = StringRegistryService.validate_external_string(
            workspace=workspace,
            platform=platform,
            rule=rule,
            entity_name=row['entity_name'],
            string_value=row['string_value'],
            external_platform_id=row['external_platform_id'],
            parent_external_id=row['parent_external_id']
        )

        # Handle entity mismatch (should skip)
        if validation_result.get('should_skip'):
            row_result['status'] = 'skipped'
            row_result['errors'] = validation_result['errors']
            return row_result

        # Copy errors and warnings
        row_result['errors'] = validation_result['errors']
        row_result['warnings'] = validation_result['warnings']

        # If validation failed, don't create string
        if not validation_result['is_valid']:
            row_result['status'] = 'failed'
            return row_result

        # Only store if external_platform_id is provided
        if not row['external_platform_id']:
            row_result['status'] = 'valid'  # Valid but not stored
            return row_result

        # Create or update String record
        try:
            with transaction.atomic():
                entity = validation_result['entity']
                existing_string = existing_strings.get(row['external_platform_id'])

                if existing_string:
                    # Update existing string
                    string_instance = self._update_existing_string(
                        existing_string=existing_string,
                        row=row,
                        validation_result=validation_result,
                        entity=entity,
                        rule=rule
                    )
                    row_result['status'] = 'updated'
                else:
                    # Create new string
                    string_instance = self._create_new_string(
                        workspace=workspace,
                        row=row,
                        validation_result=validation_result,
                        entity=entity,
                        rule=rule,
                        created_by=self.request.user
                    )
                    row_result['status'] = 'valid'
                    created_strings[row['external_platform_id']] = string_instance

                row_result['string_id'] = string_instance.id

                # Link parent if needed
                if row['parent_external_id']:
                    parent_result = self._link_parent(
                        string_instance=string_instance,
                        parent_external_id=row['parent_external_id'],
                        workspace=workspace,
                        existing_strings=existing_strings,
                        created_strings=created_strings,
                        entity=entity
                    )

                    if parent_result['parent']:
                        row_result['tuxonomy_parent_id'] = parent_result['parent'].id

                    row_result['warnings'].extend(parent_result['warnings'])
                    row_result['errors'].extend(parent_result['errors'])

                # If has warnings, update status
                if row_result['warnings'] and row_result['status'] == 'valid':
                    row_result['status'] = 'warning'

        except Exception as e:
            logger.error(f"Error creating/updating string for row {row['row_number']}: {str(e)}", exc_info=True)
            row_result['status'] = 'failed'
            row_result['errors'].append({
                'type': 'string_creation_failed',
                'message': f"Failed to create string: {str(e)}"
            })

        return row_result

    def _create_new_string(
        self,
        workspace: Workspace,
        row: Dict,
        validation_result: Dict,
        entity: Entity,
        rule: Rule,
        created_by
    ) -> String:
        """Create a new String record."""
        string_instance = String.objects.create(
            workspace=workspace,
            entity=entity,
            rule=rule,
            value=row['string_value'],
            validation_source='external',
            external_platform_id=row['external_platform_id'],
            external_parent_id=row['parent_external_id'],
            validation_status='valid',
            validation_metadata={
                'validated_at': None,  # Will be set by save
                'parsed_dimension_values': validation_result['parsed_dimension_values'],
                'errors': validation_result['errors'],
                'warnings': validation_result['warnings']
            },
            is_auto_generated=False,
            created_by=created_by
        )

        # Create StringDetails for parsed dimension values
        # TODO: Implement StringDetail creation based on parsed values

        return string_instance

    def _update_existing_string(
        self,
        existing_string: String,
        row: Dict,
        validation_result: Dict,
        entity: Entity,
        rule: Rule
    ) -> String:
        """Update an existing String record."""
        # Update fields
        existing_string.value = row['string_value']
        existing_string.external_parent_id = row['parent_external_id']
        existing_string.validation_status = 'valid'
        existing_string.validation_metadata = {
            'validated_at': None,  # Will be updated
            'parsed_dimension_values': validation_result['parsed_dimension_values'],
            'errors': validation_result['errors'],
            'warnings': validation_result['warnings']
        }
        existing_string.save()

        # Update StringDetails if needed
        # TODO: Implement StringDetail update based on parsed values

        return existing_string

    def _link_parent(
        self,
        string_instance: String,
        parent_external_id: str,
        workspace: Workspace,
        existing_strings: Dict,
        created_strings: Dict,
        entity: Entity
    ) -> Dict:
        """Link parent relationship for a string."""
        warnings = []
        errors = []
        parent = None

        # Try to find parent in created strings first, then existing
        parent = created_strings.get(parent_external_id)
        if not parent:
            parent = existing_strings.get(parent_external_id)

        if parent:
            # Validate hierarchy
            hierarchy_result = StringRegistryService.validate_hierarchy_relationship(
                child_entity=entity,
                parent_external_id=parent_external_id,
                workspace=workspace
            )

            errors.extend(hierarchy_result['errors'])
            warnings.extend(hierarchy_result['warnings'])

            # If no errors, link parent
            if not hierarchy_result['errors']:
                # Check for hierarchy conflict
                if string_instance.parent and string_instance.parent.id != parent.id:
                    warnings.append({
                        'type': 'hierarchy_conflict',
                        'message': 'External parent differs from existing Tuxonomy parent',
                        'tuxonomy_parent_external_id': string_instance.parent.external_platform_id,
                        'external_parent_id': parent_external_id
                    })

                string_instance.parent = parent
                string_instance.save(update_fields=['parent'])
        else:
            warnings.append({
                'type': 'parent_not_found',
                'message': f"Parent with external ID '{parent_external_id}' not found in workspace",
                'external_parent_id': parent_external_id
            })

        return {
            'parent': parent,
            'warnings': warnings,
            'errors': errors
        }
