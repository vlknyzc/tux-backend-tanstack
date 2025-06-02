"""
Base models and utilities for master_data app.
"""

from django.db import models
from django.conf import settings

from ..constants import DEFAULT_WORKSPACE_LOGO


def default_workspace_logo():
    """Return the default workspace logo path."""
    return DEFAULT_WORKSPACE_LOGO


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
