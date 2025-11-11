"""
String Registry ViewSet for validating and importing external platform strings.

Provides endpoints for CSV upload and validation of strings from advertising platforms
(Meta, Google Ads, TikTok, etc.) against Tuxonomy naming rules.
"""

import csv
import io
import logging
import time
from typing import Dict, List
from collections import defaultdict

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ..models import (
    Platform, Rule, Entity, String, StringDetail, Workspace,
    ExternalStringBatch, ExternalString, Project
)
from ..services import StringRegistryService, DimensionCatalogService
from ..serializers.string_registry import (
    SingleStringValidationRequestSerializer,
    SingleStringValidationResponseSerializer,
    ValidationOnlyRequestSerializer,
    ValidationOnlyResponseSerializer,
    ImportToProjectRequestSerializer,
    ImportToProjectResponseSerializer,
    SelectiveImportRequestSerializer,
    SelectiveImportResponseSerializer,
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

    # ==========================================
    # Endpoints for ExternalString/String
    # ==========================================

    @extend_schema(
        tags=["String Registry"],
        methods=['post'],
        request=ValidationOnlyRequestSerializer,
        responses={200: ValidationOnlyResponseSerializer},
        summary="Validate CSV without importing to project",
        description="""
        Validate external platform strings and store them as ExternalStrings without importing to a project.

        **Use Case**: Users want to validate compliance without committing to a project.

        **Required CSV Columns:**
        - `string_value`: The naming string to validate (required)
        - `external_platform_id`: Platform-specific identifier (required)
        - `entity_name`: Entity name (e.g., 'campaign', 'ad_group') (required)
        - `parent_external_id`: Parent's platform identifier (optional)

        **Process:**
        1. Validates all strings (valid + invalid)
        2. Creates ExternalString records for ALL strings
        3. Returns validation results
        4. Users can later import valid strings via /import-selected/

        **Response includes:**
        - batch_id: ExternalStringBatch ID for this upload
        - Summary statistics (valid, invalid, warnings, failed)
        - Detailed results per row with external_string_id
        """,
    )
    @action(detail=False, methods=['post'], url_path='validate')
    def validate_only(self, request, workspace_id=None, **kwargs):
        """Validate CSV and create ExternalStrings (no project import)."""
        start_time = time.time()

        # Validate workspace access
        workspace = self.get_validated_workspace()

        # Validate request
        serializer = ValidationOnlyRequestSerializer(data=request.data)
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

            # Create ExternalStringBatch for validation
            batch = ExternalStringBatch.objects.create(
                workspace=workspace,
                uploaded_by=request.user,
                file_name=csv_file.name,
                file_size_bytes=csv_file.size,
                platform=platform,
                rule=rule,
                operation_type='validation',
                status='processing'
            )

            # Parse CSV
            csv_data = self._parse_csv(csv_file)

            if 'error' in csv_data:
                batch.status = 'failed'
                batch.error_message = csv_data['error']
                batch.processing_time_seconds = time.time() - start_time
                batch.save()

                return Response(
                    {'error': csv_data['error'], 'details': csv_data.get('details')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process rows and create ExternalStrings
            result = self._process_validation_only(
                workspace=workspace,
                platform=platform,
                rule=rule,
                csv_rows=csv_data['rows'],
                batch=batch,
                created_by=request.user
            )

            # Update batch with results
            processing_time = time.time() - start_time
            stats = result['summary']

            batch.total_rows = stats['total_rows']
            batch.uploaded_rows = stats['uploaded_rows']
            batch.processed_rows = stats['processed_rows']
            batch.skipped_rows = stats['skipped_rows']
            batch.created_count = stats['created']
            batch.valid_count = stats['valid']
            batch.warnings_count = stats['warnings']
            batch.failed_count = stats['failed']
            batch.processing_time_seconds = processing_time
            batch.status = 'completed'
            batch.save()

            return Response({
                'success': True,
                'batch_id': batch.id,
                'operation_type': 'validation',
                'summary': stats,
                'results': result['results']
            }, status=status.HTTP_200_OK)

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
            logger.error(f"Error processing validation: {str(e)}", exc_info=True)

            if 'batch' in locals():
                batch.status = 'failed'
                batch.error_message = str(e)
                batch.processing_time_seconds = time.time() - start_time
                batch.save()

            return Response(
                {'error': f"Validation processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _process_validation_only(
        self,
        workspace: Workspace,
        platform: Platform,
        rule: Rule,
        csv_rows: List[Dict],
        batch: ExternalStringBatch,
        created_by
    ) -> Dict:
        """Process CSV rows and create ExternalString records (validation only)."""
        # Pre-fetch entities
        entities_by_name = {
            e.name: e for e in Entity.objects.filter(platform=platform)
        }

        # Process rows
        results = []
        created_external_strings = {}

        stats = {
            'total_rows': len(csv_rows),
            'uploaded_rows': len(csv_rows),
            'processed_rows': 0,
            'skipped_rows': 0,
            'created': 0,
            'valid': 0,
            'warnings': 0,
            'failed': 0,
        }

        for row in csv_rows:
            entity_name = row['entity_name']
            entity = entities_by_name.get(entity_name)

            if not entity:
                # Entity not found - skip
                results.append({
                    'row_number': row['row_number'],
                    'string_value': row['string_value'],
                    'external_platform_id': row['external_platform_id'],
                    'entity_name': entity_name,
                    'parent_external_id': row.get('parent_external_id'),
                    'validation_status': 'skipped',
                    'external_string_id': None,
                    'errors': [{'type': 'entity_not_found', 'message': f"Entity '{entity_name}' not found"}],
                    'warnings': []
                })
                stats['skipped_rows'] += 1
                continue

            # Validate the string
            validation_result = StringRegistryService.validate_external_string(
                workspace=workspace,
                platform=platform,
                rule=rule,
                entity_name=entity_name,
                string_value=row['string_value'],
                external_platform_id=row['external_platform_id'],
                parent_external_id=row.get('parent_external_id')
            )

            # Create ExternalString (regardless of validation status)
            external_string = StringRegistryService.create_external_string(
                workspace=workspace,
                platform=platform,
                rule=rule,
                entity=entity,
                batch=batch,
                string_value=row['string_value'],
                external_platform_id=row['external_platform_id'],
                external_parent_id=row.get('parent_external_id'),
                validation_result=validation_result,
                created_by=created_by
            )

            created_external_strings[row['external_platform_id']] = external_string

            # Build result
            row_result = {
                'row_number': row['row_number'],
                'string_value': row['string_value'],
                'external_platform_id': row['external_platform_id'],
                'entity_name': entity_name,
                'parent_external_id': row.get('parent_external_id'),
                'validation_status': external_string.validation_status,
                'external_string_id': external_string.id,
                'errors': validation_result.get('errors', []),
                'warnings': validation_result.get('warnings', [])
            }

            results.append(row_result)

            # Update stats
            if validation_result.get('should_skip'):
                stats['skipped_rows'] += 1
            else:
                stats['processed_rows'] += 1

            stats['created'] += 1

            if external_string.validation_status == 'valid':
                stats['valid'] += 1
            elif external_string.validation_status == 'warning':
                stats['warnings'] += 1
                stats['valid'] += 1
            elif external_string.validation_status == 'invalid':
                stats['failed'] += 1

        return {
            'summary': stats,
            'results': results
        }

    @extend_schema(
        tags=["String Registry"],
        methods=['post'],
        request=ImportToProjectRequestSerializer,
        responses={200: ImportToProjectResponseSerializer},
        summary="Validate and import CSV directly to project",
        description="""
        Validate external platform strings and directly import valid ones to a project.

        **Use Case**: Users want to validate and import in one operation.

        **Required CSV Columns:**
        - `string_value`: The naming string to validate (required)
        - `external_platform_id`: Platform-specific identifier (required)
        - `entity_name`: Entity name (e.g., 'campaign', 'ad_group') (required)
        - `parent_external_id`: Parent's platform identifier (optional)

        **Process:**
        1. Validates all strings
        2. Creates ExternalString records for ALL strings (valid + invalid)
        3. Imports VALID strings to String
        4. Returns combined results

        **Requirements:**
        - `project_id` must be provided
        - Platform must be assigned to the project

        **Response includes:**
        - batch_id: ExternalStringBatch ID
        - project: {id, name}
        - Summary statistics
        - Detailed results with external_string_id and project_string_id
        """,
    )
    @action(detail=False, methods=['post'], url_path='import')
    def import_to_project(self, request, workspace_id=None, **kwargs):
        """Validate and import CSV directly to a project."""
        start_time = time.time()

        # Validate workspace access
        workspace = self.get_validated_workspace()

        # Validate request
        serializer = ImportToProjectRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data['project_id']
        platform_id = serializer.validated_data['platform_id']
        rule_id = serializer.validated_data['rule_id']
        csv_file = serializer.validated_data['file']

        try:
            # Get project, platform, and rule
            project = Project.objects.get(id=project_id, workspace=workspace)
            platform = Platform.objects.get(id=platform_id)
            rule = Rule.objects.get(id=rule_id, workspace=workspace)

            # Validate platform is assigned to project
            if not project.platforms.filter(id=platform_id).exists():
                return Response(
                    {'error': f"Platform '{platform.name}' is not assigned to project '{project.name}'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate rule belongs to platform
            if rule.platform.id != platform.id:
                return Response(
                    {'error': f"Rule does not belong to platform '{platform.name}'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create ExternalStringBatch for import
            batch = ExternalStringBatch.objects.create(
                workspace=workspace,
                uploaded_by=request.user,
                file_name=csv_file.name,
                file_size_bytes=csv_file.size,
                platform=platform,
                rule=rule,
                project=project,
                operation_type='import',
                status='processing'
            )

            # Parse CSV
            csv_data = self._parse_csv(csv_file)

            if 'error' in csv_data:
                batch.status = 'failed'
                batch.error_message = csv_data['error']
                batch.processing_time_seconds = time.time() - start_time
                batch.save()

                return Response(
                    {'error': csv_data['error'], 'details': csv_data.get('details')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process rows: create ExternalStrings + import to Strings
            result = self._process_import_to_project(
                workspace=workspace,
                project=project,
                platform=platform,
                rule=rule,
                csv_rows=csv_data['rows'],
                batch=batch,
                created_by=request.user
            )

            # Update batch with results
            processing_time = time.time() - start_time
            stats = result['summary']

            batch.total_rows = stats['total_rows']
            batch.uploaded_rows = stats['uploaded_rows']
            batch.processed_rows = stats['processed_rows']
            batch.skipped_rows = stats['skipped_rows']
            batch.created_count = stats['created']
            batch.updated_count = stats['updated']
            batch.valid_count = stats['valid']
            batch.warnings_count = stats['warnings']
            batch.failed_count = stats['failed']
            batch.processing_time_seconds = processing_time
            batch.status = 'completed'
            batch.save()

            return Response({
                'success': True,
                'batch_id': batch.id,
                'operation_type': 'import',
                'project': {'id': project.id, 'name': project.name},
                'summary': stats,
                'results': result['results']
            }, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response(
                {'error': f"Project with id {project_id} not found in workspace"},
                status=status.HTTP_404_NOT_FOUND
            )
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
            logger.error(f"Error processing import: {str(e)}", exc_info=True)

            if 'batch' in locals():
                batch.status = 'failed'
                batch.error_message = str(e)
                batch.processing_time_seconds = time.time() - start_time
                batch.save()

            return Response(
                {'error': f"Import processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _process_import_to_project(
        self,
        workspace: Workspace,
        project: Project,
        platform: Platform,
        rule: Rule,
        csv_rows: List[Dict],
        batch: ExternalStringBatch,
        created_by
    ) -> Dict:
        """Process CSV rows: create ExternalStrings AND import to Strings."""
        # Pre-fetch entities
        entities_by_name = {
            e.name: e for e in Entity.objects.filter(platform=platform)
        }

        # Process rows
        results = []
        created_external_strings = {}
        created_project_strings = {}

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
        }

        for row in csv_rows:
            entity_name = row['entity_name']
            entity = entities_by_name.get(entity_name)

            if not entity:
                # Entity not found - skip
                results.append({
                    'row_number': row['row_number'],
                    'string_value': row['string_value'],
                    'external_platform_id': row['external_platform_id'],
                    'entity_name': entity_name,
                    'validation_status': 'skipped',
                    'external_string_id': None,
                    'project_string_id': None,
                    'import_status': 'skipped',
                    'errors': [{'type': 'entity_not_found', 'message': f"Entity '{entity_name}' not found"}],
                    'warnings': []
                })
                stats['skipped_rows'] += 1
                continue

            # Validate the string
            validation_result = StringRegistryService.validate_external_string(
                workspace=workspace,
                platform=platform,
                rule=rule,
                entity_name=entity_name,
                string_value=row['string_value'],
                external_platform_id=row['external_platform_id'],
                parent_external_id=row.get('parent_external_id')
            )

            # Create ExternalString (regardless of validation status)
            external_string = StringRegistryService.create_external_string(
                workspace=workspace,
                platform=platform,
                rule=rule,
                entity=entity,
                batch=batch,
                string_value=row['string_value'],
                external_platform_id=row['external_platform_id'],
                external_parent_id=row.get('parent_external_id'),
                validation_result=validation_result,
                created_by=created_by
            )

            created_external_strings[row['external_platform_id']] = external_string

            # Try to import to String if valid
            project_string = None
            import_status = 'skipped'

            if external_string.is_importable():
                try:
                    project_string = StringRegistryService.import_external_string_to_project(
                        project=project,
                        external_string=external_string,
                        created_by=created_by
                    )
                    created_project_strings[row['external_platform_id']] = project_string

                    if project_string.id:
                        import_status = 'imported'
                        stats['created'] += 1
                    else:
                        import_status = 'updated'
                        stats['updated'] += 1

                except Exception as e:
                    logger.warning(f"Failed to import external_string {external_string.id}: {str(e)}")
                    import_status = 'failed'
                    validation_result['errors'].append({
                        'type': 'import_failed',
                        'message': f"Import to project failed: {str(e)}"
                    })

            # Build result
            row_result = {
                'row_number': row['row_number'],
                'string_value': row['string_value'],
                'external_platform_id': row['external_platform_id'],
                'entity_name': entity_name,
                'validation_status': external_string.validation_status,
                'external_string_id': external_string.id,
                'project_string_id': project_string.id if project_string else None,
                'import_status': import_status,
                'errors': validation_result.get('errors', []),
                'warnings': validation_result.get('warnings', [])
            }

            results.append(row_result)

            # Update stats
            if validation_result.get('should_skip'):
                stats['skipped_rows'] += 1
            else:
                stats['processed_rows'] += 1

            if external_string.validation_status == 'valid':
                stats['valid'] += 1
            elif external_string.validation_status == 'warning':
                stats['warnings'] += 1
                stats['valid'] += 1
            elif external_string.validation_status == 'invalid':
                stats['failed'] += 1

        return {
            'summary': stats,
            'results': results
        }

    @extend_schema(
        tags=["String Registry"],
        methods=['post'],
        request=SelectiveImportRequestSerializer,
        responses={200: SelectiveImportResponseSerializer},
        summary="Selectively import existing ExternalStrings to project",
        description="""
        Import specific ExternalStrings (by ID) into a project as Strings.

        **Use Case**: Users previously validated strings and now want to import specific ones.

        **Workflow:**
        1. User calls `/validate/` to validate strings
        2. User reviews validation results (valid, invalid, warnings)
        3. User calls this endpoint with IDs of valid strings to import

        **Request:**
        - `project_id`: Target project ID
        - `external_string_ids`: Array of ExternalString IDs to import

        **Process:**
        - Validates each ExternalString is importable (valid/warning status, not already imported)
        - Creates String for each valid ExternalString
        - Marks ExternalString as imported
        - Handles duplicates (updates existing String)

        **Response includes:**
        - Summary: {requested, imported, failed}
        - Detailed results per ExternalString
        """,
    )
    @action(detail=False, methods=['post'], url_path='import-selected')
    def import_selected(self, request, workspace_id=None, **kwargs):
        """Import selected ExternalStrings to a project."""
        from django.utils import timezone

        # Validate workspace access
        workspace = self.get_validated_workspace()

        # Validate request
        serializer = SelectiveImportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data['project_id']
        external_string_ids = serializer.validated_data['external_string_ids']

        try:
            # Get project
            project = Project.objects.get(id=project_id, workspace=workspace)

            # Get ExternalStrings
            external_strings = ExternalString.objects.filter(
                id__in=external_string_ids,
                workspace=workspace
            )

            if external_strings.count() != len(external_string_ids):
                found_ids = set(external_strings.values_list('id', flat=True))
                missing_ids = set(external_string_ids) - found_ids
                return Response(
                    {'error': f"Some ExternalStrings not found: {list(missing_ids)}"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Process imports
            results = []
            stats = {
                'requested': len(external_string_ids),
                'imported': 0,
                'updated': 0,
                'failed': 0,
                'already_imported': 0
            }

            for ext_string in external_strings:
                # Check if platform is assigned to project
                if not project.platforms.filter(id=ext_string.platform_id).exists():
                    results.append({
                        'external_string_id': ext_string.id,
                        'external_platform_id': ext_string.external_platform_id,
                        'project_string_id': None,
                        'status': 'failed',
                        'message': f"Platform '{ext_string.platform.name}' not assigned to project"
                    })
                    stats['failed'] += 1
                    continue

                # Check if already imported
                if ext_string.imported_at:
                    results.append({
                        'external_string_id': ext_string.id,
                        'external_platform_id': ext_string.external_platform_id,
                        'project_string_id': ext_string.imported_to_project_string_id,
                        'status': 'already_imported',
                        'message': f"Already imported to String {ext_string.imported_to_project_string_id}"
                    })
                    stats['already_imported'] += 1
                    continue

                # Check if importable
                if not ext_string.is_importable():
                    results.append({
                        'external_string_id': ext_string.id,
                        'external_platform_id': ext_string.external_platform_id,
                        'project_string_id': None,
                        'status': 'failed',
                        'message': f"Cannot import (status: {ext_string.validation_status})"
                    })
                    stats['failed'] += 1
                    continue

                # Try to import
                try:
                    # Check if String already exists by external_platform_id
                    existing_ps = String.objects.filter(
                        workspace=workspace,
                        external_platform_id=ext_string.external_platform_id,
                        validation_source='external'
                    ).first()

                    if existing_ps:
                        # Update existing
                        existing_ps.value = ext_string.value
                        existing_ps.external_parent_id = ext_string.external_parent_id
                        existing_ps.validation_metadata = ext_string.validation_metadata
                        existing_ps.source_external_string = ext_string
                        existing_ps.save()

                        # Mark as imported
                        ext_string.imported_to_project_string = existing_ps
                        ext_string.imported_at = timezone.now()
                        ext_string.save()

                        results.append({
                            'external_string_id': ext_string.id,
                            'external_platform_id': ext_string.external_platform_id,
                            'project_string_id': existing_ps.id,
                            'status': 'updated',
                            'message': 'Updated existing String'
                        })
                        stats['updated'] += 1
                    else:
                        # Import new
                        project_string = StringRegistryService.import_external_string_to_project(
                            project=project,
                            external_string=ext_string,
                            created_by=request.user
                        )

                        results.append({
                            'external_string_id': ext_string.id,
                            'external_platform_id': ext_string.external_platform_id,
                            'project_string_id': project_string.id,
                            'status': 'imported',
                            'message': 'Successfully imported'
                        })
                        stats['imported'] += 1

                except Exception as e:
                    logger.error(f"Failed to import ExternalString {ext_string.id}: {str(e)}", exc_info=True)
                    results.append({
                        'external_string_id': ext_string.id,
                        'external_platform_id': ext_string.external_platform_id,
                        'project_string_id': None,
                        'status': 'failed',
                        'message': f"Import failed: {str(e)}"
                    })
                    stats['failed'] += 1

            return Response({
                'success': True,
                'summary': stats,
                'results': results
            }, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response(
                {'error': f"Project with id {project_id} not found in workspace"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error processing selective import: {str(e)}", exc_info=True)
            return Response(
                {'error': f"Selective import failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
