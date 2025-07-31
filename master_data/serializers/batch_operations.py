"""
Serializers for Phase 4 batch operations.
Handles batch updates, inheritance analysis, and conflict resolution.
"""

from rest_framework import serializers
from typing import Dict, List, Any
from .. import models


class StringUpdateSerializer(serializers.Serializer):
    """Serializer for individual string updates within a batch."""
    
    string_id = serializers.IntegerField(
        help_text="ID of the string to update"
    )
    field_updates = serializers.DictField(
        child=serializers.CharField(allow_null=True),
        help_text="Dictionary of field updates (field_name: new_value)"
    )
    metadata = serializers.DictField(
        required=False,
        default=dict,
        help_text="Additional metadata for the update"
    )

    def validate_string_id(self, value):
        """Validate that string exists and user has access."""
        request = self.context.get('request')
        if request:
            try:
                string_obj = models.String.objects.get(id=value)
                # Check workspace access
                if hasattr(request, 'user') and not request.user.is_superuser:
                    if not request.user.has_workspace_access(string_obj.workspace):
                        raise serializers.ValidationError(
                            "Access denied to string's workspace"
                        )
                return value
            except models.String.DoesNotExist:
                raise serializers.ValidationError("String does not exist")
        return value


class BatchUpdateOptionsSerializer(serializers.Serializer):
    """Serializer for batch update options."""
    
    validate_inheritance = serializers.BooleanField(
        default=True,
        help_text="Whether to validate inheritance constraints"
    )
    auto_update_children = serializers.BooleanField(
        default=True,
        help_text="Whether to automatically update child strings"
    )
    create_backup = serializers.BooleanField(
        default=True,
        help_text="Whether to create a backup before updating"
    )
    dry_run = serializers.BooleanField(
        default=False,
        help_text="Whether to perform validation only without applying changes"
    )


class StringBatchUpdateRequestSerializer(serializers.Serializer):
    """Serializer for batch string update requests."""
    
    updates = serializers.ListField(
        child=StringUpdateSerializer(),
        min_length=1,
        max_length=1000,
        help_text="List of string updates to apply"
    )
    options = BatchUpdateOptionsSerializer(
        required=False,
        default=dict,
        help_text="Batch update options"
    )

    def validate_updates(self, value):
        """Validate the list of updates."""
        if not value:
            raise serializers.ValidationError("At least one update is required")
        
        # Check for duplicate string IDs
        string_ids = [update['string_id'] for update in value]
        if len(string_ids) != len(set(string_ids)):
            raise serializers.ValidationError("Duplicate string IDs in updates")
        
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        updates = attrs.get('updates', [])
        
        # Validate all strings belong to same workspace
        request = self.context.get('request')
        if request and updates:
            string_ids = [update['string_id'] for update in updates]
            strings = models.String.objects.filter(id__in=string_ids)
            
            workspaces = strings.values_list('workspace_id', flat=True).distinct()
            if len(workspaces) > 1:
                raise serializers.ValidationError(
                    "All strings must belong to the same workspace"
                )
        
        return attrs


class InheritanceImpactRequestSerializer(serializers.Serializer):
    """Serializer for inheritance impact analysis requests."""
    
    updates = serializers.ListField(
        child=StringUpdateSerializer(),
        min_length=1,
        max_length=500,
        help_text="List of proposed updates to analyze"
    )
    depth = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=20,
        help_text="Maximum inheritance depth to analyze"
    )


class ConflictSerializer(serializers.Serializer):
    """Serializer for conflict information."""
    
    string_id = serializers.IntegerField()
    conflict_type = serializers.ChoiceField(
        choices=[
            ('inheritance', 'Inheritance'),
            ('concurrent_edit', 'Concurrent Edit'),
            ('validation', 'Validation'),
            ('duplicate_value', 'Duplicate Value'),
            ('circular_inheritance', 'Circular Inheritance'),
        ]
    )
    message = serializers.CharField()
    suggested_resolution = serializers.CharField(required=False, allow_null=True)


class InheritanceUpdateSerializer(serializers.Serializer):
    """Serializer for inheritance update information."""
    
    string_id = serializers.IntegerField()
    parent_string_id = serializers.IntegerField()
    updated_fields = serializers.ListField(child=serializers.CharField())
    inherited_values = serializers.DictField()


