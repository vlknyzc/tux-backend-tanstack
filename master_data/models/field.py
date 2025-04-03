from django.db import models
from django.urls import reverse

from .base import TimeStampModel


class Field(TimeStampModel):
    platform = models.ForeignKey(
        "master_data.Platform", on_delete=models.CASCADE, related_name="fields")

    # Fields
    name = models.CharField(max_length=30)
    field_level = models.SmallIntegerField(null=False, blank=False)
    next_field = models.ForeignKey("master_data.Field", on_delete=models.CASCADE,
                                   null=True, blank=True, related_name="fields")

    class Meta:
        unique_together = ('platform', 'name', 'field_level')

    def __str__(self):
        return str(self.platform.name + " - " + self.name)

    def get_absolute_url(self):
        return reverse("master_data_Field_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Field_update", args=(self.pk,))
