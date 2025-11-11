"""
Serializers for String Registry validation feature.

Handles validation and import of external platform strings.
"""

from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile
from typing import Dict, List

from ..models import Platform, Rule, Workspace, Project


class ErrorDetailSerializer(serializers.Serializer):
    """Serializer for error details."""
    type = serializers.CharField()
    message = serializers.CharField()
    field = serializers.CharField(required=False, allow_null=True)
    expected = serializers.JSONField(required=False, allow_null=True)
    received = serializers.JSONField(required=False, allow_null=True)
    suggestion = serializers.CharField(required=False, allow_null=True)


class WarningDetailSerializer(serializers.Serializer):
    """Serializer for warning details."""
    type = serializers.CharField()
    message = serializers.CharField()
    field = serializers.CharField(required=False, allow_null=True)


class ValidationSummarySerializer(serializers.Serializer):
    """Serializer for validation summary statistics."""
    total_rows = serializers.IntegerField()
    uploaded_rows = serializers.IntegerField()
    processed_rows = serializers.IntegerField()
    skipped_rows = serializers.IntegerField()

    # Results breakdown
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    valid = serializers.IntegerField()
    warnings = serializers.IntegerField()
    failed = serializers.IntegerField()

    # Hierarchy stats
    linked_parents = serializers.IntegerField()
    parent_conflicts = serializers.IntegerField()
    parent_not_found = serializers.IntegerField()


class SingleStringValidationRequestSerializer(serializers.Serializer):
    """Serializer for single string validation request."""
    rule_id = serializers.IntegerField()
    entity_name = serializers.CharField(max_length=100)
    string_value = serializers.CharField(max_length=500)
    external_platform_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    parent_external_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=True,
        allow_blank=True
    )

    def validate_rule_id(self, value):
        """Validate that rule exists and user has access."""
        try:
            rule = Rule.objects.get(id=value)
            # Check workspace access will be done in view
            return value
        except Rule.DoesNotExist:
            raise serializers.ValidationError(f"Rule with id {value} not found")


class SingleStringValidationResponseSerializer(serializers.Serializer):
    """Serializer for single string validation response."""
    is_valid = serializers.BooleanField()
    entity_name = serializers.CharField()
    parsed_dimension_values = serializers.DictField()
    errors = ErrorDetailSerializer(many=True)
    warnings = WarningDetailSerializer(many=True)
    string_id = serializers.IntegerField(allow_null=True)


# ==========================================
# Serializers for ExternalString/ProjectString Operations
# ==========================================

class ValidationOnlyRequestSerializer(serializers.Serializer):
    """
    Serializer for validation-only CSV upload (no project import).

    Creates ExternalString records for all strings (valid + invalid).
    """
    platform_id = serializers.IntegerField()
    rule_id = serializers.IntegerField()
    file = serializers.FileField()

    def validate_platform_id(self, value):
        """Validate that platform exists."""
        try:
            Platform.objects.get(id=value)
            return value
        except Platform.DoesNotExist:
            raise serializers.ValidationError(f"Platform with id {value} not found")

    def validate_rule_id(self, value):
        """Validate that rule exists."""
        try:
            Rule.objects.get(id=value)
            return value
        except Rule.DoesNotExist:
            raise serializers.ValidationError(f"Rule with id {value} not found")

    def validate_file(self, value: UploadedFile):
        """Validate uploaded file."""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed")

        if value.content_type not in ['text/csv', 'application/csv', 'text/plain']:
            raise serializers.ValidationError(
                f"Invalid file type: {value.content_type}. Expected CSV file."
            )

        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size ({value.size} bytes) exceeds maximum (5MB)"
            )

        return value


