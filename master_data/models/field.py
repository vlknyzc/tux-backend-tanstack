"""
Field model for the master_data app.
"""

from django.db import models
from django.urls import reverse

from .base import TimeStampModel
from ..constants import STANDARD_NAME_LENGTH


class Field(TimeStampModel):
    """
    Represents a field within a platform's naming structure.

    Fields define the hierarchical components of a naming convention.
    For example: environment, project, service, etc.
    """

    # Relationships
    platform = models.ForeignKey(
        "master_data.Platform",
        on_delete=models.CASCADE,
        related_name="fields",
        help_text="Platform this field belongs to"
    )
    next_field = models.ForeignKey(
        "master_data.Field",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_fields",
        help_text="Next field in the hierarchy sequence"
    )

    # Fields
    name = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        help_text="Name of this field (e.g., 'environment', 'project')"
    )
    field_level = models.SmallIntegerField(
        help_text="Hierarchical level of this field (1, 2, 3, etc.)"
    )

    class Meta:
        verbose_name = "Field"
        verbose_name_plural = "Fields"
        unique_together = ('platform', 'name', 'field_level')
        ordering = ['platform', 'field_level']

    def __str__(self):
        return f"{self.platform.name} - {self.name} (Level {self.field_level})"

    def get_absolute_url(self):
        return reverse("master_data_Field_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Field_update", args=(self.pk,))
