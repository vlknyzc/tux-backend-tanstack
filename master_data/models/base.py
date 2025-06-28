"""
Base models and utilities for master_data app.
"""

from django.db import models
from django.conf import settings
from threading import local

from ..constants import DEFAULT_WORKSPACE_LOGO


def default_workspace_logo():
    """Return the default workspace logo path."""
    return DEFAULT_WORKSPACE_LOGO


# Thread-local storage for current workspace context
_thread_locals = local()


def get_current_workspace():
    """Get the current workspace from thread-local storage"""
    return getattr(_thread_locals, 'workspace_id', None)


def set_current_workspace(workspace_id):
    """Set the current workspace in thread-local storage"""
    _thread_locals.workspace_id = workspace_id


class WorkspaceManager(models.Manager):
    """
    Manager that automatically filters by workspace context
    """

    def get_queryset(self):
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


class WorkspaceMixin(models.Model):
    """
    Mixin to add workspace relationship to models for multi-tenancy
    """
    workspace = models.ForeignKey(
        'master_data.Workspace',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        help_text="Workspace this record belongs to"
    )

    # Use custom manager for automatic workspace filtering
    objects = WorkspaceManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Auto-set workspace if not provided and context exists
        if not self.workspace_id:
            current_workspace = get_current_workspace()
            if current_workspace:
                self.workspace_id = current_workspace
        super().save(*args, **kwargs)


class TimeStampModel(models.Model):
    """
    Abstract base model that provides audit fields for all master data models.

    Provides:
        - created: When the record was created
        - last_updated: When the record was last modified  
        - created_by: User who created the record
    """
    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        help_text="When this record was created"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        editable=False,
        help_text="When this record was last updated"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created",
        null=True,
        blank=True,
        editable=False,
        help_text="User who created this record"
    )

    class Meta:
        abstract = True
