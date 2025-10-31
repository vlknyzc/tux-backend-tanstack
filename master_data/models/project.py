"""
Project models for the master_data app.
Handles project management for workspace-scoped string generation.
"""

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

from .base import TimeStampModel, WorkspaceMixin
from ..constants import STANDARD_NAME_LENGTH, DESCRIPTION_LENGTH, SLUG_LENGTH
from master_data.utils import generate_unique_slug


# Enum choices
class ProjectStatusChoices(models.TextChoices):
    PLANNING = 'planning', 'Planning'
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    ARCHIVED = 'archived', 'Archived'


class ApprovalStatusChoices(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class ProjectMemberRoleChoices(models.TextChoices):
    OWNER = 'owner', 'Owner'
    EDITOR = 'editor', 'Editor'
    VIEWER = 'viewer', 'Viewer'


class ProjectActivityTypeChoices(models.TextChoices):
    PROJECT_CREATED = 'project_created', 'Project Created'
    PLATFORM_ADDED = 'platform_added', 'Platform Added'
    PLATFORM_REMOVED = 'platform_removed', 'Platform Removed'
    MEMBER_ASSIGNED = 'member_assigned', 'Member Assigned'
    MEMBER_UNASSIGNED = 'member_unassigned', 'Member Unassigned'
    STRINGS_GENERATED = 'strings_generated', 'Strings Generated'
    STATUS_CHANGED = 'status_changed', 'Status Changed'
    PROJECT_UPDATED = 'project_updated', 'Project Updated'
    SUBMITTED_FOR_APPROVAL = 'submitted_for_approval', 'Submitted for Approval'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class ApprovalActionChoices(models.TextChoices):
    SUBMITTED = 'submitted', 'Submitted'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class Project(TimeStampModel, WorkspaceMixin):
    """
    Represents a project for organizing platform-specific strings.

    Projects are workspace-scoped containers that replace the submission concept
    for platform-specific string management.
    """

    # Fields
    name = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        help_text="Project name"
    )
    slug = models.SlugField(
        max_length=SLUG_LENGTH,
        blank=True,
        help_text="URL-friendly version of the name (auto-generated)"
    )
    description = models.TextField(
        max_length=DESCRIPTION_LENGTH,
        null=True,
        blank=True,
        help_text="Optional description of this project"
    )
    status = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        choices=ProjectStatusChoices.choices,
        default=ProjectStatusChoices.PLANNING,
        help_text="Current status of this project"
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Project start date"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Project end date"
    )

    # Relationships
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        help_text="Project owner"
    )

    # Approval fields
    approval_status = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        choices=ApprovalStatusChoices.choices,
        default=ApprovalStatusChoices.DRAFT,
        help_text="Approval status of this project"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_projects",
        help_text="User who approved this project"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this project was approved"
    )
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_projects",
        help_text="User who rejected this project"
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this project was rejected"
    )
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for rejection"
    )

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        unique_together = [('workspace', 'slug')]  # Slug unique per workspace
        ordering = ['workspace', '-created']
        indexes = [
            models.Index(fields=['workspace', 'slug']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['workspace', 'owner']),
            models.Index(fields=['workspace', 'approval_status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.workspace.name})"

    def save(self, *args, **kwargs):
        """Override save to generate slug automatically."""
        if not self.slug:
            self.slug = generate_unique_slug(self, 'name', 'slug', SLUG_LENGTH)
        super().save(*args, **kwargs)

    def clean(self):
        """Validate the project configuration."""
        super().clean()

        # Validate end_date >= start_date
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError("End date must be after start date")


class PlatformAssignment(TimeStampModel, WorkspaceMixin):
    """
    Represents a platform assignment within a project.

    Links a platform to a project and tracks platform-specific approval status.
    """

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="platform_assignments",
        help_text="Project this platform is assigned to"
    )
    platform = models.ForeignKey(
        "master_data.Platform",
        on_delete=models.CASCADE,
        related_name="project_assignments",
        help_text="Platform assigned to this project"
    )
    assigned_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="platform_assignments",
        blank=True,
        help_text="Users assigned to work on this platform"
    )

    # Approval fields
    approval_status = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        choices=ApprovalStatusChoices.choices,
        default=ApprovalStatusChoices.DRAFT,
        help_text="Approval status of this platform assignment"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_platform_assignments",
        help_text="User who approved this platform assignment"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this platform assignment was approved"
    )
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_platform_assignments",
        help_text="User who rejected this platform assignment"
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this platform assignment was rejected"
    )
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for rejection"
    )

    class Meta:
        verbose_name = "Platform Assignment"
        verbose_name_plural = "Platform Assignments"
        unique_together = [('project', 'platform')]  # One platform per project
        ordering = ['project', 'platform']
        indexes = [
            models.Index(fields=['project', 'platform']),
            models.Index(fields=['workspace', 'approval_status']),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.platform.name}"

    def save(self, *args, **kwargs):
        """Override save to auto-set workspace from project."""
        if not self.workspace_id and self.project_id:
            self.workspace = self.project.workspace
        super().save(*args, **kwargs)


