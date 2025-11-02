"""
Bulk operations serializers for efficient batch processing.
These serializers handle multiple entity operations in single API calls.
"""

from rest_framework import serializers
from django.db import transaction
from .. import models


class BulkStringCreateSerializer(serializers.Serializer):
    """Serializer for bulk string creation."""

    strings = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of string creation data with details"
    )

    def validate_strings(self, value):
        """Validate that strings list is not empty."""
        if not value:
            raise serializers.ValidationError(
                "At least one string must be provided")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create multiple strings atomically."""
        strings_data = validated_data['strings']
        created_strings = []

        # Import here to avoid circular import
        from .string import StringWithDetailsSerializer

        for string_data in strings_data:
            string_serializer = StringWithDetailsSerializer(
                data=string_data,
                context=self.context
            )
            string_serializer.is_valid(raise_exception=True)
            string = string_serializer.save()
            created_strings.append(string)

        return {'strings': created_strings}


class BulkStringDetailUpdateSerializer(serializers.Serializer):
    """Serializer for bulk string detail updates."""

    details = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of string detail updates with id and field updates"
    )

    def validate_details(self, value):
        """Validate details list."""
        if not value:
            raise serializers.ValidationError(
                "At least one detail must be provided")

        for detail in value:
            if 'id' not in detail:
                raise serializers.ValidationError(
                    "Each detail must have an 'id' field")

        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update multiple string details atomically."""
        details_data = validated_data['details']
        updated_details = []

        for detail_data in details_data:
            detail_id = detail_data.pop('id')
            try:
                detail = models.StringDetail.objects.get(id=detail_id)

                # Validate workspace access
                request = self.context.get('request')
                if request and hasattr(request, 'user'):
                    workspace_id = getattr(request, 'workspace_id', None)
                    if workspace_id and detail.workspace.id != workspace_id:
                        raise serializers.ValidationError(
                            f"Detail {detail_id} does not belong to workspace {workspace_id}"
                        )

                # Update detail fields
                for field, value in detail_data.items():
                    setattr(detail, field, value)
                detail.save()

                # Trigger string regeneration
                detail.string.regenerate_value()

                updated_details.append(detail)

            except models.StringDetail.DoesNotExist:
                raise serializers.ValidationError(
                    f"StringDetail {detail_id} does not exist")

        return {'details': updated_details}


# DEPRECATED: BulkSubmissionCreateSerializer removed - use BulkProjectCreateSerializer instead


class BulkStringDeleteSerializer(serializers.Serializer):
    """Serializer for bulk string deletion."""

    string_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of string IDs to delete"
    )

    def validate_string_ids(self, value):
        """Validate that string_ids list is not empty."""
        if not value:
            raise serializers.ValidationError(
                "At least one string ID must be provided")
        return value

    @transaction.atomic
    def delete(self, validated_data):
        """Delete multiple strings atomically."""
        string_ids = validated_data['string_ids']
        deleted_count = 0

        for string_id in string_ids:
            try:
                string = models.String.objects.get(id=string_id)
                
                # Validate workspace access
                request = self.context.get('request')
                if request and hasattr(request, 'user'):
                    workspace_id = getattr(request, 'workspace_id', None)
                    if workspace_id and string.workspace.id != workspace_id:
                        raise serializers.ValidationError(
                            f"String {string_id} does not belong to workspace {workspace_id}"
                        )

                string.delete()
                deleted_count += 1

            except models.String.DoesNotExist:
                raise serializers.ValidationError(
                    f"String {string_id} does not exist")

        return {'deleted_count': deleted_count, 'string_ids': string_ids}


class BulkValidationResultSerializer(serializers.Serializer):
    """Serializer for bulk operation validation results."""

    valid_items = serializers.ListField(
        child=serializers.DictField(),
        help_text="Items that passed validation"
    )
    invalid_items = serializers.ListField(
        child=serializers.DictField(),
        help_text="Items that failed validation with error details"
    )
    summary = serializers.DictField(
        help_text="Summary statistics of the validation"
    )


class BulkOperationStatusSerializer(serializers.Serializer):
    """Serializer for bulk operation status responses."""

    operation_id = serializers.CharField(
        help_text="Unique identifier for the bulk operation"
    )
    status = serializers.ChoiceField(
        choices=['pending', 'processing', 'completed', 'failed'],
        help_text="Current status of the bulk operation"
    )
    total_items = serializers.IntegerField(
        help_text="Total number of items to process"
    )
    processed_items = serializers.IntegerField(
        help_text="Number of items successfully processed"
    )
    failed_items = serializers.IntegerField(
        help_text="Number of items that failed processing"
    )
    error_details = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Details of any errors that occurred"
    )
    started_at = serializers.DateTimeField(
        help_text="When the operation started"
    )
    completed_at = serializers.DateTimeField(
        required=False,
        help_text="When the operation completed"
    )