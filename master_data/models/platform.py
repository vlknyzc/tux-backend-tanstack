from django.db import models
from django.urls import reverse
from .base import TimeStampModel


class Platform(TimeStampModel):
    # Fields
    platform_type = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=50, unique=True)
    icon_name = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("master_data_Platform_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Platform_update", args=(self.pk,))
