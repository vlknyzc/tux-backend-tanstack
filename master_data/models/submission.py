"""
Submission model for the master_data app.

DEPRECATED: Submissions have been replaced by Projects.
This model is kept for backward compatibility and data preservation only.
"""

from django.db import models
from django.urls import reverse
from django.conf import settings

from .base import TimeStampModel, WorkspaceMixin
from ..constants import STANDARD_NAME_LENGTH, DESCRIPTION_LENGTH, SLUG_LENGTH
from master_data.utils import generate_unique_slug


# Status choices for legacy Submission model
class SubmissionStatusChoices(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    DRAFT = "draft", "Draft"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Submission(TimeStampModel, WorkspaceMixin):
    """
    [DEPRECATED] Represents a submission for naming convention generation.

    This model has been replaced by the Project model which provides enhanced
    functionality including platform-specific assignments and team collaboration.

    Kept for backward compatibility and data preservation only.
    New implementations should use the Project model instead.
    """

    # Relationships
    rule = models.ForeignKey(
        "master_data.Rule",
        on_delete=models.CASCADE,
        related_name="submissions",
        help_text="The naming rule to apply for this submission"
    )
    starting_entity = models.ForeignKey(
        "master_data.Entity",
        on_delete=models.CASCADE,
        related_name="starting_entity",
        help_text="The field to start the naming sequence from"
    )

    # Fields
    name = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        help_text="Name for this submission"
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
        ordering = ['workspace', '-created']
        unique_together = [('workspace', 'name')]  # Name unique per workspace

    def save(self, *args, **kwargs):
        """Override save to generate slug automatically."""
        if not self.slug:
            self.slug = generate_unique_slug(self, 'name', 'slug', SLUG_LENGTH)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("master_data_Submission_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Submission_update", args=(self.pk,))
