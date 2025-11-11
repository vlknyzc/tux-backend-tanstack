"""
ExternalStringBatch model for tracking CSV upload events.

Tracks external platform string validation and import operations,
including upload metadata, statistics, and results.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .base import TimeStampModel, WorkspaceMixin

User = get_user_model()


class ExternalStringBatch(TimeStampModel, WorkspaceMixin):
    """
    Tracks CSV upload batches for external platform string operations.

    Each batch represents one CSV file upload containing external platform
    strings that were either:
    - Validated and stored in ExternalString (validation operation)
    - Validated and imported to String (import operation)

    Provides audit trail and summary statistics for each upload.
    """

    # Upload metadata
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='external_string_batches',
        help_text="User who uploaded the file"
    )
    file_name = models.CharField(
        max_length=255,
        help_text="Original CSV file name"
    )
    file_size_bytes = models.IntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )

    # Operation context
    operation_type = models.CharField(
        max_length=20,
        choices=[
            ('validation', 'Validation Only'),
            ('import', 'Import to Project'),
        ],
        default='validation',
        help_text="Type of operation performed"
    )
    platform = models.ForeignKey(
        'master_data.Platform',
        on_delete=models.CASCADE,
        related_name='external_string_batches',
        help_text="Platform the strings came from"
    )
    rule = models.ForeignKey(
        'master_data.Rule',
        on_delete=models.CASCADE,
        related_name='external_string_batches',
        help_text="Rule used for validation"
    )
    project = models.ForeignKey(
        'master_data.Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='external_string_batches',
        help_text="Project (only for 'import' operation type)"
    )

    # Summary statistics
    total_rows = models.IntegerField(
        default=0,
        help_text="Total rows in CSV"
    )
    uploaded_rows = models.IntegerField(
        default=0,
        help_text="Rows uploaded (excluding header)"
    )
    processed_rows = models.IntegerField(
        default=0,
        help_text="Rows successfully processed"
    )
    skipped_rows = models.IntegerField(
        default=0,
        help_text="Rows skipped (entity mismatch, duplicates)"
    )

    # Validation results
    created_count = models.IntegerField(
        default=0,
        help_text="ExternalStrings or Strings created"
    )
    updated_count = models.IntegerField(
        default=0,
        help_text="Strings updated (import operation only)"
    )
    valid_count = models.IntegerField(
        default=0,
        help_text="Strings that passed validation"
    )
    warnings_count = models.IntegerField(
        default=0,
        help_text="Strings with warnings (but still valid)"
    )
    failed_count = models.IntegerField(
        default=0,
        help_text="Strings that failed validation"
    )

    # Hierarchy statistics
    linked_parents_count = models.IntegerField(
        default=0,
        help_text="Successfully linked to parent"
    )
    parent_conflicts_count = models.IntegerField(
        default=0,
        help_text="Hierarchy conflicts detected"
    )
    parent_not_found_count = models.IntegerField(
        default=0,
        help_text="Parent external_id not found"
    )

    # Processing info
    processing_time_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Time taken to process the upload"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='completed',
        help_text="Processing status"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if processing failed"
    )

    class Meta:
        db_table = 'master_data_external_string_batch'
        verbose_name = 'External String Batch'
        verbose_name_plural = 'External String Batches'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['workspace', 'uploaded_by']),
            models.Index(fields=['workspace', 'platform']),
            models.Index(fields=['workspace', 'project']),
            models.Index(fields=['workspace', 'created']),
            models.Index(fields=['operation_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        op_type = self.get_operation_type_display()
        project_info = f" → {self.project.name}" if self.project else ""
        return f"{self.file_name} ({op_type}{project_info}) - {self.created.strftime('%Y-%m-%d %H:%M')}"

    def clean(self):
        """Validate batch configuration."""
        super().clean()

        # Validate project is required for import operations
        if self.operation_type == 'import' and not self.project:
            raise ValidationError("Project is required for import operations")

        # Validate platform is assigned to project (for import)
        if self.project and self.platform:
            if not self.project.platforms.filter(id=self.platform_id).exists():
                raise ValidationError(
                    f"Platform '{self.platform.name}' is not assigned to project '{self.project.name}'"
                )

    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.uploaded_rows == 0:
            return 0
        return round((self.valid_count / self.uploaded_rows) * 100, 1)

    @property
    def failure_rate(self):
        """Calculate failure rate percentage."""
        if self.uploaded_rows == 0:
            return 0
        return round((self.failed_count / self.uploaded_rows) * 100, 1)