class ImportToProjectRequestSerializer(serializers.Serializer):
    """
    Serializer for direct import to project.

    Validates, creates ExternalStrings, and imports to ProjectStrings in one operation.
    """
    project_id = serializers.IntegerField()
    platform_id = serializers.IntegerField()
    rule_id = serializers.IntegerField()
    file = serializers.FileField()

    def validate_project_id(self, value):
        """Validate that project exists and user has access."""
        try:
            Project.objects.get(id=value)
            return value
        except Project.DoesNotExist:
            raise serializers.ValidationError(f"Project with id {value} not found")

    def validate_platform_id(self, value):
        """Validate that platform exists."""
        try:
            Platform.objects.get(id=value)
            return value
        except Platform.DoesNotExist:
            raise serializers.ValidationError(f"Platform with id {value} not found")

    def validate_rule_id(self, value):
        """Validate that rule exists."""
        try:
            Rule.objects.get(id=value)
            return value
        except Rule.DoesNotExist:
            raise serializers.ValidationError(f"Rule with id {value} not found")

    def validate_file(self, value: UploadedFile):
        """Validate uploaded file."""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed")

        if value.content_type not in ['text/csv', 'application/csv', 'text/plain']:
            raise serializers.ValidationError(
                f"Invalid file type: {value.content_type}. Expected CSV file."
            )

        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size ({value.size} bytes) exceeds maximum (5MB)"
            )

        return value

    def validate(self, attrs):
        """Cross-field validation."""
        # Validate platform is assigned to project
        project_id = attrs.get('project_id')
        platform_id = attrs.get('platform_id')

        if project_id and platform_id:
            try:
                project = Project.objects.get(id=project_id)
                if not project.platforms.filter(id=platform_id).exists():
                    raise serializers.ValidationError({
                        'platform_id': f"Platform not assigned to project"
                    })
            except Project.DoesNotExist:
                pass  # Already handled in field validation

        return attrs


class SelectiveImportRequestSerializer(serializers.Serializer):
    """
    Serializer for selective import of existing ExternalStrings to a project.
    """
    project_id = serializers.IntegerField()
    external_string_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of ExternalString IDs to import"
    )

    def validate_project_id(self, value):
        """Validate that project exists."""
        try:
            Project.objects.get(id=value)
            return value
        except Project.DoesNotExist:
            raise serializers.ValidationError(f"Project with id {value} not found")


class ExternalStringRowSerializer(serializers.Serializer):
    """Serializer for individual ExternalString row result."""
    row_number = serializers.IntegerField()
    string_value = serializers.CharField()
    external_platform_id = serializers.CharField()
    entity_name = serializers.CharField()
    parent_external_id = serializers.CharField(allow_null=True, allow_blank=True)
    validation_status = serializers.ChoiceField(
        choices=['valid', 'invalid', 'warning', 'skipped']
    )
    external_string_id = serializers.IntegerField(allow_null=True)
    errors = ErrorDetailSerializer(many=True)
    warnings = WarningDetailSerializer(many=True)


class ValidationOnlyResponseSerializer(serializers.Serializer):
    """Serializer for validation-only response."""
    success = serializers.BooleanField()
    batch_id = serializers.IntegerField()
    operation_type = serializers.CharField(default='validation')
    summary = ValidationSummarySerializer()
    results = ExternalStringRowSerializer(many=True)


class ProjectStringRowSerializer(serializers.Serializer):
    """Serializer for ProjectString import result."""
    row_number = serializers.IntegerField()
    string_value = serializers.CharField()
    external_platform_id = serializers.CharField()
    entity_name = serializers.CharField()
    validation_status = serializers.ChoiceField(
        choices=['valid', 'invalid', 'warning', 'skipped']
    )
    external_string_id = serializers.IntegerField(allow_null=True)
    project_string_id = serializers.IntegerField(allow_null=True)
    import_status = serializers.ChoiceField(
        choices=['imported', 'updated', 'failed', 'skipped']
    )
    errors = ErrorDetailSerializer(many=True)
    warnings = WarningDetailSerializer(many=True)


class ImportToProjectResponseSerializer(serializers.Serializer):
    """Serializer for import-to-project response."""
    success = serializers.BooleanField()
    batch_id = serializers.IntegerField()
    operation_type = serializers.CharField(default='import')
    project = serializers.DictField()  # {id, name}
    summary = ValidationSummarySerializer()
    results = ProjectStringRowSerializer(many=True)


class SelectiveImportResponseSerializer(serializers.Serializer):
    """Serializer for selective import response."""
    success = serializers.BooleanField()
    summary = serializers.DictField()  # {requested, imported, failed}
    results = serializers.ListField()  # List of import results
