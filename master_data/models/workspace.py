from django.db import models
from django.urls import reverse
from django.conf import settings

from .base import TimeStampModel, default_workspace_logo


class Workspace(TimeStampModel):
    ACTIVE = "active"
    INACTIVE = "inactive"
    STATUSES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]

    # Relationships
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspace")

    # Fields
    name = models.CharField(max_length=30, unique=True)
    logo = models.ImageField(
        upload_to='workspaces/logos/',
        default=default_workspace_logo,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=30,
        choices=STATUSES,
        default=ACTIVE,
    )

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("master_data_Workspace_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Workspace_update", args=(self.pk,))
