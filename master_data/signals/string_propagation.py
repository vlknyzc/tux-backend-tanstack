"""
Enhanced signal handlers for string propagation.
"""

import uuid
import logging
from typing import Dict, Any, Optional

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ..models import StringDetail, String
from ..services.propagation_service import PropagationService, PropagationError

logger = logging.getLogger('master_data.string_propagation')


# Store pre-save state for change detection
_pre_save_state = {}


@receiver(pre_save, sender=StringDetail)
def capture_stringdetail_pre_save_state(sender, instance, **kwargs):
    """
    Capture the state of StringDetail before save for change detection.
    """
    if instance.pk:  # Only for existing records
        try:
            original = StringDetail.objects.get(pk=instance.pk)
            _pre_save_state[instance.pk] = {
                'dimension_value_id': original.dimension_value_id,
                'dimension_value_freetext': original.dimension_value_freetext,
                'string_id': original.string_id,
                'dimension_id': original.dimension_id
            }
        except StringDetail.DoesNotExist:
            pass


@receiver(post_save, sender=StringDetail)
def enhanced_auto_regenerate_string_on_detail_update(sender, instance, created, **kwargs):
    """
    Enhanced automatic string regeneration when StringDetail is updated.
    Uses the new PropagationService for better change detection and propagation.
    """
    if created:
        # Clean up any stored state for new records
        _pre_save_state.pop(instance.pk, None)
        return
    
    # Get configuration
    config = getattr(settings, 'MASTER_DATA_CONFIG', {})
    
    if not config.get('AUTO_REGENERATE_STRINGS', True):
        logger.debug(f"Auto-regeneration disabled globally, skipping StringDetail {instance.id}")
        return
    
    # Prevent infinite recursion
    if getattr(instance, '_regenerating', False):
        logger.debug(f"Recursion guard active for StringDetail {instance.id}, skipping")
        return
    
    try:
        # Mark to prevent recursion
        instance._regenerating = True
        
        # Detect what changed
        changed_fields = _detect_stringdetail_changes(instance)
        
        if not changed_fields:
            logger.debug(f"No significant changes detected for StringDetail {instance.id}")
            return
        
        logger.info(
            f"Detected changes in StringDetail {instance.id}: {list(changed_fields.keys())}"
        )
        
        # Execute enhanced propagation
        _execute_enhanced_propagation(instance, changed_fields, config)
        
    except Exception as e:
        logger.error(f"Enhanced auto-regeneration failed for StringDetail {instance.id}: {str(e)}")
        
        # Create error record
        _log_propagation_error(instance, str(e), 'auto_regeneration_error')
        
        # Re-raise exception if strict mode is enabled
        if config.get('STRICT_AUTO_REGENERATION', False):
            raise
    finally:
        # Clean up
        _pre_save_state.pop(instance.pk, None)
        if hasattr(instance, '_regenerating'):
            delattr(instance, '_regenerating')


def _detect_stringdetail_changes(instance: StringDetail) -> Dict[str, Any]:
    """
    Detect what fields changed in a StringDetail update.
    """
    changed_fields = {}
    original_state = _pre_save_state.get(instance.pk, {})
    
    if not original_state:
        # If we don't have original state, assume all fields changed
        # This is a fallback for cases where pre_save didn't capture state
        logger.warning(f"No pre-save state found for StringDetail {instance.id}, assuming all fields changed")
        return {
            'dimension_value': {
                'old': None,
                'new': instance.dimension_value_id,
                'old_display': None,
                'new_display': instance.dimension_value.value if instance.dimension_value else None
            },
            'dimension_value_freetext': {
                'old': None,
                'new': instance.dimension_value_freetext
            }
        }
    
    # Check dimension_value change
    if original_state.get('dimension_value_id') != instance.dimension_value_id:
        # Get display values for better logging
        old_display = None
        if original_state.get('dimension_value_id'):
            try:
                from ..models import DimensionValue
                old_dim_value = DimensionValue.objects.get(id=original_state['dimension_value_id'])
                old_display = old_dim_value.value
            except DimensionValue.DoesNotExist:
                pass
        
        new_display = instance.dimension_value.value if instance.dimension_value else None
        
        changed_fields['dimension_value'] = {
            'old': original_state.get('dimension_value_id'),
            'new': instance.dimension_value_id,
            'old_display': old_display,
            'new_display': new_display
        }
    
    # Check dimension_value_freetext change
    if original_state.get('dimension_value_freetext') != instance.dimension_value_freetext:
        changed_fields['dimension_value_freetext'] = {
            'old': original_state.get('dimension_value_freetext'),
            'new': instance.dimension_value_freetext
        }
    
    return changed_fields


