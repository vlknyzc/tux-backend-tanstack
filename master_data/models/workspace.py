"""
Workspace model for the master_data app.
"""

from django.db import models
from django.urls import reverse
from django.conf import settings

from .base import TimeStampModel, default_workspace_logo
from ..constants import STANDARD_NAME_LENGTH, SLUG_LENGTH, StatusChoices, WORKSPACE_LOGO_UPLOAD_PATH
from ..utils import generate_unique_slug


class Workspace(TimeStampModel):
    """
    Represents a workspace in the system.

    A workspace is a logical grouping or organization unit that contains
    multiple projects, rules, and naming conventions.
    """

    # Fields
    name = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        unique=True,
        help_text="Unique name for this workspace"
    )
    slug = models.SlugField(
        max_length=SLUG_LENGTH,
        unique=True,
        blank=True,
        help_text="URL-friendly version of the name (auto-generated)"
    )
    logo = models.ImageField(
        upload_to=WORKSPACE_LOGO_UPLOAD_PATH,
        default=default_workspace_logo,
        null=True,
        blank=True,
        help_text="Logo image for this workspace"
    )
    status = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        help_text="Current status of this workspace"
    )

    class Meta:
        verbose_name = "Workspace"
        verbose_name_plural = "Workspaces"
        ordering = ['name']

    def save(self, *args, **kwargs):
        """Override save to generate slug automatically."""
        if not self.slug:
            self.slug = generate_unique_slug(self, 'name', 'slug', SLUG_LENGTH)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("master_data_Workspace_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Workspace_update", args=(self.pk,))
