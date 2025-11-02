"""
ProjectString models for the master_data app.
Handles string generation within projects (replacing submission-based strings).
"""

import uuid
from django.db import models
from django.core.exceptions import ValidationError

from .base import TimeStampModel, WorkspaceMixin
from ..constants import STRING_VALUE_LENGTH, FREETEXT_LENGTH


class ProjectStringQuerySet(models.QuerySet):
    """Custom QuerySet for ProjectString model."""

    def for_project(self, project):
        """Filter strings for a specific project."""
        return self.filter(project=project)

    def for_platform(self, platform):
        """Filter strings for a specific platform."""
        return self.filter(platform=platform)

    def for_field_level(self, level):
        """Filter strings for a specific field level."""
        return self.filter(field__field_level=level)


class ProjectStringManager(models.Manager):
    """Custom manager for ProjectString model."""

    def get_queryset(self):
        from .base import get_current_workspace, _thread_locals
        queryset = ProjectStringQuerySet(self.model, using=self._db)
        # Auto-filter by workspace if context is set and user is not superuser
        current_workspace = get_current_workspace()
        if current_workspace and not getattr(_thread_locals, 'is_superuser', False):
            queryset = queryset.filter(workspace_id=current_workspace)
        return queryset

    def all_workspaces(self):
        """Get queryset without workspace filtering (for superusers)"""
        return ProjectStringQuerySet(self.model, using=self._db)

    def for_workspace(self, workspace_id):
        """Filter queryset by specific workspace"""
        return ProjectStringQuerySet(self.model, using=self._db).filter(workspace_id=workspace_id)

    def for_project(self, project):
        return self.get_queryset().for_project(project)

    def for_platform(self, platform):
        return self.get_queryset().for_platform(platform)

    def for_field_level(self, level):
        return self.get_queryset().for_field_level(level)


class ProjectString(TimeStampModel, WorkspaceMixin):
    """
    Represents a generated naming string within a project.

    ProjectStrings are similar to Strings but belong to projects instead of submissions.
    They are organized by platform within a project and support hierarchical relationships.
    """

    # Relationships
    project = models.ForeignKey(
        "master_data.Project",
        on_delete=models.CASCADE,
        related_name="strings",
        help_text="Project this string belongs to"
    )
    platform = models.ForeignKey(
        "master_data.Platform",
        on_delete=models.CASCADE,
        related_name="project_strings",
        help_text="Platform this string belongs to (via project platform assignment)"
    )
    field = models.ForeignKey(
        "master_data.Field",
        on_delete=models.CASCADE,
        related_name="project_field_strings",
        help_text="Field this string belongs to"
    )
    rule = models.ForeignKey(
        "master_data.Rule",
        on_delete=models.CASCADE,
        related_name="project_rule_strings",
        help_text="Rule used to generate this string"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent string in hierarchical naming structure"
    )
    created_by = models.ForeignKey(
        "users.UserAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_project_strings",
        help_text="User who created this string"
    )

    # Fields
    value = models.CharField(
        max_length=STRING_VALUE_LENGTH,
        help_text="Generated string value following naming convention"
    )
    string_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,  # Globally unique across all projects and workspaces
        help_text="Unique identifier for this string (globally unique)"
    )
    parent_uuid = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID of parent string for hierarchical linking"
    )

    # Custom manager
    objects = ProjectStringManager()

    class Meta:
        verbose_name = "Project String"
        verbose_name_plural = "Project Strings"
        ordering = ['workspace', 'project', 'field__field_level', 'value']
        indexes = [
            models.Index(fields=['workspace', 'project', 'platform']),
            models.Index(fields=['workspace', 'string_uuid']),
            models.Index(fields=['workspace', 'parent_uuid']),
            models.Index(fields=['project', 'platform', 'field']),
        ]
        constraints = [
            # Unique constraint for strings WITH a parent
            models.UniqueConstraint(
                fields=['workspace', 'project', 'platform', 'field', 'parent', 'value'],
                name='unique_with_parent',
                condition=models.Q(parent__isnull=False)
            ),
            # Unique constraint for strings WITHOUT a parent (handles NULL properly)
            models.UniqueConstraint(
                fields=['workspace', 'project', 'platform', 'field', 'value'],
                name='unique_without_parent',
                condition=models.Q(parent__isnull=True)
            ),
        ]

    def __str__(self):
        return f"{self.project.name} - Level {self.field.field_level} - {self.field.name}: {self.value}"

    def clean(self):
        """Validate the project string configuration."""
        super().clean()

        # Validate value is not empty
        if not self.value or not self.value.strip():
            raise ValidationError("String value cannot be empty")

        # Validate rule belongs to same platform as field
        if self.rule and self.field:
            if self.rule.platform != self.field.platform:
                raise ValidationError(
                    "Rule and field must belong to the same platform")

        # Validate platform is assigned to project
        if self.project_id and self.platform_id:
            if not self.project.platforms.filter(id=self.platform_id).exists():
                raise ValidationError(
                    "Platform must be assigned to this project")

        # Validate parent is in same platform (if parent exists)
        if self.parent_uuid:
            try:
                parent = ProjectString.objects.get(
                    string_uuid=self.parent_uuid,
                    platform=self.platform
                )
                # Validate parent is not self
                if parent.string_uuid == self.string_uuid:
                    raise ValidationError("String cannot be its own parent")
            except ProjectString.DoesNotExist:
                raise ValidationError(
                    "Parent string must exist in the same platform")

        # Validate workspace consistency
        if self.project and self.project.workspace != self.workspace:
            raise ValidationError("Project must belong to the same workspace")
        if self.platform and hasattr(self.platform, 'workspace') and self.platform.workspace != self.workspace:
            raise ValidationError("Platform must belong to the same workspace")

    def save(self, *args, **kwargs):
        """Enhanced save with auto-generation and validation."""
        # Auto-set workspace from project
        if not self.workspace_id and self.project_id:
            self.workspace = self.project.workspace

        # Auto-generate UUID if not set (only for new instances without provided UUID)
        if not self.string_uuid:
            self.string_uuid = uuid.uuid4()

        # Full clean to run validation
        self.full_clean()

        super().save(*args, **kwargs)

    def get_hierarchy_path(self):
        """Get the full hierarchy path for this string."""
        path = []
        current = self
        max_depth = 10  # Prevent infinite loops

        while current and max_depth > 0:
            path.insert(0, {
                'id': current.id,
                'value': current.value,
                'field_level': current.field.field_level
            })
            current = current.parent
            max_depth -= 1

        return path

    def get_child_strings(self):
        """Get all direct child strings."""
        return self.children.all()

    def can_have_children(self):
        """Check if this string can have child strings."""
        next_field = self.field.next_field
        return next_field is not None

    def suggest_child_field(self):
        """Suggest the next field for child string generation."""
        return self.field.next_field


