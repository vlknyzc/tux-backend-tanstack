from django.db import models
from django.urls import reverse

from .base import TimeStampModel


class Dimension(TimeStampModel):
    LIST = "list"
    FREE_TEXT = "text"
    TYPES = [
        (LIST, 'List'),
        (FREE_TEXT, 'Free Text'),
    ]

    ACTIVE = "active"
    INACTIVE = "inactive"
    STATUSES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]

    # Relationships
    parent = models.ForeignKey("master_data.Dimension", on_delete=models.CASCADE,
                               null=True, blank=True, related_name="dimensions")

    # Fields
    status = models.CharField(
        max_length=30,
        choices=STATUSES,
        default=ACTIVE,
    )
    definition = models.TextField(max_length=500, null=True, blank=True)
    dimension_type = models.CharField(
        max_length=30,
        choices=TYPES,
        default=LIST,
    )
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return str(f'{self.name}')

    def get_absolute_url(self):
        return reverse("master_data_Dimension_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Dimension_update", args=(self.pk,))


class DimensionValue(TimeStampModel):
    # Relationships
    dimension = models.ForeignKey(
        "master_data.Dimension", on_delete=models.CASCADE, related_name="dimension_values")
    parent = models.ForeignKey("master_data.DimensionValue",
                               on_delete=models.CASCADE, related_name="dimension_values", null=True, blank=True)

    # Fields
    valid_until = models.DateField(null=True, blank=True)
    dimension_value = models.CharField(max_length=30)
    dimension_value_label = models.CharField(max_length=50)
    dimension_value_utm = models.CharField(max_length=30)
    valid_from = models.DateField(null=True, blank=True)
    definition = models.TextField(max_length=500, null=True, blank=True)

    class Meta:
        unique_together = ('dimension', 'dimension_value')

    def __str__(self):
        return str(self.dimension_value)

    def get_absolute_url(self):
        return reverse("master_data_DimensionValue_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_DimensionValue_update", args=(self.pk,))