class BatchUpdateErrorSerializer(serializers.Serializer):
    """Serializer for batch update errors."""
    
    string_id = serializers.IntegerField()
    field = serializers.CharField(required=False, allow_null=True)
    message = serializers.CharField()
    code = serializers.CharField()


class StringBatchUpdateResponseSerializer(serializers.Serializer):
    """Serializer for batch string update responses."""
    
    success = serializers.BooleanField()
    updated_strings = serializers.ListField(child=serializers.IntegerField())
    affected_strings = serializers.ListField(child=serializers.IntegerField())
    inheritance_updates = serializers.ListField(child=InheritanceUpdateSerializer())
    conflicts = serializers.ListField(child=ConflictSerializer())
    backup_id = serializers.CharField(required=False, allow_null=True)
    errors = serializers.ListField(child=BatchUpdateErrorSerializer())
    batch_id = serializers.CharField(required=False, allow_null=True)
    dry_run = serializers.BooleanField(required=False, default=False)


class AffectedStringSerializer(serializers.Serializer):
    """Serializer for affected string information in impact analysis."""
    
    string_id = serializers.IntegerField()
    string_value = serializers.CharField()
    parent_string_id = serializers.IntegerField(required=False, allow_null=True)
    level = serializers.IntegerField()
    update_type = serializers.ChoiceField(choices=[('direct', 'Direct'), ('inherited', 'Inherited')])
    affected_fields = serializers.ListField(child=serializers.CharField())
    new_values = serializers.DictField()
    children = serializers.ListField(child=serializers.IntegerField())


class ImpactSummarySerializer(serializers.Serializer):
    """Serializer for impact analysis summary."""
    
    direct_updates = serializers.IntegerField()
    inheritance_updates = serializers.IntegerField()
    total_affected = serializers.IntegerField()
    max_depth = serializers.IntegerField()


class WarningSerializer(serializers.Serializer):
    """Serializer for warnings in impact analysis."""
    
    string_id = serializers.IntegerField()
    warning_type = serializers.ChoiceField(
        choices=[
            ('deep_inheritance', 'Deep Inheritance'),
            ('many_children', 'Many Children'),
            ('circular_dependency', 'Circular Dependency'),
        ]
    )
    message = serializers.CharField()
    severity = serializers.ChoiceField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])


class BlockerSerializer(serializers.Serializer):
    """Serializer for blockers in impact analysis."""
    
    string_id = serializers.IntegerField()
    blocker = serializers.ChoiceField(
        choices=[
            ('missing_parent', 'Missing Parent'),
            ('circular_reference', 'Circular Reference'),
            ('invalid_field', 'Invalid Field'),
        ]
    )
    message = serializers.CharField()


class InheritanceImpactResponseSerializer(serializers.Serializer):
    """Serializer for inheritance impact analysis responses."""
    
    impact = ImpactSummarySerializer()
    affected_strings = serializers.ListField(child=AffectedStringSerializer())
    warnings = serializers.ListField(child=WarningSerializer())
    blockers = serializers.ListField(child=BlockerSerializer())


class StringHistoryEntrySerializer(serializers.Serializer):
    """Serializer for string history entries."""
    
    id = serializers.CharField()
    string_id = serializers.IntegerField()
    version = serializers.IntegerField()
    values = serializers.DictField()
    string_value = serializers.CharField()
    modified_by = serializers.CharField()
    modified_at = serializers.CharField()
    change_type = serializers.ChoiceField(
        choices=[
            ('direct_edit', 'Direct Edit'),
            ('inheritance_update', 'Inheritance Update'),
            ('batch_update', 'Batch Update'),
            ('regeneration', 'Regeneration'),
            ('rollback', 'Rollback'),
        ]
    )
    parent_version = serializers.CharField(required=False, allow_null=True)
    metadata = serializers.DictField()


class StringHistoryResponseSerializer(serializers.Serializer):
    """Serializer for string history responses."""
    
    history = serializers.ListField(child=StringHistoryEntrySerializer())


