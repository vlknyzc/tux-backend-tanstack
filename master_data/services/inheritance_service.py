"""
Inheritance service for Phase 4 backend integration.
Handles inheritance analysis and propagation in string hierarchies.
"""

import uuid
from typing import Dict, List, Optional, Set, Any
from django.db import transaction, models
from django.contrib.auth import get_user_model

from ..models import (
    String, StringDetail, StringModification, StringInheritanceUpdate
)

User = get_user_model()


class InheritanceError(Exception):
    """Custom exception for inheritance-related errors."""
    pass


class InheritanceService:
    """
    Service for managing string inheritance relationships and propagation.
    """

    @staticmethod
    def analyze_inheritance_impact(
        parent_strings,
        proposed_updates: List[Dict[str, Any]],
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze the impact of proposed updates on inheritance hierarchy.
        
        Args:
            parent_strings: QuerySet or list of parent strings being updated
            proposed_updates: List of proposed updates
            max_depth: Maximum depth to traverse
            
        Returns:
            Impact analysis with affected strings and warnings
        """
        try:
            affected_strings = []
            warnings = []
            blockers = []
            max_actual_depth = 0

            # Create mapping of string updates
            update_map = {
                update['string_id']: update for update in proposed_updates
            }

            for parent_string in parent_strings:
                if parent_string.id not in update_map:
                    continue

                update_data = update_map[parent_string.id]
                
                # Analyze this string's impact
                string_impact = InheritanceService._analyze_single_string_impact(
                    parent_string, update_data, max_depth
                )
                
                affected_strings.extend(string_impact['affected_strings'])
                warnings.extend(string_impact['warnings'])
                blockers.extend(string_impact['blockers'])
                max_actual_depth = max(max_actual_depth, string_impact['max_depth'])

            # Remove duplicates while preserving order
            seen_ids = set()
            unique_affected = []
            for item in affected_strings:
                if item['string_id'] not in seen_ids:
                    unique_affected.append(item)
                    seen_ids.add(item['string_id'])

            return {
                'affected_strings': unique_affected,
                'warnings': warnings,
                'blockers': blockers,
                'max_depth': max_actual_depth
            }

        except Exception as e:
            raise InheritanceError(f"Inheritance impact analysis failed: {str(e)}")

    @staticmethod
    def _analyze_single_string_impact(
        parent_string,
        update_data: Dict[str, Any],
        max_depth: int,
        current_depth: int = 0,
        visited: Optional[Set[int]] = None
    ) -> Dict[str, Any]:
        """
        Analyze impact for a single string and its descendants.
        """
        if visited is None:
            visited = set()

        # Prevent circular references
        if parent_string.id in visited or current_depth >= max_depth:
            return {
                'affected_strings': [],
                'warnings': [],
                'blockers': [],
                'max_depth': current_depth
            }

        visited.add(parent_string.id)

        affected_strings = []
        warnings = []
        blockers = []
        max_actual_depth = current_depth

        # Add the parent string itself
        affected_strings.append({
            'string_id': parent_string.id,
            'string_value': parent_string.value,
            'parent_string_id': parent_string.parent.id if parent_string.parent else None,
            'level': current_depth,
            'update_type': 'direct' if current_depth == 0 else 'inherited',
            'affected_fields': list(update_data.get('field_updates', {}).keys()),
            'new_values': update_data.get('field_updates', {}),
            'children': []
        })

        # Get direct children
        children = String.objects.filter(
            parent=parent_string,
            workspace=parent_string.workspace
        ).select_related('field', 'parent')

        # Check for warnings
        if children.count() > 50:
            warnings.append({
                'string_id': parent_string.id,
                'warning_type': 'many_children',
                'message': f'String has {children.count()} children - large inheritance impact',
                'severity': 'medium' if children.count() < 100 else 'high'
            })

        if current_depth > 5:
            warnings.append({
                'string_id': parent_string.id,
                'warning_type': 'deep_inheritance',
                'message': f'Deep inheritance at level {current_depth}',
                'severity': 'medium' if current_depth < 8 else 'high'
            })

        # Analyze each child
        for child in children:
            try:
                # Check for circular dependencies
                if InheritanceService._has_circular_dependency(child, parent_string):
                    blockers.append({
                        'string_id': child.id,
                        'blocker': 'circular_reference',
                        'message': f'Circular dependency detected: {child.value} → {parent_string.value}'
                    })
                    continue

                # Recursively analyze child impact
                child_update = InheritanceService._generate_inherited_update(
                    child, update_data
                )
                
                child_impact = InheritanceService._analyze_single_string_impact(
                    child, child_update, max_depth, current_depth + 1, visited.copy()
                )

                affected_strings.extend(child_impact['affected_strings'])
                warnings.extend(child_impact['warnings'])
                blockers.extend(child_impact['blockers'])
                max_actual_depth = max(max_actual_depth, child_impact['max_depth'])

                # Add child ID to parent's children list
                affected_strings[0]['children'].append(child.id)

            except Exception as e:
                blockers.append({
                    'string_id': child.id,
                    'blocker': 'analysis_error',
                    'message': f'Error analyzing child: {str(e)}'
                })

        return {
            'affected_strings': affected_strings,
            'warnings': warnings,
            'blockers': blockers,
            'max_depth': max_actual_depth
        }

    @staticmethod
    def _generate_inherited_update(child_string, parent_update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an inherited update for a child string based on parent changes.
        """
        # In a real implementation, this would apply inheritance rules
        # For now, we'll propagate all field updates that are inheritable
        
        parent_field_updates = parent_update.get('field_updates', {})
        inherited_updates = {}
        
        # Simple inheritance: child inherits all parent field updates
        # In practice, this would check inheritance rules and field compatibility
        for field_key, value in parent_field_updates.items():
            # Check if this field should be inherited
            if InheritanceService._should_inherit_field(child_string, field_key):
                inherited_updates[field_key] = value

        return {
            'string_id': child_string.id,
            'field_updates': inherited_updates,
            'metadata': {
                'inherited_from': parent_update.get('string_id'),
                'inheritance_type': 'automatic'
            }
        }

    @staticmethod
    def _should_inherit_field(child_string, field_key: str) -> bool:
        """
        Determine if a child string should inherit a specific field.
        """
        # In a real implementation, this would check:
        # - Field inheritance rules
        # - Child field compatibility
        # - Business logic constraints
        
        # For now, inherit all fields except those explicitly marked as non-inheritable
        non_inheritable_prefixes = ['local_', 'child_specific_']
        
        return not any(field_key.startswith(prefix) for prefix in non_inheritable_prefixes)

    @staticmethod
    def _has_circular_dependency(child_string, potential_parent) -> bool:
        """
        Check if making potential_parent a parent of child_string would create a circular dependency.
        """
        current = potential_parent.parent
        visited = {child_string.id}
        
        while current and current.id not in visited:
            if current.id == child_string.id:
                return True
            visited.add(current.id)
            current = current.parent
        
        return False

    @staticmethod
    @transaction.atomic
    def propagate_inheritance_updates(
        updated_string_ids: List[int],
        user: User,
        batch_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Propagate inheritance updates to child strings.
        
        Args:
            updated_string_ids: List of string IDs that were updated
            user: User performing the update
            batch_id: Batch operation ID
            
        Returns:
            List of inheritance update records
        """
        try:
            inheritance_updates = []
            
            # Get all updated strings with their modifications
            updated_strings = String.objects.filter(
                id__in=updated_string_ids
            ).select_related('workspace').prefetch_related('modifications')

            for updated_string in updated_strings:
                # Get the latest modification for this string
                latest_modification = updated_string.modifications.filter(
                    batch_id=batch_id
                ).order_by('-version').first()

                if not latest_modification:
                    continue

                # Get all direct children
                children = String.objects.filter(
                    parent=updated_string,
                    workspace=updated_string.workspace
                ).select_related('field')

                for child in children:
                    try:
                        # Generate inherited update
                        inherited_update = InheritanceService._apply_inheritance_to_child(
                            child, latest_modification, user, batch_id
                        )
                        
                        if inherited_update:
                            inheritance_updates.append(inherited_update)

                            # Recursively propagate to grandchildren
                            grandchild_updates = InheritanceService.propagate_inheritance_updates(
                                [child.id], user, batch_id
                            )
                            inheritance_updates.extend(grandchild_updates)

                    except Exception as e:
                        # Log error but continue with other children
                        inheritance_updates.append({
                            'string_id': child.id,
                            'parent_string_id': updated_string.id,
                            'updated_fields': [],
                            'inherited_values': {},
                            'error': str(e)
                        })

            return inheritance_updates

        except Exception as e:
            raise InheritanceError(f"Inheritance propagation failed: {str(e)}")

    @staticmethod
    def _apply_inheritance_to_child(
        child_string,
        parent_modification: StringModification,
        user: User,
        batch_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Apply inheritance updates to a specific child string.
        """
        try:
            parent_field_updates = parent_modification.field_updates
            inherited_fields = {}
            updated_fields = []

            # Determine which fields should be inherited
            for field_key, value in parent_field_updates.items():
                if InheritanceService._should_inherit_field(child_string, field_key):
                    inherited_fields[field_key] = value
                    updated_fields.append(field_key)

            # If no fields to inherit, skip this child
            if not inherited_fields:
                return None

            # Update the child string
            child_string.version += 1
            
            # In a real implementation, this would update the actual field values
            # For now, we'll just update the metadata
            child_string.generation_metadata.update({
                'last_inherited_from': str(parent_modification.string.id),
                'inherited_at': parent_modification.modified_at.isoformat(),
                'inherited_fields': list(inherited_fields.keys())
            })
            child_string.save()

            # Create modification record for the child
            child_modification = StringModification.objects.create(
                workspace=child_string.workspace,
                string=child_string,
                version=child_string.version,
                field_updates=inherited_fields,
                string_value=child_string.value,
                original_values={'inherited_from': str(parent_modification.id)},
                modified_by=user,
                change_type='inheritance_update',
                batch_id=batch_id,
                parent_version=parent_modification,
                metadata={
                    'inheritance_source': str(parent_modification.string.id),
                    'inherited_fields': updated_fields
                }
            )

            # Create inheritance tracking record
            StringInheritanceUpdate.objects.create(
                workspace=child_string.workspace,
                parent_modification=parent_modification,
                child_string=child_string,
                inherited_fields=inherited_fields
            )

            return {
                'string_id': child_string.id,
                'parent_string_id': parent_modification.string.id,
                'updated_fields': updated_fields,
                'inherited_values': inherited_fields
            }

        except Exception as e:
            raise InheritanceError(f"Failed to apply inheritance to child {child_string.id}: {str(e)}")

    @staticmethod
    def validate_inheritance_constraints(
        string_updates: List[Dict[str, Any]],
        workspace
    ) -> List[Dict[str, Any]]:
        """
        Validate inheritance constraints before applying updates.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            for update in string_updates:
                string_id = update['string_id']
                field_updates = update.get('field_updates', {})
                
                try:
                    string_obj = String.objects.get(id=string_id, workspace=workspace)
                    
                    # Check field compatibility
                    for field_key, value in field_updates.items():
                        compatibility_error = InheritanceService._check_field_compatibility(
                            string_obj, field_key, value
                        )
                        if compatibility_error:
                            errors.append({
                                'string_id': string_id,
                                'field': field_key,
                                'error': compatibility_error,
                                'error_type': 'field_compatibility'
                            })

                    # Check for potential orphans
                    if string_obj.parent and 'parent_id' in update:
                        new_parent_id = update['parent_id']
                        if new_parent_id is None:
                            # Check if removing parent would orphan children
                            children_count = String.objects.filter(parent=string_obj).count()
                            if children_count > 0:
                                errors.append({
                                    'string_id': string_id,
                                    'field': 'parent_id',
                                    'error': f'Removing parent would orphan {children_count} children',
                                    'error_type': 'orphan_prevention'
                                })

                except String.DoesNotExist:
                    errors.append({
                        'string_id': string_id,
                        'field': None,
                        'error': 'String not found',
                        'error_type': 'not_found'
                    })

        except Exception as e:
            errors.append({
                'string_id': None,
                'field': None,
                'error': f'Validation error: {str(e)}',
                'error_type': 'system_error'
            })

        return errors

    @staticmethod
    def _check_field_compatibility(string_obj, field_key: str, value: Any) -> Optional[str]:
        """
        Check if a field value is compatible with the string's configuration.
        """
        # In a real implementation, this would check:
        # - Field type constraints
        # - Value format validation
        # - Business rule compliance
        
        # Basic validation example
        if value is not None and not isinstance(value, (str, int, float, bool)):
            return f"Invalid value type for field {field_key}"
        
        if isinstance(value, str) and len(value) > 255:
            return f"Value too long for field {field_key} (max 255 characters)"
        
        return None