"""
Database models for tracking string propagation operations.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .base import TimeStampModel, WorkspaceMixin

User = get_user_model()


class PropagationJobManager(models.Manager):
    """Custom manager for PropagationJob model."""

    def get_queryset(self):
        from .base import get_current_workspace, _thread_locals
        queryset = super().get_queryset()
        # Auto-filter by workspace if context is set and user is not superuser
        current_workspace = get_current_workspace()
        if current_workspace and not getattr(_thread_locals, 'is_superuser', False):
            queryset = queryset.filter(workspace_id=current_workspace)
        return queryset

    def all_workspaces(self):
        """Get queryset without workspace filtering (for superusers)"""
        return super().get_queryset()

    def for_workspace(self, workspace_id):
        """Filter queryset by specific workspace"""
        return super().get_queryset().filter(workspace_id=workspace_id)


class PropagationJob(TimeStampModel, WorkspaceMixin):
    """
    Tracks string propagation operations for audit and monitoring.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('partial_failure', 'Partial Failure'),
    ]
    
    # Core fields
    batch_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique identifier for this propagation batch"
    )
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="triggered_propagation_jobs",
        help_text="User who triggered this propagation"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the propagation job"
    )
    
    # Timing fields
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the job actually started processing"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the job completed or failed"
    )
    
    # Progress tracking
    total_strings = models.PositiveIntegerField(
        default=0,
        help_text="Total number of strings to be processed"
    )
    processed_strings = models.PositiveIntegerField(
        default=0,
        help_text="Number of strings successfully processed"
    )
    failed_strings = models.PositiveIntegerField(
        default=0,
        help_text="Number of strings that failed processing"
    )
    
    # Configuration and metadata
    max_depth = models.PositiveIntegerField(
        default=10,
        help_text="Maximum propagation depth configured for this job"
    )
    processing_method = models.CharField(
        max_length=20,
        choices=[
            ('synchronous', 'Synchronous'),
            ('background', 'Background'),
            ('chunked', 'Chunked Processing')
        ],
        default='synchronous',
        help_text="Processing method used for this job"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about the job configuration and execution"
    )
    
    # Error tracking
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if job failed"
    )
    
    # Custom manager
    objects = PropagationJobManager()
    
    class Meta:
        verbose_name = "Propagation Job"
        verbose_name_plural = "Propagation Jobs"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['workspace', 'triggered_by']),
            models.Index(fields=['batch_id']),
            models.Index(fields=['created']),
        ]
    
    def __str__(self):
        return f"PropagationJob {self.batch_id} - {self.status}"
    
    @property
    def duration(self):
        """Calculate job duration if completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def progress_percentage(self):
        """Calculate completion percentage."""
        if self.total_strings == 0:
            return 0
        return (self.processed_strings / self.total_strings) * 100
    
    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.total_strings == 0:
            return 0
        return (self.processed_strings / self.total_strings) * 100
    
    def clean(self):
        """Validate the propagation job."""
        super().clean()
        
        # Validate timing consistency
        if self.started_at and self.completed_at:
            if self.completed_at < self.started_at:
                raise ValidationError("Completion time cannot be before start time")
        
        # Validate progress consistency
        if self.processed_strings + self.failed_strings > self.total_strings:
            raise ValidationError("Processed + failed strings cannot exceed total")
    
    def mark_started(self):
        """Mark the job as started."""
        from django.utils import timezone
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, success=True):
        """Mark the job as completed."""
        from django.utils import timezone
        self.status = 'completed' if success else 'failed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def add_error(self, error_message: str):
        """Add error message to the job."""
        self.error_message = error_message
        self.status = 'failed'
        self.save(update_fields=['error_message', 'status'])


class PropagationErrorManager(models.Manager):
    """Custom manager for PropagationError model."""

    def get_queryset(self):
        from .base import get_current_workspace, _thread_locals
        queryset = super().get_queryset()
        # Auto-filter by workspace if context is set and user is not superuser
        current_workspace = get_current_workspace()
        if current_workspace and not getattr(_thread_locals, 'is_superuser', False):
            queryset = queryset.filter(workspace_id=current_workspace)
        return queryset

    def all_workspaces(self):
        """Get queryset without workspace filtering (for superusers)"""
        return super().get_queryset()

    def for_workspace(self, workspace_id):
        """Filter queryset by specific workspace"""
        return super().get_queryset().filter(workspace_id=workspace_id)


class PropagationError(TimeStampModel, WorkspaceMixin):
    """
    Tracks individual errors that occur during string propagation.
    """
    
    ERROR_TYPES = [
        ('string_generation_error', 'String Generation Error'),
        ('database_error', 'Database Error'),
        ('validation_error', 'Validation Error'),
        ('circular_dependency', 'Circular Dependency'),
        ('conflict_error', 'Conflict Error'),
        ('permission_error', 'Permission Error'),
        ('timeout_error', 'Timeout Error'),
        ('unknown_error', 'Unknown Error'),
    ]
    
    # Relationships
    job = models.ForeignKey(
        PropagationJob,
        on_delete=models.CASCADE,
        related_name="errors",
        help_text="Propagation job this error belongs to"
    )
    string = models.ForeignKey(
        "master_data.String",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="propagation_errors",
        help_text="String that caused the error (if applicable)"
    )
    string_detail = models.ForeignKey(
        "master_data.StringDetail",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="propagation_errors",
        help_text="StringDetail that caused the error (if applicable)"
    )
    
    # Error details
    error_type = models.CharField(
        max_length=30,
        choices=ERROR_TYPES,
        help_text="Type of error that occurred"
    )
    error_message = models.TextField(
        help_text="Human-readable error message"
    )
    error_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Machine-readable error code"
    )
    stack_trace = models.TextField(
        null=True,
        blank=True,
        help_text="Full stack trace of the error"
    )
    
    # Context
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context data about the error"
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this operation has been retried"
    )
    is_retryable = models.BooleanField(
        default=False,
        help_text="Whether this error can be retried"
    )
    resolved = models.BooleanField(
        default=False,
        help_text="Whether this error has been resolved"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this error was resolved"
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_propagation_errors",
        help_text="User who resolved this error"
    )
    
    # Custom manager
    objects = PropagationErrorManager()
    
    class Meta:
        verbose_name = "Propagation Error"
        verbose_name_plural = "Propagation Errors"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['workspace', 'error_type']),
            models.Index(fields=['workspace', 'resolved']),
            models.Index(fields=['job', 'error_type']),
            models.Index(fields=['created']),
        ]
    
    def __str__(self):
        return f"PropagationError {self.error_type} - Job {self.job.batch_id}"
    
    def mark_resolved(self, user=None):
        """Mark this error as resolved."""
        from django.utils import timezone
        self.resolved = True
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        self.save(update_fields=['resolved', 'resolved_at', 'resolved_by'])
    
    def increment_retry_count(self):
        """Increment the retry count."""
        self.retry_count += 1
        self.save(update_fields=['retry_count'])


class PropagationSettingsManager(models.Manager):
    """Custom manager for PropagationSettings model."""

    def get_queryset(self):
        from .base import get_current_workspace, _thread_locals
        queryset = super().get_queryset()
        # Auto-filter by workspace if context is set and user is not superuser
        current_workspace = get_current_workspace()
        if current_workspace and not getattr(_thread_locals, 'is_superuser', False):
            queryset = queryset.filter(workspace_id=current_workspace)
        return queryset

    def all_workspaces(self):
        """Get queryset without workspace filtering (for superusers)"""
        return super().get_queryset()

    def for_workspace(self, workspace_id):
        """Filter queryset by specific workspace"""
        return super().get_queryset().filter(workspace_id=workspace_id)

    def get_for_user_and_workspace(self, user, workspace):
        """Get settings for specific user and workspace combination."""
        try:
            return self.get(user=user, workspace=workspace)
        except PropagationSettings.DoesNotExist:
            # Return default settings
            return PropagationSettings(
                user=user,
                workspace=workspace,
                settings={}
            )


class PropagationSettings(TimeStampModel, WorkspaceMixin):
    """
    User and workspace-specific propagation settings.
    """
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="propagation_settings",
        help_text="User these settings belong to"
    )
    
    # Settings
    settings = models.JSONField(
        default=dict,
        help_text="User-specific propagation settings"
    )
    
    # Custom manager
    objects = PropagationSettingsManager()
    
    class Meta:
        verbose_name = "Propagation Settings"
        verbose_name_plural = "Propagation Settings"
        unique_together = [('user', 'workspace')]
        indexes = [
            models.Index(fields=['workspace', 'user']),
        ]
    
    def __str__(self):
        return f"PropagationSettings for {self.user.email} in {self.workspace.name}"
    
    def get_setting(self, key: str, default=None):
        """Get a specific setting value."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Set a specific setting value."""
        self.settings[key] = value
        self.save(update_fields=['settings'])
    
    def get_default_propagation_depth(self):
        """Get default propagation depth for this user/workspace."""
        return self.get_setting('default_propagation_depth', 10)
    
    def get_default_propagation_enabled(self):
        """Get default propagation enabled setting."""
        return self.get_setting('default_propagation_enabled', True)
    
    def get_field_propagation_rules(self):
        """Get field-specific propagation rules."""
        return self.get_setting('field_propagation_rules', {})