def _execute_enhanced_propagation(
    instance: StringDetail, 
    changed_fields: Dict[str, Any], 
    config: Dict[str, Any]
) -> None:
    """
    Execute enhanced propagation using PropagationService.
    """
    string_obj = instance.string
    batch_id = uuid.uuid4()
    
    logger.info(f"Starting enhanced propagation for String {string_obj.id} (batch: {batch_id})")
    
    try:
        with transaction.atomic():
            # Store original value for metadata
            old_value = string_obj.value
            
            # Regenerate the parent string
            string_obj.regenerate_value()
            
            logger.info(
                f"String {string_obj.id} regenerated: '{old_value}' -> '{string_obj.value}'"
            )
            
            # Handle inheritance propagation if enabled (simplified version)
            if config.get('ENABLE_INHERITANCE_PROPAGATION', True):
                try:
                    _propagate_to_children_simplified(string_obj, changed_fields, config)
                except Exception as propagation_error:
                    logger.error(f"Child propagation failed: {str(propagation_error)}")
                    # Don't fail the parent regeneration due to child propagation errors
            
            logger.info(f"Enhanced propagation completed for batch {batch_id}")
            
    except Exception as e:
        logger.error(f"Enhanced propagation failed for batch {batch_id}: {str(e)}")
        raise