class RollbackTargetSerializer(serializers.Serializer):
    """Serializer for rollback target specification."""
    
    string_id = serializers.IntegerField(required=False, allow_null=True)
    version = serializers.IntegerField(required=False, allow_null=True)
    batch_id = serializers.CharField(required=False, allow_null=True)
    backup_id = serializers.CharField(required=False, allow_null=True)

    def validate(self, attrs):
        """Ensure appropriate target fields are provided for rollback type."""
        # This validation will be enhanced based on rollback_type in the parent serializer
        return attrs


class RollbackOptionsSerializer(serializers.Serializer):
    """Serializer for rollback options."""
    
    rollback_children = serializers.BooleanField(default=False)
    validate_inheritance = serializers.BooleanField(default=True)


class RollbackRequestSerializer(serializers.Serializer):
    """Serializer for rollback requests."""
    
    rollback_type = serializers.ChoiceField(
        choices=[
            ('single', 'Single String'),
            ('batch', 'Batch Operation'),
            ('backup', 'Backup Restore'),
        ]
    )
    target = RollbackTargetSerializer()
    options = RollbackOptionsSerializer(required=False, default=dict)

    def validate(self, attrs):
        """Validate target fields based on rollback type."""
        rollback_type = attrs['rollback_type']
        target = attrs['target']
        
        if rollback_type == 'single':
            if not target.get('string_id') or not target.get('version'):
                raise serializers.ValidationError(
                    "Single rollback requires string_id and version"
                )
        elif rollback_type == 'batch':
            if not target.get('batch_id'):
                raise serializers.ValidationError(
                    "Batch rollback requires batch_id"
                )
        elif rollback_type == 'backup':
            if not target.get('backup_id'):
                raise serializers.ValidationError(
                    "Backup rollback requires backup_id"
                )
        
        return attrs


class RollbackResponseSerializer(serializers.Serializer):
    """Serializer for rollback responses."""
    
    success = serializers.BooleanField()
    rolled_back_strings = serializers.ListField(child=serializers.IntegerField())
    message = serializers.CharField()


# Audit model serializers
class StringModificationSerializer(serializers.ModelSerializer):
    """Serializer for StringModification model."""
    
    modified_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = models.StringModification
        fields = [
            'id', 'string', 'version', 'field_updates', 'string_value',
            'original_values', 'modified_by', 'modified_by_name', 'modified_at',
            'change_type', 'batch_id', 'parent_version', 'metadata'
        ]
        read_only_fields = ['id', 'modified_at']
    
    def get_modified_by_name(self, obj):
        """Get human-readable name of the user who made the modification."""
        if obj.modified_by:
            return f"{obj.modified_by.first_name} {obj.modified_by.last_name}".strip() or obj.modified_by.username
        return None


class StringUpdateBatchSerializer(serializers.ModelSerializer):
    """Serializer for StringUpdateBatch model."""
    
    initiated_by_name = serializers.SerializerMethodField()
    progress_percentage = serializers.ReadOnlyField()
    is_complete = serializers.ReadOnlyField()
    
    class Meta:
        model = models.StringUpdateBatch
        fields = [
            'id', 'rule', 'field', 'initiated_by', 'initiated_by_name',
            'initiated_at', 'completed_at', 'status', 'total_strings',
            'processed_strings', 'failed_strings', 'backup_id', 'metadata',
            'progress_percentage', 'is_complete'
        ]
        read_only_fields = ['id', 'initiated_at', 'completed_at', 'progress_percentage', 'is_complete']
    
    def get_initiated_by_name(self, obj):
        """Get human-readable name of the user who initiated the batch."""
        if obj.initiated_by:
            return f"{obj.initiated_by.first_name} {obj.initiated_by.last_name}".strip() or obj.initiated_by.username
        return None


class StringInheritanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for StringInheritanceUpdate model."""
    
    parent_string_value = serializers.SerializerMethodField()
    child_string_value = serializers.SerializerMethodField()
    
    class Meta:
        model = models.StringInheritanceUpdate
        fields = [
            'id', 'parent_modification', 'child_string', 'inherited_fields',
            'applied_at', 'parent_string_value', 'child_string_value'
        ]
        read_only_fields = ['id', 'applied_at']
    
    def get_parent_string_value(self, obj):
        """Get the value of the parent string."""
        return obj.parent_modification.string.value
    
    def get_child_string_value(self, obj):
        """Get the value of the child string."""
        return obj.child_string.value