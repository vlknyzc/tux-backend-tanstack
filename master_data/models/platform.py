"""
Platform model for the master_data app.
"""

from django.db import models
from django.urls import reverse
from .base import TimeStampModel
from ..constants import STANDARD_NAME_LENGTH, SLUG_LENGTH


class Platform(TimeStampModel):
    """
    Represents different platforms in the system.

    A platform is a target environment or system where naming conventions apply.
    Examples: AWS, Azure, Kubernetes, etc.

    Platforms are workspace-agnostic - they are shared across all workspaces.
    """

    # Fields
    platform_type = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        help_text="Type or category of this platform"
    )
    name = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        help_text="Human-readable name of the platform"
    )
    slug = models.SlugField(
        max_length=SLUG_LENGTH,
        help_text="URL-friendly identifier for this platform"
    )
    icon_name = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="Name of the icon to display for this platform"
    )

    class Meta:
        verbose_name = "Platform"
        verbose_name_plural = "Platforms"
        ordering = ['name']
        unique_together = [('slug',)]  # Slug unique globally

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("master_data_Platform_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Platform_update", args=(self.pk,))
