"""
Serializers for String Registry validation feature.

Handles validation and import of external platform strings.
"""

from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile
from typing import Dict, List

from ..models import Platform, Rule, Workspace


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


class RowResultSerializer(serializers.Serializer):
    """Serializer for individual row validation result."""
    row_number = serializers.IntegerField()
    string_value = serializers.CharField()
    external_platform_id = serializers.CharField(allow_null=True)
    entity_name = serializers.CharField()
    parent_external_id = serializers.CharField(allow_null=True, allow_blank=True)
    status = serializers.ChoiceField(
        choices=['valid', 'warning', 'failed', 'skipped', 'updated']
    )
    string_id = serializers.IntegerField(allow_null=True)
    tuxonomy_parent_id = serializers.IntegerField(allow_null=True)
    errors = ErrorDetailSerializer(many=True)
    warnings = WarningDetailSerializer(many=True)


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


class BulkValidationResponseSerializer(serializers.Serializer):
    """Serializer for bulk validation response."""
    success = serializers.BooleanField()
    summary = ValidationSummarySerializer()
    results = RowResultSerializer(many=True)


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


class CSVUploadRequestSerializer(serializers.Serializer):
    """Serializer for CSV upload request."""
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
        # Check file extension
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed")

        # Check MIME type
        if value.content_type not in ['text/csv', 'application/csv', 'text/plain']:
            raise serializers.ValidationError(
                f"Invalid file type: {value.content_type}. Expected CSV file."
            )

        # Check file size (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size ({value.size} bytes) exceeds maximum (5MB)"
            )

        return value

    def validate(self, attrs):
        """Cross-field validation."""
        # Additional validation can be added here
        return attrs
