"""
Entity model for the master_data app.
"""

from django.db import models
from django.urls import reverse

from .base import TimeStampModel
from ..constants import STANDARD_NAME_LENGTH


class Entity(TimeStampModel):
    """
    Represents an entity within a platform's naming structure.

    Entities define the hierarchical components of a naming convention.
    For example: environment, project, service, etc.

    Entities are workspace-agnostic - they are shared across all workspaces.
    """

    # Relationships
    platform = models.ForeignKey(
        "master_data.Platform",
        on_delete=models.CASCADE,
        related_name="entities",
        help_text="Platform this entity belongs to"
    )
    next_entity = models.ForeignKey(
        "master_data.Entity",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_entities",
        help_text="Next entity in the hierarchy sequence"
    )

    # Fields
    name = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        help_text="Name of this entity (e.g., 'environment', 'project')"
    )
    entity_level = models.SmallIntegerField(
        help_text="Hierarchical level of this entity (1, 2, 3, etc.)"
    )

    class Meta:
        verbose_name = "Entity"
        verbose_name_plural = "Entities"
        # Unique globally per platform
        unique_together = [('platform', 'name', 'entity_level')]
        ordering = ['platform', 'entity_level']

    def __str__(self):
        return f"{self.platform.name} - {self.name} (Level {self.entity_level})"

    def get_absolute_url(self):
        return reverse("master_data_Entity_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Entity_update", args=(self.pk,))
