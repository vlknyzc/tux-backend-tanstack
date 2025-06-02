"""
Submission model for the master_data app.
"""

from django.db import models
from django.urls import reverse
from django.conf import settings

from .base import TimeStampModel
from ..constants import STANDARD_NAME_LENGTH, DESCRIPTION_LENGTH, SubmissionStatusChoices


class Submission(TimeStampModel):
    """
    Represents a submission for naming convention generation.

    A submission contains the configuration and rules needed to generate
    naming strings according to platform-specific conventions.
    """

    # Relationships
    rule = models.ForeignKey(
        "master_data.Rule",
        on_delete=models.CASCADE,
        related_name="submissions",
        help_text="The naming rule to apply for this submission"
    )
    selected_parent_string = models.ForeignKey(
        "master_data.String",
        on_delete=models.CASCADE,
        related_name="selected_parent_string",
        null=True,
        blank=True,
        help_text="Parent string to base this submission on (if any)"
    )
    starting_field = models.ForeignKey(
        "master_data.Field",
        on_delete=models.CASCADE,
        related_name="starting_field",
        help_text="The field to start the naming sequence from"
    )

    # Fields
    name = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        help_text="Name for this submission"
    )
    description = models.TextField(
        max_length=DESCRIPTION_LENGTH,
        null=True,
        blank=True,
        help_text="Optional description of this submission"
    )
    status = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        choices=SubmissionStatusChoices.choices,
        default=SubmissionStatusChoices.DRAFT,
        help_text="Current status of this submission"
    )

    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"
        ordering = ['-created']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("master_data_Submission_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Submission_update", args=(self.pk,))
