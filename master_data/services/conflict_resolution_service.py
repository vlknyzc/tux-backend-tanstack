"""
Conflict resolution service for Phase 4 backend integration.
Handles detection and resolution of conflicts in batch string updates.
"""

from typing import Dict, List, Optional, Any, Tuple
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import (
    String, StringDetail, StringModification, Rule, Field, Workspace
)

User = get_user_model()


class ConflictResolutionError(Exception):
    """Custom exception for conflict resolution errors."""
    pass


class ConflictResolutionService:
    """
    Service for detecting and resolving conflicts in string updates.
    """

    @staticmethod
    def detect_batch_conflicts(
        strings,
        updates: List[Dict[str, Any]],
        workspace: Workspace
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts in a batch of string updates.
        
        Args:
            strings: QuerySet or list of strings being updated
            updates: List of proposed updates
            workspace: Workspace context
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        try:
            # Create mapping for easy lookup
            update_map = {
                update['string_id']: update for update in updates
            }

            for string_obj in strings:
                if string_obj.id not in update_map:
                    continue

                update_data = update_map[string_obj.id]
                
                # Check for various conflict types
                string_conflicts = ConflictResolutionService._detect_string_conflicts(
                    string_obj, update_data, workspace
                )
                conflicts.extend(string_conflicts)

            # Check for cross-string conflicts
            cross_conflicts = ConflictResolutionService._detect_cross_string_conflicts(
                updates, workspace
            )
            conflicts.extend(cross_conflicts)

            return conflicts

        except Exception as e:
            raise ConflictResolutionError(f"Conflict detection failed: {str(e)}")

    @staticmethod
    def _detect_string_conflicts(
        string_obj,
        update_data: Dict[str, Any],
        workspace: Workspace
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts for a single string update.
        """
        conflicts = []

        try:
            # 1. Concurrent modification conflict
            metadata = update_data.get('metadata', {})
            original_string_uuid = metadata.get('original_string_uuid')
            
            if original_string_uuid and str(string_obj.string_uuid) != original_string_uuid:
                conflicts.append({
                    'string_id': string_obj.id,
                    'conflict_type': 'concurrent_edit',
                    'message': 'String was modified by another user since last read',
                    'suggested_resolution': 'Refresh and retry update'
                })

            # 2. Version conflict
            original_value = metadata.get('original_value')
            if original_value and string_obj.value != original_value:
                # Check if change was recent
                recent_modifications = StringModification.objects.filter(
                    string=string_obj,
                    modified_at__gte=timezone.now() - timezone.timedelta(minutes=5)
                ).exclude(
                    modified_by__username=metadata.get('modified_by', '')
                )

                if recent_modifications.exists():
                    latest_mod = recent_modifications.first()
                    conflicts.append({
                        'string_id': string_obj.id,
                        'conflict_type': 'concurrent_edit',
                        'message': f'String was recently modified by {latest_mod.modified_by.username}',
                        'suggested_resolution': 'Review recent changes and merge if needed'
                    })

            # 3. Inheritance conflict
            if string_obj.parent:
                parent_conflicts = ConflictResolutionService._check_inheritance_conflicts(
                    string_obj, update_data
                )
                conflicts.extend(parent_conflicts)

            # 4. Validation conflicts
            field_updates = update_data.get('field_updates', {})
            validation_conflicts = ConflictResolutionService._check_validation_conflicts(
                string_obj, field_updates, workspace
            )
            conflicts.extend(validation_conflicts)

        except Exception as e:
            conflicts.append({
                'string_id': string_obj.id,
                'conflict_type': 'validation',
                'message': f'Error during conflict detection: {str(e)}',
                'suggested_resolution': 'Check update data format'
            })

        return conflicts

    @staticmethod
    def _check_inheritance_conflicts(
        string_obj,
        update_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check for inheritance-related conflicts.
        """
        conflicts = []
        field_updates = update_data.get('field_updates', {})

        try:
            # Check if update conflicts with inherited values
            if string_obj.parent:
                # Get parent's current field values (simplified)
                parent_metadata = string_obj.parent.generation_metadata
                inherited_fields = parent_metadata.get('inherited_fields', [])

                for field_key, new_value in field_updates.items():
                    if field_key in inherited_fields:
                        # This field is inherited from parent - potential conflict
                        conflicts.append({
                            'string_id': string_obj.id,
                            'conflict_type': 'inheritance',
                            'message': f'Field {field_key} is inherited from parent and cannot be directly modified',
                            'suggested_resolution': 'Update parent string instead or override inheritance'
                        })

            # Check if update would break child inheritance
            children = String.objects.filter(parent=string_obj)
            if children.exists():
                for field_key, new_value in field_updates.items():
                    # Check if any children depend on this field
                    dependent_children = children.filter(
                        generation_metadata__inherited_fields__contains=[field_key]
                    )
                    
                    if dependent_children.exists():
                        conflicts.append({
                            'string_id': string_obj.id,
                            'conflict_type': 'inheritance',
                            'message': f'Changing {field_key} will affect {dependent_children.count()} child strings',
                            'suggested_resolution': 'Confirm inheritance propagation'
                        })

        except Exception as e:
            conflicts.append({
                'string_id': string_obj.id,
                'conflict_type': 'inheritance',
                'message': f'Error checking inheritance conflicts: {str(e)}',
                'suggested_resolution': 'Review inheritance configuration'
            })

        return conflicts

    @staticmethod
    def _check_validation_conflicts(
        string_obj,
        field_updates: Dict[str, Any],
        workspace: Workspace
    ) -> List[Dict[str, Any]]:
        """
        Check for validation conflicts in field updates.
        """
        conflicts = []

        try:
            for field_key, value in field_updates.items():
                # Basic type validation
                if value is not None and not isinstance(value, (str, int, float, bool, type(None))):
                    conflicts.append({
                        'string_id': string_obj.id,
                        'conflict_type': 'validation',
                        'message': f'Invalid value type for field {field_key}',
                        'suggested_resolution': 'Provide valid value type'
                    })

                # Length validation for string values
                if isinstance(value, str) and len(value) > 255:
                    conflicts.append({
                        'string_id': string_obj.id,
                        'conflict_type': 'validation',
                        'message': f'Value too long for field {field_key} (max 255 characters)',
                        'suggested_resolution': 'Shorten the value'
                    })

                # Check for empty required fields
                if value in [None, ''] and field_key.startswith('required_'):
                    conflicts.append({
                        'string_id': string_obj.id,
                        'conflict_type': 'validation',
                        'message': f'Required field {field_key} cannot be empty',
                        'suggested_resolution': 'Provide a valid value'
                    })

        except Exception as e:
            conflicts.append({
                'string_id': string_obj.id,
                'conflict_type': 'validation',
                'message': f'Validation error: {str(e)}',
                'suggested_resolution': 'Check field values and types'
            })

        return conflicts

    @staticmethod
    def _detect_cross_string_conflicts(
        updates: List[Dict[str, Any]],
        workspace: Workspace
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts across multiple string updates in the same batch.
        """
        conflicts = []

        try:
            # Check for duplicate values being created
            value_map = {}
            for update in updates:
                metadata = update.get('metadata', {})
                new_value = metadata.get('new_value')
                
                if new_value:
                    if new_value in value_map:
                        conflicts.append({
                            'string_id': update['string_id'],
                            'conflict_type': 'duplicate_value',
                            'message': f'Duplicate value "{new_value}" with string {value_map[new_value]}',
                            'suggested_resolution': 'Ensure unique values within batch'
                        })
                    else:
                        value_map[new_value] = update['string_id']

            # Check for circular inheritance
            inheritance_updates = [
                update for update in updates 
                if 'parent_id' in update.get('field_updates', {})
            ]
            
            circular_conflicts = ConflictResolutionService._detect_circular_inheritance(
                inheritance_updates, workspace
            )
            conflicts.extend(circular_conflicts)

        except Exception as e:
            conflicts.append({
                'string_id': None,
                'conflict_type': 'batch_validation',
                'message': f'Cross-string validation error: {str(e)}',
                'suggested_resolution': 'Review batch update configuration'
            })

        return conflicts

    @staticmethod
    def _detect_circular_inheritance(
        inheritance_updates: List[Dict[str, Any]],
        workspace: Workspace
    ) -> List[Dict[str, Any]]:
        """
        Detect circular inheritance dependencies in updates.
        """
        conflicts = []

        try:
            # Build inheritance graph from updates
            inheritance_graph = {}
            for update in inheritance_updates:
                string_id = update['string_id']
                new_parent_id = update['field_updates'].get('parent_id')
                inheritance_graph[string_id] = new_parent_id

            # Check for cycles
            for string_id in inheritance_graph:
                if ConflictResolutionService._has_cycle(string_id, inheritance_graph):
                    conflicts.append({
                        'string_id': string_id,
                        'conflict_type': 'circular_inheritance',
                        'message': f'Circular inheritance dependency detected starting from string {string_id}',
                        'suggested_resolution': 'Review parent-child relationships to eliminate cycles'
                    })

        except Exception as e:
            conflicts.append({
                'string_id': None,
                'conflict_type': 'inheritance',
                'message': f'Circular inheritance detection error: {str(e)}',
                'suggested_resolution': 'Review inheritance updates'
            })

        return conflicts

    @staticmethod
    def _has_cycle(start_id: int, graph: Dict[int, Optional[int]], visited: Optional[set] = None) -> bool:
        """
        Check if there's a cycle in the inheritance graph starting from start_id.
        """
        if visited is None:
            visited = set()

        if start_id in visited:
            return True

        visited.add(start_id)
        parent_id = graph.get(start_id)
        
        if parent_id and parent_id in graph:
            return ConflictResolutionService._has_cycle(parent_id, graph, visited)

        return False

    @staticmethod
    def resolve_conflict(
        conflict: Dict[str, Any],
        resolution_strategy: str,
        resolution_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve a specific conflict using the provided strategy.
        
        Args:
            conflict: The conflict to resolve
            resolution_strategy: Strategy to use (take_theirs, take_mine, merge, skip)
            resolution_data: Additional data needed for resolution
            
        Returns:
            Resolution result
        """
        try:
            string_id = conflict['string_id']
            conflict_type = conflict['conflict_type']

            if resolution_strategy == 'skip':
                return {
                    'string_id': string_id,
                    'resolution': 'skipped',
                    'message': 'Conflict skipped - no changes applied'
                }

            elif resolution_strategy == 'take_mine':
                return ConflictResolutionService._resolve_take_mine(
                    conflict, resolution_data
                )

            elif resolution_strategy == 'take_theirs':
                return ConflictResolutionService._resolve_take_theirs(
                    conflict, resolution_data
                )

            elif resolution_strategy == 'merge':
                return ConflictResolutionService._resolve_merge(
                    conflict, resolution_data
                )

            else:
                raise ConflictResolutionError(f"Unknown resolution strategy: {resolution_strategy}")

        except Exception as e:
            return {
                'string_id': conflict.get('string_id'),
                'resolution': 'failed',
                'message': f'Resolution failed: {str(e)}'
            }

    @staticmethod
    def _resolve_take_mine(
        conflict: Dict[str, Any],
        resolution_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve conflict by keeping user's changes.
        """
        return {
            'string_id': conflict['string_id'],
            'resolution': 'take_mine',
            'message': 'User changes will be applied, overriding conflicting values'
        }

    @staticmethod
    def _resolve_take_theirs(
        conflict: Dict[str, Any],
        resolution_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve conflict by keeping existing values.
        """
        return {
            'string_id': conflict['string_id'],
            'resolution': 'take_theirs',
            'message': 'Existing values will be kept, user changes discarded'
        }

    @staticmethod
    def _resolve_merge(
        conflict: Dict[str, Any],
        resolution_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve conflict by merging changes.
        """
        if not resolution_data or 'merged_values' not in resolution_data:
            raise ConflictResolutionError("Merge resolution requires merged_values in resolution_data")

        return {
            'string_id': conflict['string_id'],
            'resolution': 'merged',
            'message': 'Changes merged successfully',
            'merged_values': resolution_data['merged_values']
        }

    @staticmethod
    def auto_resolve_conflicts(
        conflicts: List[Dict[str, Any]],
        auto_resolution_rules: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Automatically resolve conflicts based on predefined rules.
        
        Args:
            conflicts: List of conflicts to resolve
            auto_resolution_rules: Mapping of conflict types to resolution strategies
            
        Returns:
            List of resolution results
        """
        resolutions = []

        for conflict in conflicts:
            conflict_type = conflict['conflict_type']
            strategy = auto_resolution_rules.get(conflict_type, 'skip')
            
            try:
                resolution = ConflictResolutionService.resolve_conflict(
                    conflict, strategy
                )
                resolutions.append(resolution)
            except Exception as e:
                resolutions.append({
                    'string_id': conflict.get('string_id'),
                    'resolution': 'failed',
                    'message': f'Auto-resolution failed: {str(e)}'
                })

        return resolutions

    @staticmethod
    def get_suggested_resolutions(conflict: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get suggested resolution strategies for a conflict.
        """
        conflict_type = conflict['conflict_type']
        suggestions = []

        if conflict_type == 'concurrent_edit':
            suggestions = [
                {
                    'type': 'take_mine',
                    'description': 'Keep your changes (overwrite other user\'s changes)',
                    'risk_level': 'high'
                },
                {
                    'type': 'take_theirs',
                    'description': 'Keep existing changes (discard your changes)',
                    'risk_level': 'low'
                },
                {
                    'type': 'merge',
                    'description': 'Manually merge both sets of changes',
                    'risk_level': 'medium'
                }
            ]
        elif conflict_type == 'inheritance':
            suggestions = [
                {
                    'type': 'skip',
                    'description': 'Skip this update to preserve inheritance',
                    'risk_level': 'low'
                },
                {
                    'type': 'take_mine',
                    'description': 'Override inheritance with your values',
                    'risk_level': 'medium'
                }
            ]
        elif conflict_type == 'validation':
            suggestions = [
                {
                    'type': 'skip',
                    'description': 'Skip this update due to validation error',
                    'risk_level': 'low'
                }
            ]
        else:
            suggestions = [
                {
                    'type': 'skip',
                    'description': 'Skip this update',
                    'risk_level': 'low'
                }
            ]

        return suggestions