class ProjectMember(TimeStampModel):
    """
    Represents a team member assigned to a project with a specific role.
    """

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="team_members",
        help_text="Project this member belongs to"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
        help_text="User assigned to this project"
    )

    # Fields
    role = models.CharField(
        max_length=20,
        choices=ProjectMemberRoleChoices.choices,
        default=ProjectMemberRoleChoices.VIEWER,
        help_text="User's role in this project"
    )

    class Meta:
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"
        unique_together = [('project', 'user')]  # One role per user per project
        ordering = ['project', 'user']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.project.name} ({self.role})"


class ProjectActivity(TimeStampModel):
    """
    Tracks activities and changes within a project for audit trail.
    """

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="activities",
        help_text="Project this activity belongs to"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_activities",
        help_text="User who performed this action"
    )

    # Fields
    type = models.CharField(
        max_length=50,
        choices=ProjectActivityTypeChoices.choices,
        help_text="Type of activity"
    )
    description = models.TextField(
        help_text="Human-readable description of the activity"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context about the activity"
    )

    class Meta:
        verbose_name = "Project Activity"
        verbose_name_plural = "Project Activities"
        ordering = ['project', '-created']
        indexes = [
            models.Index(fields=['project', '-created']),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.type} ({self.created})"


class ApprovalHistory(TimeStampModel):
    """
    Tracks approval history for projects and platform assignments.
    """

    # Relationships (either project OR platform_assignment, not both)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="approval_history",
        help_text="Project this approval relates to (for project-level approval)"
    )
    platform_assignment = models.ForeignKey(
        PlatformAssignment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="approval_history",
        help_text="Platform assignment this approval relates to (for platform-level approval)"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="approval_actions",
        help_text="User who performed this action"
    )

    # Fields
    action = models.CharField(
        max_length=20,
        choices=ApprovalActionChoices.choices,
        help_text="Type of approval action"
    )
    comment = models.TextField(
        null=True,
        blank=True,
        help_text="Optional comment or reason"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this action was performed"
    )

    class Meta:
        verbose_name = "Approval History"
        verbose_name_plural = "Approval Histories"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['project', '-timestamp']),
            models.Index(fields=['platform_assignment', '-timestamp']),
        ]

    def __str__(self):
        target = self.project or self.platform_assignment
        return f"{target} - {self.action} by {self.user} ({self.timestamp})"

    def clean(self):
        """Validate that either project OR platform_assignment is set, not both."""
        super().clean()

        if self.project and self.platform_assignment:
            raise ValidationError(
                "Cannot specify both project and platform_assignment"
            )

        if not self.project and not self.platform_assignment:
            raise ValidationError(
                "Must specify either project or platform_assignment"
            )
