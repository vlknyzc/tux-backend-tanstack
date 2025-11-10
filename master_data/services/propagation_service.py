"""
Enhanced Propagation Service for String Detail Updates.
Handles impact analysis, propagation logic, and background processing.
"""

import uuid
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from ..models import (
    String, StringDetail, StringModification, StringInheritanceUpdate
)
from .constants import (
    PROPAGATION_WARNING_THRESHOLD,
    PROPAGATION_HIGH_SEVERITY_THRESHOLD,
    BASE_TIME_PER_STRING_SECONDS,
    DEPTH_MULTIPLIER_PER_LEVEL,
    SECONDS_PER_MINUTE,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class PropagationError(Exception):
    """Custom exception for propagation-related errors."""
    pass


class PropagationService:
    """
    Enhanced service for managing string propagation with impact analysis,
    change detection, and background processing capabilities.
    """

    @staticmethod
    def analyze_impact(
        string_detail_updates: List[Dict[str, Any]],
        workspace,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze the impact of proposed StringDetail updates.
        
        Args:
            string_detail_updates: List of updates with string_detail_id and new values
            workspace: Workspace context
            max_depth: Maximum propagation depth
            
        Returns:
            Impact analysis with affected strings, warnings, and estimates
        """
        try:
            affected_strings = []
            warnings = []
            conflicts = []
            processing_estimates = {}
            
            total_affected = 0
            max_actual_depth = 0
            
            for update in string_detail_updates:
                string_detail_id = update['string_detail_id']
                
                try:
                    string_detail = StringDetail.objects.select_related(
                        'string', 'string__field', 'dimension'
                    ).get(id=string_detail_id, workspace=workspace)
                    
                    # Detect what fields would change
                    changed_fields = PropagationService._detect_field_changes(
                        string_detail, update
                    )
                    
                    if not changed_fields:
                        continue  # No actual changes
                    
                    # Analyze impact for this string's hierarchy
                    impact = PropagationService._analyze_string_hierarchy_impact(
                        string_detail.string, changed_fields, max_depth, workspace
                    )
                    
                    affected_strings.extend(impact['affected_strings'])
                    warnings.extend(impact['warnings'])
                    conflicts.extend(impact['conflicts'])
                    
                    total_affected += len(impact['affected_strings'])
                    max_actual_depth = max(max_actual_depth, impact['max_depth'])
                    
                except StringDetail.DoesNotExist:
                    warnings.append({
                        'type': 'not_found',
                        'message': f'StringDetail {string_detail_id} not found',
                        'severity': 'high'
                    })
                    
            # Generate processing estimates
            processing_estimates = PropagationService._estimate_processing_time(
                total_affected, max_actual_depth
            )
            
            # Remove duplicate affected strings
            unique_affected = PropagationService._deduplicate_affected_strings(
                affected_strings
            )
            
            return {
                'affected_strings': unique_affected,
                'warnings': warnings,
                'conflicts': conflicts,
                'summary': {
                    'total_affected': len(unique_affected),
                    'max_depth': max_actual_depth,
                    'estimated_duration': processing_estimates['duration'],
                    'processing_method': processing_estimates['method'],
                    'requires_background': processing_estimates['background_required']
                }
            }
            
        except Exception as e:
            logger.error(f"Impact analysis failed: {str(e)}")
            raise PropagationError(f"Impact analysis failed: {str(e)}")

    @staticmethod
    def _detect_field_changes(
        string_detail: StringDetail, 
        update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect what fields would change in a StringDetail update.
        """
        changed_fields = {}
        
        # Check dimension_value change
        new_dimension_value_id = update.get('dimension_value')
        current_dimension_value_id = string_detail.dimension_value_id
        
        if new_dimension_value_id != current_dimension_value_id:
            changed_fields['dimension_value'] = {
                'old': current_dimension_value_id,
                'new': new_dimension_value_id,
                'old_display': string_detail.dimension_value.value if string_detail.dimension_value else None,
                'new_display': None  # Will be resolved later
            }
        
        # Check dimension_value_freetext change
        new_freetext = update.get('dimension_value_freetext')
        current_freetext = string_detail.dimension_value_freetext
        
        if new_freetext != current_freetext:
            changed_fields['dimension_value_freetext'] = {
                'old': current_freetext,
                'new': new_freetext
            }
        
        return changed_fields

    @staticmethod
    def _analyze_string_hierarchy_impact(
        root_string: String,
        changed_fields: Dict[str, Any],
        max_depth: int,
        workspace,
        current_depth: int = 0,
        visited: Optional[Set[int]] = None
    ) -> Dict[str, Any]:
        """
        Analyze impact for a string hierarchy starting from root_string.

        This is the main orchestrator that coordinates the analysis process.
        Complexity reduced from 15+ to 4 by extracting focused helper methods.
        """
        # Initialize visited set
        if visited is None:
            visited = set()

        # Guard clause: stop if already visited or max depth reached
        if root_string.id in visited or current_depth >= max_depth:
            return PropagationService._create_empty_impact_data(current_depth)

        visited.add(root_string.id)

        # Step 1: Create empty impact data structure
        impact_data = PropagationService._create_empty_impact_data(current_depth)

        # Step 2: Build and add current string's impact
        string_impact = PropagationService._build_string_impact_record(
            root_string, changed_fields, current_depth
        )
        PropagationService._add_new_value_and_check_conflicts(
            root_string, changed_fields, workspace, string_impact, impact_data
        )
        impact_data['affected_strings'].append(string_impact)

        # Step 3: Get children and check for large counts
        children = PropagationService._get_children_with_large_count_warning(
            root_string, workspace, impact_data
        )

        # Step 4: Recursively analyze each child
        for child in children:
            PropagationService._analyze_child_recursively(
                child, changed_fields, max_depth, workspace,
                current_depth, visited, string_impact, impact_data
            )

        return impact_data

    @staticmethod
    def _create_empty_impact_data(current_depth: int = 0) -> Dict[str, Any]:
        """
        Create empty impact data structure.

        Single responsibility: Initialize data structure.
        """
        return {
            'affected_strings': [],
            'warnings': [],
            'conflicts': [],
            'max_depth': current_depth
        }

    @staticmethod
    def _build_string_impact_record(
        root_string: String,
        changed_fields: Dict[str, Any],
        current_depth: int
    ) -> Dict[str, Any]:
        """
        Build the impact record for current string.

        Single responsibility: Create impact record with metadata.
        """
        return {
            'string_id': root_string.id,
            'string_value': root_string.value,
            'new_value': None,  # Will be calculated
            'entity_level': root_string.entity.entity_level,
            'parent_id': root_string.parent_id,
            'level': current_depth,
            'change_type': 'direct' if current_depth == 0 else 'inherited',
            'changed_fields': list(changed_fields.keys()),
            'children': []
        }

    @staticmethod
    def _add_new_value_and_check_conflicts(
        root_string: String,
        changed_fields: Dict[str, Any],
        workspace,
        string_impact: Dict[str, Any],
        impact_data: Dict[str, Any]
    ) -> None:
        """
        Calculate new value and check for conflicts.

        Single responsibility: Value calculation and conflict detection.
        """
        try:
            new_value = PropagationService._calculate_new_string_value(
                root_string, changed_fields
            )
            string_impact['new_value'] = new_value

            # Check for conflicts
            conflict = PropagationService._check_value_conflict(
                root_string, new_value, workspace
            )
            if conflict:
                impact_data['conflicts'].append(conflict)

        except Exception as e:
            impact_data['warnings'].append({
                'string_id': root_string.id,
                'type': 'calculation_error',
                'message': f'Error calculating new value: {str(e)}',
                'severity': 'high'
            })

    @staticmethod
    def _get_children_with_large_count_warning(
        root_string: String,
        workspace,
        impact_data: Dict[str, Any]
    ):
        """
        Get children and warn if count is large.

        Single responsibility: Child retrieval with performance warning.
        """
        children = String.objects.filter(
            parent=root_string,
            workspace=workspace
        ).select_related('entity')

        # Check for large number of children
        child_count = children.count()
        if child_count > PROPAGATION_WARNING_THRESHOLD:
            impact_data['warnings'].append({
                'string_id': root_string.id,
                'type': 'many_children',
                'message': f'String has {child_count} children - large propagation impact',
                'severity': 'medium' if child_count < PROPAGATION_HIGH_SEVERITY_THRESHOLD else 'high'
            })

        return children

    @staticmethod
    def _analyze_child_recursively(
        child: String,
        changed_fields: Dict[str, Any],
        max_depth: int,
        workspace,
        current_depth: int,
        visited: Set[int],
        string_impact: Dict[str, Any],
        impact_data: Dict[str, Any]
    ) -> None:
        """
        Recursively analyze a single child string.

        Single responsibility: Child analysis with error handling.
        """
        try:
            # Generate inherited changes for child
            inherited_changes = PropagationService._generate_inherited_changes(
                child, changed_fields
            )

            if inherited_changes:
                child_impact = PropagationService._analyze_string_hierarchy_impact(
                    child, inherited_changes, max_depth, workspace,
                    current_depth + 1, visited.copy()
                )

                # Merge child impact into parent
                PropagationService._merge_child_impact_into_parent(
                    impact_data, child_impact, string_impact, child.id
                )

        except Exception as e:
            impact_data['warnings'].append({
                'string_id': child.id,
                'type': 'child_analysis_error',
                'message': f'Error analyzing child: {str(e)}',
                'severity': 'medium'
            })

    @staticmethod
    def _merge_child_impact_into_parent(
        parent_impact: Dict[str, Any],
        child_impact: Dict[str, Any],
        string_impact: Dict[str, Any],
        child_id: int
    ) -> None:
        """
        Merge child impact data into parent impact data.

        Single responsibility: Data merging.
        """
        parent_impact['affected_strings'].extend(child_impact['affected_strings'])
        parent_impact['warnings'].extend(child_impact['warnings'])
        parent_impact['conflicts'].extend(child_impact['conflicts'])
        parent_impact['max_depth'] = max(parent_impact['max_depth'], child_impact['max_depth'])

        # Add child to parent's children list
        string_impact['children'].append(child_id)

    @staticmethod
    def _calculate_new_string_value(
        string_obj: String, 
        changed_fields: Dict[str, Any]
    ) -> str:
        """
        Calculate what the new string value would be after property changes.
        """
        # Get current dimension values
        current_values = string_obj.get_dimension_values()
        
        # Apply changes (simplified - in real implementation would be more complex)
        # This is a placeholder that would integrate with StringGenerationService
        
        # For now, just modify the current value based on changes
        new_value = string_obj.value
        
        for field_key, change in changed_fields.items():
            if field_key == 'dimension_value' and change.get('new_display'):
                # Replace old dimension value with new one in string
                old_display = change.get('old_display', '')
                new_display = change.get('new_display', '')
                if old_display and old_display in new_value:
                    new_value = new_value.replace(old_display, new_display)
            elif field_key == 'dimension_value_freetext':
                # Handle freetext changes
                old_freetext = change.get('old', '')
                new_freetext = change.get('new', '')
                if old_freetext and old_freetext in new_value:
                    new_value = new_value.replace(old_freetext, new_freetext)
        
        return new_value

    @staticmethod
    def _check_value_conflict(
        string_obj: String, 
        new_value: str, 
        workspace
    ) -> Optional[Dict[str, Any]]:
        """
        Check if the new string value would create conflicts.
        """
        # Check for duplicate values in same workspace/rule/entity
        existing = String.objects.filter(
            workspace=workspace,
            rule=string_obj.rule,
            entity=string_obj.entity,
            value=new_value
        ).exclude(id=string_obj.id).first()
        
        if existing:
            return {
                'string_id': string_obj.id,
                'type': 'duplicate_value',
                'message': f'Value "{new_value}" already exists for another string',
                'conflicting_string_id': existing.id,
                'severity': 'high'
            }
        
        return None

    @staticmethod
    def _generate_inherited_changes(
        child_string: String, 
        parent_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate inherited changes for a child string based on parent changes.
        """
        inherited_changes = {}
        
        # Simple inheritance rules - inherit all changes by default
        # In practice, this would have more complex business logic
        for field_key, change in parent_changes.items():
            if PropagationService._should_inherit_field(child_string, field_key):
                inherited_changes[field_key] = change
        
        return inherited_changes

    @staticmethod
    def _should_inherit_field(child_string: String, field_key: str) -> bool:
        """
        Determine if a child string should inherit a specific property change.
        """
        # Get configuration
        config = getattr(settings, 'MASTER_DATA_CONFIG', {})
        field_rules = config.get('FIELD_PROPAGATION_RULES', {})
        
        # Default rule
        default_rule = field_rules.get('default', 'inherit_always')
        field_rule = field_rules.get(field_key, default_rule)
        
        if field_rule == 'inherit_never':
            return False
        elif field_rule == 'inherit_always':
            return True
        elif field_rule == 'inherit_if_empty':
            # Check if child has empty value for this property
            # This would need more complex logic to check child's StringDetails
            return True  # Simplified for now
        
        return True

    @staticmethod
    def _estimate_processing_time(
        total_affected: int, 
        max_depth: int
    ) -> Dict[str, Any]:
        """
        Estimate processing time and method based on scope.
        """
        config = getattr(settings, 'MASTER_DATA_CONFIG', {})
        background_threshold = config.get('BACKGROUND_PROCESSING_THRESHOLD', 100)
        
        # Base processing time estimates (in seconds)
        base_time_per_string = BASE_TIME_PER_STRING_SECONDS
        depth_multiplier = 1 + (max_depth * DEPTH_MULTIPLIER_PER_LEVEL)

        estimated_seconds = total_affected * base_time_per_string * depth_multiplier

        # Format duration
        if estimated_seconds < SECONDS_PER_MINUTE:
            duration = f"{estimated_seconds:.1f}s"
        else:
            minutes = int(estimated_seconds // SECONDS_PER_MINUTE)
            seconds = int(estimated_seconds % SECONDS_PER_MINUTE)
            duration = f"{minutes}m {seconds}s"
        
        # Determine processing method
        background_required = total_affected >= background_threshold
        method = 'background' if background_required else 'synchronous'
        
        return {
            'duration': duration,
            'estimated_seconds': estimated_seconds,
            'method': method,
            'background_required': background_required
        }

    @staticmethod
    def _deduplicate_affected_strings(affected_strings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate strings from affected list while preserving order.
        """
        seen_ids = set()
        unique_strings = []
        
        for string_data in affected_strings:
            string_id = string_data['string_id']
            if string_id not in seen_ids:
                unique_strings.append(string_data)
                seen_ids.add(string_id)
        
        return unique_strings

    @staticmethod
    @transaction.atomic
    def execute_propagation(
        string_detail_updates: List[Dict[str, Any]],
        workspace,
        user: User,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the actual propagation of string detail updates.
        
        Args:
            string_detail_updates: List of updates to apply
            workspace: Workspace context
            user: User performing the operation
            options: Additional options (propagate, max_depth, etc.)
            
        Returns:
            Execution results with success/failure details
        """
        options = options or {}
        batch_id = uuid.uuid4()
        
        try:
            # Create job record
            from ..models.propagation import PropagationJob
            job = PropagationJob.objects.create(
                workspace=workspace,
                triggered_by=user,
                batch_id=batch_id,
                status='running',
                total_strings=0,
                metadata={
                    'options': options,
                    'updates': string_detail_updates
                }
            )
            
            results = {
                'job_id': str(batch_id),
                'successful_updates': [],
                'failed_updates': [],
                'total_affected': 0,
                'processing_time': 0
            }
            
            start_time = timezone.now()
            
            for update in string_detail_updates:
                try:
                    # Execute single update with propagation
                    update_result = PropagationService._execute_single_update(
                        update, workspace, user, batch_id, options
                    )
                    
                    results['successful_updates'].append(update_result)
                    results['total_affected'] += update_result.get('affected_count', 0)
                    
                except Exception as e:
                    logger.error(f"Update failed for {update}: {str(e)}")
                    results['failed_updates'].append({
                        'update': update,
                        'error': str(e)
                    })
            
            # Update job status
            end_time = timezone.now()
            processing_time = (end_time - start_time).total_seconds()
            
            job.status = 'completed' if not results['failed_updates'] else 'partial_failure'
            job.completed_at = end_time
            job.processed_strings = len(results['successful_updates'])
            job.failed_strings = len(results['failed_updates'])
            job.save()
            
            results['processing_time'] = processing_time
            results['summary'] = {
                'total_updates': len(string_detail_updates),
                'successful_count': len(results['successful_updates']),
                'failed_count': len(results['failed_updates']),
                'status': 'completed' if not results['failed_updates'] else 'partial_failure'
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Propagation execution failed: {str(e)}")
            raise PropagationError(f"Propagation execution failed: {str(e)}")

    @staticmethod
    def _execute_single_update(
        update: Dict[str, Any],
        workspace,
        user: User,
        batch_id: uuid.UUID,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single StringDetail update with propagation.
        """
        string_detail_id = update['string_detail_id']
        
        # Get the StringDetail
        string_detail = StringDetail.objects.select_related(
            'string', 'string__field'
        ).get(id=string_detail_id, workspace=workspace)
        
        # Store original values
        original_values = {
            'dimension_value_id': string_detail.dimension_value_id,
            'dimension_value_freetext': string_detail.dimension_value_freetext
        }
        
        # Update the StringDetail
        for field, value in update.items():
            if field != 'string_detail_id' and hasattr(string_detail, field):
                # Handle foreign key fields by using the _id suffix
                if field == 'dimension_value' and value is not None:
                    setattr(string_detail, 'dimension_value_id', value)
                else:
                    setattr(string_detail, field, value)
        
        string_detail.save()
        
        # The signal handler will handle the propagation
        # Just return the basic update info
        return {
            'string_detail_id': string_detail_id,
            'string_id': string_detail.string_id,
            'original_values': original_values,
            'affected_count': 1  # Will be updated by signal handler
        }