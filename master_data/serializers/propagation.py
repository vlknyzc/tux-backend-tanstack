"""
Serializers for string propagation functionality.
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from typing import List, Dict, Any

from .. import models


class PropagationImpactRequestSerializer(serializers.Serializer):
    """Serializer for propagation impact analysis requests."""
    
    string_detail_updates = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of StringDetail updates to analyze"
    )
    max_depth = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        help_text="Maximum propagation depth to analyze"
    )
    
    def validate_string_detail_updates(self, value):
        """Validate the list of string detail updates."""
        if not value:
            raise serializers.ValidationError("At least one update must be provided")
        
        for i, update in enumerate(value):
            # Validate required fields
            if 'string_detail_id' not in update:
                raise serializers.ValidationError(
                    f"Update {i}: string_detail_id is required"
                )
            
            # Validate string_detail_id is integer
            try:
                int(update['string_detail_id'])
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Update {i}: string_detail_id must be an integer"
                )
            
            # Validate at least one field to update is provided
            update_fields = [k for k in update.keys() if k != 'string_detail_id']
            if not update_fields:
                raise serializers.ValidationError(
                    f"Update {i}: At least one field to update must be provided"
                )
        
        return value


class PropagationImpactResponseSerializer(serializers.Serializer):
    """Serializer for propagation impact analysis responses."""
    
    affected_strings = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of strings that would be affected"
    )
    warnings = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of warnings about the propagation"
    )
    conflicts = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of potential conflicts"
    )
    summary = serializers.DictField(
        help_text="Summary of the impact analysis"
    )


class StringDetailUpdateWithPropagationSerializer(serializers.ModelSerializer):
    """Enhanced StringDetail serializer with propagation control."""
    
    # Propagation control fields
    propagate = serializers.BooleanField(
        default=True,
        write_only=True,
        help_text="Whether to propagate changes to child strings"
    )
    propagation_depth = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        write_only=True,
        help_text="Maximum depth for propagation"
    )
    dry_run = serializers.BooleanField(
        default=False,
        write_only=True,
        help_text="Preview changes without applying them"
    )
    
    # Response fields
    propagation_summary = serializers.DictField(
        read_only=True,
        help_text="Summary of propagation results"
    )
    
    class Meta:
        model = models.StringDetail
        fields = [
            'id', 'string', 'dimension', 'dimension_value',
            'dimension_value_freetext', 'created', 'last_updated',
            # Propagation control
            'propagate', 'propagation_depth', 'dry_run',
            # Response
            'propagation_summary'
        ]
        read_only_fields = ['created', 'last_updated']
    
    def validate(self, attrs):
        """Enhanced validation with propagation awareness."""
        attrs = super().validate(attrs)
        
        # If dry_run is True, we don't need to validate as strictly
        if attrs.get('dry_run', False):
            return attrs
        
        # Standard StringDetail validation
        dimension_value = attrs.get('dimension_value')
        dimension_value_freetext = attrs.get('dimension_value_freetext')
        
        if not dimension_value and not dimension_value_freetext:
            raise serializers.ValidationError(
                "Either dimension_value or dimension_value_freetext must be provided"
            )
        
        if dimension_value and dimension_value_freetext:
            raise serializers.ValidationError(
                "Cannot specify both dimension_value and dimension_value_freetext"
            )
        
        return attrs


class PropagationJobSerializer(serializers.ModelSerializer):
    """Serializer for PropagationJob model."""
    
    triggered_by_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = models.PropagationJob
        fields = [
            'id', 'batch_id', 'workspace', 'workspace_name',
            'triggered_by', 'triggered_by_name', 'status',
            'started_at', 'completed_at', 'duration',
            'total_strings', 'processed_strings', 'failed_strings',
            'progress_percentage', 'success_rate',
            'max_depth', 'processing_method', 'metadata',
            'error_message', 'created', 'last_updated'
        ]
        read_only_fields = ['batch_id', 'created', 'last_updated']
    
    def get_triggered_by_name(self, obj) -> str:
        if obj.triggered_by:
            return f"{obj.triggered_by.first_name} {obj.triggered_by.last_name}".strip()
        return "System"
    
    def get_workspace_name(self, obj) -> str:
        return obj.workspace.name if obj.workspace else ""
    
    def get_duration(self, obj) -> str:
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            if total_seconds < 60:
                return f"{total_seconds}s"
            else:
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f"{minutes}m {seconds}s"
        return None
    
    def get_progress_percentage(self, obj) -> float:
        return obj.progress_percentage
    
    def get_success_rate(self, obj) -> float:
        return obj.success_rate


class PropagationErrorSerializer(serializers.ModelSerializer):
    """Serializer for PropagationError model."""
    
    job_batch_id = serializers.SerializerMethodField()
    string_value = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = models.PropagationError
        fields = [
            'id', 'job', 'job_batch_id', 'string', 'string_value',
            'string_detail', 'error_type', 'error_message', 'error_code',
            'context_data', 'retry_count', 'is_retryable',
            'resolved', 'resolved_at', 'resolved_by', 'resolved_by_name',
            'created', 'last_updated'
        ]
        read_only_fields = ['created', 'last_updated']
    
    def get_job_batch_id(self, obj) -> str:
        return str(obj.job.batch_id) if obj.job else ""
    
    def get_string_value(self, obj) -> str:
        return obj.string.value if obj.string else ""
    
    def get_resolved_by_name(self, obj) -> str:
        if obj.resolved_by:
            return f"{obj.resolved_by.first_name} {obj.resolved_by.last_name}".strip()
        return ""


class StringDetailBatchUpdateRequestSerializer(serializers.Serializer):
    """Serializer for batch StringDetail updates."""
    
    updates = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of StringDetail updates to apply"
    )
    options = serializers.DictField(
        default=dict,
        help_text="Batch update options"
    )
    
    def validate_updates(self, value):
        """Validate the batch updates."""
        if not value:
            raise serializers.ValidationError("At least one update must be provided")
        
        if len(value) > 100:  # Reasonable limit
            raise serializers.ValidationError("Too many updates in single batch (max 100)")
        
        for i, update in enumerate(value):
            if 'string_detail_id' not in update:
                raise serializers.ValidationError(
                    f"Update {i}: string_detail_id is required"
                )
            
            try:
                int(update['string_detail_id'])
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Update {i}: string_detail_id must be an integer"
                )
        
        return value
    
    def validate_options(self, value):
        """Validate batch update options."""
        # Validate known options
        valid_options = {
            'propagate', 'max_depth', 'parallel_processing',
            'error_handling', 'dry_run'
        }
        
        invalid_options = set(value.keys()) - valid_options
        if invalid_options:
            raise serializers.ValidationError(
                f"Invalid options: {', '.join(invalid_options)}"
            )
        
        # Validate option values
        if 'max_depth' in value:
            try:
                depth = int(value['max_depth'])
                if depth < 1 or depth > 50:
                    raise serializers.ValidationError(
                        "max_depth must be between 1 and 50"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError("max_depth must be an integer")
        
        if 'error_handling' in value:
            valid_strategies = ['continue', 'stop', 'rollback']
            if value['error_handling'] not in valid_strategies:
                raise serializers.ValidationError(
                    f"error_handling must be one of: {', '.join(valid_strategies)}"
                )
        
        return value


class StringDetailBatchUpdateResponseSerializer(serializers.Serializer):
    """Serializer for batch StringDetail update responses."""
    
    job_id = serializers.CharField(help_text="Batch job identifier")
    successful_updates = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of successful updates"
    )
    failed_updates = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of failed updates"
    )
    total_affected = serializers.IntegerField(
        help_text="Total number of strings affected"
    )
    processing_time = serializers.FloatField(
        help_text="Processing time in seconds"
    )
    summary = serializers.DictField(
        help_text="Summary of the batch operation"
    )


class PropagationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for PropagationSettings model."""
    
    user_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    
    class Meta:
        model = models.PropagationSettings
        fields = [
            'id', 'user', 'user_name', 'workspace', 'workspace_name',
            'settings', 'created', 'last_updated'
        ]
        read_only_fields = ['user', 'workspace', 'created', 'last_updated']
    
    def get_user_name(self, obj) -> str:
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return ""
    
    def get_workspace_name(self, obj) -> str:
        return obj.workspace.name if obj.workspace else ""
    
    def validate_settings(self, value):
        """Validate the settings dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Settings must be a dictionary")
        
        # Validate known settings
        valid_settings = {
            'default_propagation_enabled',
            'default_propagation_depth',
            'field_propagation_rules',
            'notification_preferences',
            'auto_preview_enabled'
        }
        
        for key in value.keys():
            if key not in valid_settings:
                # Allow unknown settings but log a warning
                pass
        
        # Validate specific setting values
        if 'default_propagation_depth' in value:
            try:
                depth = int(value['default_propagation_depth'])
                if depth < 1 or depth > 50:
                    raise serializers.ValidationError(
                        "default_propagation_depth must be between 1 and 50"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    "default_propagation_depth must be an integer"
                )
        
        if 'field_propagation_rules' in value:
            if not isinstance(value['field_propagation_rules'], dict):
                raise serializers.ValidationError(
                    "field_propagation_rules must be a dictionary"
                )
        
        return value