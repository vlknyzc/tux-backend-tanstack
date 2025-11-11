"""
ExternalString model for tracking external platform strings.

Stores ALL external platform strings (valid, invalid, warnings) imported
from advertising platforms (Meta, Google Ads, TikTok, etc.) for validation
and potential import into projects.
"""

from django.db import models
from django.core.exceptions import ValidationError

from .base import TimeStampModel, WorkspaceMixin
from ..constants import STRING_VALUE_LENGTH


class ExternalString(TimeStampModel, WorkspaceMixin):
    """
    External platform strings imported for validation.

    Stores ALL strings (valid, invalid, warnings) so users can:
    - See which external strings failed validation
    - Reference external_platform_id when fixing issues
    - Re-upload and track validation history
    - Selectively import valid strings into projects
    """

    # Context
    platform = models.ForeignKey(
        'master_data.Platform',
        on_delete=models.CASCADE,
        related_name='external_strings',
        help_text="Platform this string came from"
    )
    rule = models.ForeignKey(
        'master_data.Rule',
        on_delete=models.CASCADE,
        related_name='external_strings',
        help_text="Rule used for validation"
    )
    entity = models.ForeignKey(
        'master_data.Entity',
        on_delete=models.CASCADE,
        related_name='external_strings',
        help_text="Entity type of this string"
    )
    batch = models.ForeignKey(
        'master_data.ExternalStringBatch',
        on_delete=models.CASCADE,
        related_name='external_strings',
        help_text="Batch this string belongs to"
    )

    # String data
    value = models.CharField(
        max_length=STRING_VALUE_LENGTH,
        help_text="The external string value"
    )
    external_platform_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Platform-specific identifier (e.g., campaign_123)"
    )
    external_parent_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Parent's platform identifier"
    )

    # Validation results (valid, invalid, or warning)
    validation_status = models.CharField(
        max_length=20,
        choices=[
            ('valid', 'Valid'),
            ('invalid', 'Invalid'),
            ('warning', 'Warning'),
            ('skipped', 'Skipped - Entity Mismatch'),
        ],
        help_text="Validation result"
    )
    validation_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Parsed values, errors, warnings, hierarchy conflicts"
    )

    # Import tracking
    imported_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this was imported to a project"
    )
    imported_to_project_string = models.ForeignKey(
        'master_data.String',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='source_external_strings',
        help_text="If imported to project, link to String"
    )

    # User tracking
    created_by = models.ForeignKey(
        'users.UserAccount',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_external_strings',
        help_text="User who uploaded this"
    )

    # Version tracking (for re-uploads)
    version = models.IntegerField(
        default=1,
        help_text="Version number (increments on re-upload)"
    )
    superseded_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='supersedes',
        help_text="If re-uploaded, link to newer version"
    )

    class Meta:
        db_table = 'master_data_external_string'
        verbose_name = 'External String'
        verbose_name_plural = 'External Strings'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['workspace', 'external_platform_id']),
            models.Index(fields=['workspace', 'validation_status']),
            models.Index(fields=['workspace', 'platform', 'entity']),
            models.Index(fields=['batch']),
            models.Index(fields=['imported_to_project_string']),
        ]
        # Allow multiple versions of same external_platform_id
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'external_platform_id', 'batch'],
                name='unique_external_id_per_batch',
                condition=models.Q(superseded_by__isnull=True)
            ),
        ]

    def __str__(self):
        status_icon = {
            'valid': '✓',
            'invalid': '✗',
            'warning': '⚠',
            'skipped': '⊘'
        }.get(self.validation_status, '?')
        return f"{status_icon} {self.external_platform_id}: {self.value}"

    def is_importable(self):
        """Check if this string can be imported to a project."""
        return self.validation_status in ('valid', 'warning') and not self.imported_at

    def get_latest_version(self):
        """Get the latest version if this was superseded."""
        current = self
        max_iterations = 100  # Prevent infinite loops
        iterations = 0

        while current.superseded_by and iterations < max_iterations:
            current = current.superseded_by
            iterations += 1

        return current

    def clean(self):
        """Validate the external string configuration."""
        super().clean()

        # Validate value is not empty
        if not self.value or not self.value.strip():
            raise ValidationError("String value cannot be empty")

        # Validate external_platform_id is not empty
        if not self.external_platform_id or not self.external_platform_id.strip():
            raise ValidationError("External platform ID cannot be empty")

        # Validate workspace consistency
        if self.platform and hasattr(self.platform, 'workspace'):
            if self.platform.workspace != self.workspace:
                raise ValidationError("Platform must belong to the same workspace")
        if self.rule and self.rule.workspace != self.workspace:
            raise ValidationError("Rule must belong to the same workspace")
        if self.entity and self.entity.platform != self.platform:
            raise ValidationError("Entity must belong to the same platform")
        if self.batch and self.batch.workspace != self.workspace:
            raise ValidationError("Batch must belong to the same workspace")
