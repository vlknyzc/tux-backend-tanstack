from django.db import models
from django.urls import reverse

from .base import TimeStampModel


class Submission(TimeStampModel):
    SUBMITTED = "submitted"
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    STATUSES = [
        (SUBMITTED, 'Submitted'),
        (DRAFT, 'Draft'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    # relationships
    rule = models.ForeignKey(
        "master_data.Rule", on_delete=models.CASCADE, related_name="strings")

    selected_parent_string = models.ForeignKey(
        "master_data.String", on_delete=models.CASCADE, related_name="selected_parent_string", null=True, blank=True)
    starting_field = models.ForeignKey(
        "master_data.Field", on_delete=models.CASCADE, related_name="starting_field", null=False, blank=False)

    name = models.CharField(max_length=30)
    description = models.TextField(max_length=500, null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUSES,
        default=DRAFT,
    )

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("master_data_Submission_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Submission_update", args=(self.pk,))
