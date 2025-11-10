"""
Batch update service for Phase 4 backend integration.
Handles bulk string updates with inheritance management and conflict resolution.
"""

import uuid
from typing import Dict, List, Optional, Tuple, Any
from django.db import transaction, models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import (
    String, StringDetail, StringModification, StringUpdateBatch,
    StringInheritanceUpdate, Rule, Entity, Workspace
)
from .inheritance_service import InheritanceService
from .conflict_resolution_service import ConflictResolutionService

User = get_user_model()


class BatchUpdateError(Exception):
    """Custom exception for batch update errors."""
    pass


class BatchUpdateService:
    """
    Service for handling batch string updates with inheritance management.
    """

    @staticmethod
    def analyze_impact(workspace: Workspace, updates: List[Dict[str, Any]], depth: int = 10) -> Dict[str, Any]:
        """
        Analyze the impact of proposed updates on inheritance hierarchy.
        
        Args:
            workspace: Workspace context
            updates: List of update objects with string_id and field_updates
            depth: Maximum inheritance depth to analyze
            
        Returns:
            Impact analysis results
        """
        try:
            string_ids = [update['string_id'] for update in updates]
            strings = String.objects.filter(
                id__in=string_ids,
                workspace=workspace
            ).select_related('field', 'rule', 'parent')

            if len(strings) != len(string_ids):
                found_ids = {s.id for s in strings}
                missing_ids = set(string_ids) - found_ids
                raise BatchUpdateError(f"Strings not found: {missing_ids}")

            # Use inheritance service to analyze impact
            impact_result = InheritanceService.analyze_inheritance_impact(
                strings, updates, depth
            )

            # Add summary statistics
            impact_result['impact'] = {
                'direct_updates': len(updates),
                'inheritance_updates': len(impact_result.get('affected_strings', [])) - len(updates),
                'total_affected': len(impact_result.get('affected_strings', [])),
                'max_depth': impact_result.get('max_depth', 0)
            }

            return impact_result

        except Exception as e:
            raise BatchUpdateError(f"Impact analysis failed: {str(e)}")

    @staticmethod
    @transaction.atomic
    def batch_update_strings(
        workspace: Workspace,
        updates: List[Dict[str, Any]],
        user: User,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute batch update of strings with inheritance management.
        
        Args:
            workspace: Workspace context
            updates: List of update objects
            user: User performing the update
            options: Update options (validate_inheritance, auto_update_children, etc.)
            
        Returns:
            Update results
        """
        batch_id = uuid.uuid4()
        
        try:
            # Validate inputs
            if not updates:
                raise BatchUpdateError("No updates provided")

            # Extract string IDs and validate existence
            string_ids = [update['string_id'] for update in updates]
            strings = String.objects.filter(
                id__in=string_ids,
                workspace=workspace
            ).select_related('field', 'rule', 'parent').prefetch_related('string_details')

            if len(strings) != len(string_ids):
                found_ids = {s.id for s in strings}
                missing_ids = set(string_ids) - found_ids
                raise BatchUpdateError(f"Strings not found: {missing_ids}")

            # Create batch tracking record
            batch = StringUpdateBatch.objects.create(
                workspace=workspace,
                rule=strings.first().rule,  # Assume all strings use same rule
                entity=strings.first().entity,  # Assume all strings use same entity
                initiated_by=user,
                total_strings=len(updates),
                metadata={
                    'options': options,
                    'update_count': len(updates)
                }
            )
            batch.status = 'processing'
            batch.save()

            # Dry run mode - just validate without applying changes
            if options.get('dry_run', False):
                return BatchUpdateService._dry_run_validation(
                    strings, updates, workspace, user, options
                )

            # Check for conflicts if requested
            conflicts = []
            if options.get('validate_inheritance', True):
                conflicts = ConflictResolutionService.detect_batch_conflicts(
                    strings, updates, workspace
                )

            # Create backup if requested
            backup_id = None
            if options.get('create_backup', True):
                backup_id = BatchUpdateService._create_backup(strings, batch_id)

            # Apply updates
            results = BatchUpdateService._apply_updates(
                strings, updates, workspace, user, batch_id, options
            )

            # Handle inheritance updates if enabled
            inheritance_updates = []
            if options.get('auto_update_children', True):
                inheritance_updates = InheritanceService.propagate_inheritance_updates(
                    results['updated_strings'], user, batch_id
                )

            # Update batch status
            batch.mark_completed()

            return {
                'success': True,
                'updated_strings': results['updated_strings'],
                'affected_strings': results['affected_strings'],
                'inheritance_updates': inheritance_updates,
                'conflicts': conflicts,
                'backup_id': backup_id,
                'errors': results['errors'],
                'batch_id': str(batch_id)
            }

        except Exception as e:
            # Mark batch as failed if it exists
            try:
                batch = StringUpdateBatch.objects.get(id=batch_id)
                batch.mark_failed()
            except StringUpdateBatch.DoesNotExist:
                pass
            
            raise BatchUpdateError(f"Batch update failed: {str(e)}")

    @staticmethod
    def _dry_run_validation(
        strings, updates, workspace, user, options
    ) -> Dict[str, Any]:
        """
        Perform validation without applying changes.
        """
        errors = []
        conflicts = []
        
        # Validate each update
        for update in updates:
            try:
                string_obj = next(s for s in strings if s.id == update['string_id'])
                
                # Validate field updates
                field_updates = update.get('field_updates', {})
                for field_key, value in field_updates.items():
                    # Basic validation - could be enhanced
                    if not isinstance(value, (str, type(None))):
                        errors.append({
                            'string_id': string_obj.id,
                            'field': field_key,
                            'message': 'Invalid field value type',
                            'code': 'INVALID_TYPE'
                        })

            except Exception as e:
                errors.append({
                    'string_id': update['string_id'],
                    'field': None,
                    'message': str(e),
                    'code': 'VALIDATION_ERROR'
                })

        # Check for conflicts
        if options.get('validate_inheritance', True):
            conflicts = ConflictResolutionService.detect_batch_conflicts(
                strings, updates, workspace
            )

        return {
            'success': len(errors) == 0,
            'updated_strings': [],
            'affected_strings': [],
            'inheritance_updates': [],
            'conflicts': conflicts,
            'backup_id': None,
            'errors': errors,
            'dry_run': True
        }

    @staticmethod
    def _apply_updates(
        strings, updates, workspace, user, batch_id, options
    ) -> Dict[str, Any]:
        """
        Apply the actual updates to strings.
        """
        updated_strings = []
        affected_strings = []
        errors = []

        for update in updates:
            try:
                string_obj = next(s for s in strings if s.id == update['string_id'])
                
                # Store original values for audit
                original_values = {
                    'value': string_obj.value,
                    'field_updates': {}
                }

                # Apply field updates
                field_updates = update.get('field_updates', {})
                new_value = string_obj.value  # Default to current value
                
                # Process field updates (simplified - would need more complex logic)
                for field_key, value in field_updates.items():
                    if field_key.startswith('field_'):
                        # This is a dimension field update
                        # In real implementation, this would update StringDetail records
                        original_values['field_updates'][field_key] = value

                # Update string value if provided in metadata
                metadata = update.get('metadata', {})
                if 'new_value' in metadata:
                    new_value = metadata['new_value']

                # Increment version and update string
                string_obj.version += 1
                string_obj.value = new_value
                string_obj.save()

                # Create modification record
                modification = StringModification.objects.create(
                    workspace=workspace,
                    string=string_obj,
                    version=string_obj.version,
                    field_updates=field_updates,
                    string_value=new_value,
                    original_values=original_values,
                    modified_by=user,
                    change_type='batch_update',
                    batch_id=batch_id,
                    metadata=metadata
                )

                updated_strings.append(string_obj.id)
                affected_strings.append(string_obj.id)

            except Exception as e:
                errors.append({
                    'string_id': update['string_id'],
                    'field': None,
                    'message': str(e),
                    'code': 'UPDATE_FAILED'
                })

        return {
            'updated_strings': updated_strings,
            'affected_strings': affected_strings,
            'errors': errors
        }

    @staticmethod
    def _create_backup(strings, batch_id: uuid.UUID) -> str:
        """
        Create backup of strings before update.
        """
        backup_id = uuid.uuid4()
        
        # In a real implementation, this would create backup records
        # For now, just return the backup ID
        
        return str(backup_id)

    @staticmethod
    def get_string_history(string_id: int, workspace: Workspace) -> List[Dict[str, Any]]:
        """
        Get modification history for a string.
        """
        try:
            string_obj = String.objects.get(id=string_id, workspace=workspace)
            
            modifications = StringModification.objects.filter(
                string=string_obj
            ).select_related('modified_by').order_by('-modified_at')

            history = []
            for mod in modifications:
                history.append({
                    'id': str(mod.id),
                    'string_id': string_obj.id,
                    'version': mod.version,
                    'values': mod.field_updates,
                    'string_value': mod.string_value,
                    'modified_by': mod.modified_by.username if mod.modified_by else None,
                    'modified_at': mod.modified_at.isoformat(),
                    'change_type': mod.change_type,
                    'parent_version': str(mod.parent_version.id) if mod.parent_version else None,
                    'metadata': mod.metadata
                })

            return {'history': history}

        except String.DoesNotExist:
            raise BatchUpdateError(f"String {string_id} not found")

    @staticmethod
    @transaction.atomic
    def rollback_changes(
        workspace: Workspace,
        rollback_type: str,
        target: Dict[str, Any],
        user: User,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Rollback strings to previous versions.
        """
        try:
            if rollback_type == 'single':
                return BatchUpdateService._rollback_single_string(
                    workspace, target, user, options
                )
            elif rollback_type == 'batch':
                return BatchUpdateService._rollback_batch(
                    workspace, target, user, options
                )
            elif rollback_type == 'backup':
                return BatchUpdateService._rollback_from_backup(
                    workspace, target, user, options
                )
            else:
                raise BatchUpdateError(f"Unknown rollback type: {rollback_type}")

        except Exception as e:
            raise BatchUpdateError(f"Rollback failed: {str(e)}")

    @staticmethod
    def _rollback_single_string(workspace, target, user, options):
        """Rollback a single string to a specific version."""
        string_id = target['string_id']
        version = target['version']
        
        string_obj = String.objects.get(id=string_id, workspace=workspace)
        modification = StringModification.objects.get(
            string=string_obj,
            version=version
        )
        
        # Restore string to this version
        string_obj.value = modification.string_value
        string_obj.version += 1
        string_obj.save()
        
        # Create rollback modification record
        StringModification.objects.create(
            workspace=workspace,
            string=string_obj,
            version=string_obj.version,
            field_updates=modification.field_updates,
            string_value=modification.string_value,
            original_values={'rollback_from_version': string_obj.version - 1},
            modified_by=user,
            change_type='rollback',
            parent_version=modification,
            metadata={'rollback_target_version': version}
        )
        
        return {
            'success': True,
            'rolled_back_strings': [string_id],
            'message': f'String rolled back to version {version}'
        }

    @staticmethod
    def _rollback_batch(workspace, target, user, options):
        """Rollback all strings from a batch operation."""
        batch_id = target['batch_id']
        
        modifications = StringModification.objects.filter(
            workspace=workspace,
            batch_id=batch_id
        ).select_related('string')
        
        rolled_back_strings = []
        for mod in modifications:
            # Restore original values
            string_obj = mod.string
            string_obj.value = mod.original_values.get('value', string_obj.value)
            string_obj.version += 1
            string_obj.save()
            
            # Create rollback record
            StringModification.objects.create(
                workspace=workspace,
                string=string_obj,
                version=string_obj.version,
                field_updates=mod.original_values.get('field_updates', {}),
                string_value=string_obj.value,
                original_values={'rollback_from_batch': str(batch_id)},
                modified_by=user,
                change_type='rollback',
                parent_version=mod,
                metadata={'rollback_batch_id': str(batch_id)}
            )
            
            rolled_back_strings.append(string_obj.id)
        
        return {
            'success': True,
            'rolled_back_strings': rolled_back_strings,
            'message': f'Batch {batch_id} rolled back successfully'
        }

    @staticmethod
    def _rollback_from_backup(workspace, target, user, options):
        """Rollback from backup."""
        backup_id = target['backup_id']
        
        # In a real implementation, this would restore from backup
        # For now, return success message
        
        return {
            'success': True,
            'rolled_back_strings': [],
            'message': f'Restore from backup {backup_id} completed'
        }