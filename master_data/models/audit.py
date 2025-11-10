"""
Audit and tracking models for Phase 4 backend integration.
Handles string modification history, inheritance tracking, and batch operations.
"""

import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from .base import TimeStampModel, WorkspaceMixin

User = get_user_model()


class StringModification(TimeStampModel, WorkspaceMixin):
    """
    Tracks all modifications to strings for audit trail and rollback capability.
    """
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    string = models.ForeignKey(
        'master_data.String',
        on_delete=models.CASCADE,
        related_name='modifications',
        help_text="String that was modified"
    )
    version = models.IntegerField(
        help_text="Version number for this modification"
    )
    
    # Modification details
    field_updates = models.JSONField(
        help_text="JSON object containing field updates made"
    )
    string_value = models.TextField(
        help_text="String value after this modification"
    )
    original_values = models.JSONField(
        help_text="Original values before modification"
    )
    
    # Tracking information
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who made this modification"
    )
    modified_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this modification was made"
    )
    change_type = models.CharField(
        max_length=50,
        choices=[
            ('direct_edit', 'Direct Edit'),
            ('inheritance_update', 'Inheritance Update'),
            ('batch_update', 'Batch Update'),
            ('regeneration', 'Regeneration'),
        ],
        help_text="Type of change that was made"
    )
    
    # Batch and hierarchy tracking
    batch_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of batch operation if part of batch"
    )
    parent_version = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_versions',
        help_text="Parent version that triggered this change"
    )
    
    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about the modification"
    )

    class Meta:
        verbose_name = "String Modification"
        verbose_name_plural = "String Modifications"
        ordering = ['-modified_at']
        constraints = [
            models.UniqueConstraint(
                fields=['string', 'version'],
                name='unique_string_version'
            )
        ]
        indexes = [
            models.Index(fields=['string', 'version']),
            models.Index(fields=['batch_id']),
            models.Index(fields=['modified_at']),
            models.Index(fields=['workspace', 'string']),
        ]

    def __str__(self):
        return f"String {self.string.value} v{self.version} - {self.change_type}"

    def save(self, *args, **kwargs):
        # Auto-increment version for new modifications
        if not self.version:
            last_version = StringModification.objects.filter(
                string=self.string
            ).aggregate(
                max_version=models.Max('version')
            )['max_version']
            self.version = (last_version or 0) + 1
        
        super().save(*args, **kwargs)


class StringInheritanceUpdate(TimeStampModel, WorkspaceMixin):
    """
    Tracks inheritance updates when parent strings are modified.
    """
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_modification = models.ForeignKey(
        StringModification,
        on_delete=models.CASCADE,
        related_name='inheritance_updates',
        help_text="Parent modification that triggered this inheritance update"
    )
    child_string = models.ForeignKey(
        'master_data.String',
        on_delete=models.CASCADE,
        related_name='inheritance_received',
        help_text="Child string that received inherited changes"
    )
    
    # Update details
    inherited_fields = models.JSONField(
        help_text="Fields that were inherited from parent"
    )
    applied_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the inheritance update was applied"
    )

    class Meta:
        verbose_name = "String Inheritance Update"
        verbose_name_plural = "String Inheritance Updates"
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(
                fields=['parent_modification', 'child_string'],
                name='unique_inheritance_update'
            )
        ]
        indexes = [
            models.Index(fields=['parent_modification']),
            models.Index(fields=['child_string']),
            models.Index(fields=['workspace', 'applied_at']),
        ]

    def __str__(self):
        return f"Inheritance: {self.parent_modification.string.value} → {self.child_string.value}"


class StringUpdateBatch(TimeStampModel, WorkspaceMixin):
    """
    Tracks batch update operations for monitoring and management.
    """
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Batch metadata
    rule = models.ForeignKey(
        'master_data.Rule',
        on_delete=models.CASCADE,
        help_text="Rule being updated in this batch"
    )
    entity = models.ForeignKey(
        'master_data.Entity',
        on_delete=models.CASCADE,
        help_text="Field being updated in this batch"
    )
    
    # Execution tracking
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who initiated this batch operation"
    )
    initiated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the batch operation was started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the batch operation completed"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending',
        help_text="Current status of the batch operation"
    )
    
    # Progress tracking
    total_strings = models.IntegerField(
        help_text="Total number of strings to update"
    )
    processed_strings = models.IntegerField(
        default=0,
        help_text="Number of strings successfully processed"
    )
    failed_strings = models.IntegerField(
        default=0,
        help_text="Number of strings that failed to process"
    )
    
    # Backup and recovery
    backup_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of backup created before this operation"
    )
    
    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about the batch operation"
    )

    class Meta:
        verbose_name = "String Update Batch"
        verbose_name_plural = "String Update Batches"
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['initiated_by', 'initiated_at']),
            models.Index(fields=['rule', 'entity']),
        ]

    def __str__(self):
        return f"Batch {self.id.hex[:8]} - {self.status} ({self.processed_strings}/{self.total_strings})"

    @property
    def progress_percentage(self):
        """Calculate completion percentage."""
        if self.total_strings == 0:
            return 0
        return round((self.processed_strings / self.total_strings) * 100, 1)

    @property
    def is_complete(self):
        """Check if batch is complete."""
        return self.status in ['completed', 'failed', 'cancelled']

    def mark_completed(self):
        """Mark batch as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def mark_failed(self):
        """Mark batch as failed."""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def increment_processed(self):
        """Increment processed count."""
        self.processed_strings += 1
        self.save(update_fields=['processed_strings'])

    def increment_failed(self):
        """Increment failed count."""
        self.failed_strings += 1
        self.save(update_fields=['failed_strings'])