def _propagate_with_enhanced_service(
    parent_string: String,
    changed_fields: Dict[str, Any],
    job,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use PropagationService for enhanced child string propagation.
    """
    max_depth = config.get('MAX_INHERITANCE_DEPTH', 10)
    parallel_processing = config.get('PARALLEL_PROPAGATION', False)
    
    try:
        # Analyze impact first
        impact = PropagationService._analyze_string_hierarchy_impact(
            parent_string, changed_fields, max_depth, parent_string.workspace
        )
        
        total_affected = len(impact['affected_strings'])
        successful = 0
        failed = 0
        
        logger.info(f"Propagation impact: {total_affected} strings affected")
        
        # Process each affected string
        for string_data in impact['affected_strings']:
            if string_data['level'] == 0:  # Skip parent (already processed)
                continue
                
            try:
                affected_string = String.objects.get(id=string_data['string_id'])
                
                # Apply inherited changes
                old_value = affected_string.value
                affected_string.regenerate_value()
                
                logger.info(
                    f"Child string {affected_string.id} regenerated: "
                    f"'{old_value}' -> '{affected_string.value}' (level {string_data['level']})"
                )
                
                successful += 1
                
            except Exception as child_error:
                logger.error(
                    f"Failed to propagate to child string {string_data['string_id']}: "
                    f"{str(child_error)}"
                )
                
                # Log specific error
                _log_propagation_error(
                    None, str(child_error), 'child_propagation_error',
                    job=job, string_id=string_data['string_id']
                )
                
                failed += 1
        
        return {
            'total_processed': total_affected - 1,  # Exclude parent
            'successful': successful,
            'failed': failed
        }
        
    except PropagationError as e:
        logger.error(f"PropagationService error: {str(e)}")
        _log_propagation_error(None, str(e), 'propagation_service_error', job=job)
        
        return {
            'total_processed': 0,
            'successful': 0,
            'failed': 1
        }


def _propagate_to_children_simplified(
    parent_string: String,
    changed_fields: Dict[str, Any],
    config: Dict[str, Any]
) -> None:
    """
    Simplified child propagation that properly inherits parent changes.
    """
    max_depth = config.get('MAX_INHERITANCE_DEPTH', 5)
    
    # Get direct children and propagate changes
    child_strings = parent_string.child_strings.all()
    
    for child in child_strings:
        try:
            old_value = child.value
            
            # Apply inherited changes to child's StringDetails
            inherited_changes_applied = _apply_inheritance_to_child(child, changed_fields)
            
            if inherited_changes_applied:
                # Only regenerate if we actually inherited some changes
                child.regenerate_value()
                logger.info(f"Child string {child.id} inherited changes and regenerated: '{old_value}' -> '{child.value}'")
            else:
                logger.info(f"Child string {child.id} has no inheritable changes, skipping")
            
            # Recursively propagate to grandchildren (with depth limit)
            if max_depth > 1:
                child_config = config.copy()
                child_config['MAX_INHERITANCE_DEPTH'] = max_depth - 1
                _propagate_to_children_simplified(child, changed_fields, child_config)
                
        except Exception as child_error:
            logger.error(f"Failed to propagate to child string {child.id}: {str(child_error)}")


def _apply_inheritance_to_child(child_string: String, parent_changed_fields: Dict[str, Any]) -> bool:
    """
    Apply parent changes to child string's StringDetails based on inheritance rules.
    
    Returns:
        bool: True if any changes were applied, False otherwise
    """
    changes_applied = False
    
    for field_key, change_info in parent_changed_fields.items():
        try:
            if field_key == 'dimension_value':
                # Handle dimension_value inheritance
                old_dimension_value_id = change_info.get('old')
                new_dimension_value_id = change_info.get('new')
                
                if old_dimension_value_id and new_dimension_value_id:
                    # Find parent's dimension from the change
                    from ..models import DimensionValue
                    new_dimension_value = DimensionValue.objects.get(id=new_dimension_value_id)
                    parent_dimension = new_dimension_value.dimension
                    
                    # Find child's StringDetail for the same dimension
                    child_string_detail = child_string.string_details.filter(
                        dimension=parent_dimension
                    ).first()
                    
                    if child_string_detail:
                        # Check if this field should be inherited
                        if _should_inherit_field(child_string, field_key, parent_dimension.name):
                            logger.info(f"Inheriting {parent_dimension.name}: {child_string_detail.dimension_value.value if child_string_detail.dimension_value else 'None'} -> {new_dimension_value.value}")
                            child_string_detail.dimension_value_id = new_dimension_value_id
                            child_string_detail.save()
                            changes_applied = True
                        else:
                            logger.info(f"Skipping inheritance of {parent_dimension.name} for child {child_string.id}")
                    
            elif field_key == 'dimension_value_freetext':
                # Handle freetext inheritance (more complex, skip for now)
                logger.info(f"Freetext inheritance not implemented yet for child {child_string.id}")
                
        except Exception as e:
            logger.error(f"Error applying inheritance of {field_key} to child {child_string.id}: {str(e)}")
    
    return changes_applied


def _should_inherit_field(child_string: String, field_key: str, dimension_name: str) -> bool:
    """
    Determine if a child string should inherit a specific field change.
    """
    from django.conf import settings
    
    # Get configuration
    config = getattr(settings, 'MASTER_DATA_CONFIG', {})
    field_rules = config.get('FIELD_PROPAGATION_RULES', {})
    
    # Check dimension-specific rule first
    dimension_rule = field_rules.get(f'{field_key}_{dimension_name}')
    if dimension_rule:
        return dimension_rule == 'inherit_always'
    
    # Check field-specific rule
    field_rule = field_rules.get(field_key, 'inherit_always')
    
    if field_rule == 'inherit_never':
        return False
    elif field_rule == 'inherit_always':
        return True
    elif field_rule == 'inherit_if_empty':
        # Check if child has empty value for this field (simplified logic)
        return True  # For now, always inherit
    
    return True  # Default to inherit


def _log_propagation_error(
    instance: Optional[StringDetail],
    error_message: str,
    error_type: str,
    job=None,
    string_id: Optional[int] = None
) -> None:
    """
    Log propagation errors for tracking and debugging.
    Simplified version that just logs to the logger instead of database.
    """
    logger.error(
        f"Propagation error ({error_type}): {error_message} "
        f"[StringDetail: {instance.id if instance else 'None'}, "
        f"String: {string_id if string_id else (instance.string.id if instance else 'None')}]"
    )


def _is_error_retryable(error_type: str) -> bool:
    """
    Determine if an error type is retryable.
    """
    retryable_types = [
        'database_error',
        'timeout_error',
        'unknown_error'
    ]
    
    non_retryable_types = [
        'circular_dependency',
        'validation_error',
        'permission_error'
    ]
    
    if error_type in retryable_types:
        return True
    elif error_type in non_retryable_types:
        return False
    else:
        return False  # Conservative default