class ProjectStringDetail(TimeStampModel, WorkspaceMixin):
    """
    Represents dimension values used in project string generation.

    Stores the specific dimension values that were combined to create
    the parent project string according to the naming rule.
    """

    # Relationships
    string = models.ForeignKey(
        ProjectString,
        on_delete=models.CASCADE,
        related_name="details",
        help_text="Project string this detail belongs to"
    )
    dimension = models.ForeignKey(
        "master_data.Dimension",
        on_delete=models.CASCADE,
        related_name="project_string_details",
        help_text="Dimension this value represents"
    )
    dimension_value = models.ForeignKey(
        "master_data.DimensionValue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_string_details",
        help_text="Predefined dimension value (for list-type dimensions)"
    )

    # Fields
    dimension_value_freetext = models.CharField(
        max_length=FREETEXT_LENGTH,
        null=True,
        blank=True,
        help_text="Free-text dimension value (for text-type dimensions)"
    )
    is_inherited = models.BooleanField(
        default=False,
        help_text="Whether this value was inherited from parent string"
    )

    class Meta:
        verbose_name = "Project String Detail"
        verbose_name_plural = "Project String Details"
        # Unique per workspace
        unique_together = [('workspace', 'string', 'dimension')]
        ordering = ['workspace', 'string', 'dimension']
        indexes = [
            models.Index(fields=['string', 'dimension']),
        ]

    def __str__(self):
        return f"{self.string} - {self.dimension.name}: {self.get_effective_value()}"

    def clean(self):
        """Validate the string detail configuration."""
        super().clean()

        # Ensure either dimension_value or dimension_value_freetext is provided
        if not self.dimension_value and not self.dimension_value_freetext:
            raise ValidationError(
                "Either dimension value or freetext value must be provided")

        if self.dimension_value and self.dimension_value_freetext:
            raise ValidationError(
                "Cannot specify both dimension value and freetext value")

        # Validate workspace consistency
        if self.string and self.string.workspace != self.workspace:
            raise ValidationError("String must belong to the same workspace")
        if self.dimension and self.dimension.workspace != self.workspace:
            raise ValidationError(
                "Dimension must belong to the same workspace")
        if self.dimension_value and self.dimension_value.workspace != self.workspace:
            raise ValidationError(
                "Dimension value must belong to the same workspace")

    def save(self, *args, **kwargs):
        """Auto-set workspace from string."""
        if not self.workspace_id and self.string_id:
            self.workspace = self.string.workspace
        super().save(*args, **kwargs)

    def get_effective_value(self):
        """Get the effective value (either from dimension_value or freetext)."""
        if self.dimension_value:
            return self.dimension_value.value
        return self.dimension_value_freetext
