"""
Dimension models for the master_data app.
"""

from django.db import models
from django.urls import reverse

from .base import TimeStampModel
from ..constants import (
    STANDARD_NAME_LENGTH, LONG_NAME_LENGTH, DESCRIPTION_LENGTH,
    UTM_LENGTH, StatusChoices, DimensionTypeChoices
)


class Dimension(TimeStampModel):
    """
    Represents a dimension for categorizing and structuring naming conventions.

    Dimensions define the different aspects or categories that can be used
    in naming rules (e.g., environment, region, cost center).
    """

    # Relationships
    parent = models.ForeignKey(
        "master_data.Dimension",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_dimensions",
        help_text="Parent dimension if this is a sub-dimension"
    )

    # Fields
    name = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        unique=True,
        help_text="Unique name for this dimension"
    )
    description = models.TextField(
        max_length=DESCRIPTION_LENGTH,
        null=True,
        blank=True,
        help_text="Description of what this dimension represents"
    )
    type = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        choices=DimensionTypeChoices.choices,
        default=DimensionTypeChoices.LIST,
        help_text="Type of dimension: list of values or free text"
    )
    status = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        help_text="Current status of this dimension"
    )

    class Meta:
        verbose_name = "Dimension"
        verbose_name_plural = "Dimensions"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("master_data_Dimension_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Dimension_update", args=(self.pk,))


class DimensionValue(TimeStampModel):
    """
    Represents a specific value within a dimension.

    For list-type dimensions, these are the predefined values that can be
    selected (e.g., 'prod', 'dev', 'test' for an environment dimension).
    """

    # Relationships
    dimension = models.ForeignKey(
        "master_data.Dimension",
        on_delete=models.CASCADE,
        related_name="dimension_values",
        help_text="The dimension this value belongs to"
    )
    parent = models.ForeignKey(
        "master_data.DimensionValue",
        on_delete=models.CASCADE,
        related_name="child_dimension_values",
        null=True,
        blank=True,
        help_text="Parent value if this is a sub-value"
    )

    # Fields
    value = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        help_text="The actual value (e.g., 'prod', 'dev')"
    )
    label = models.CharField(
        max_length=LONG_NAME_LENGTH,
        help_text="Human-readable label for this value"
    )
    utm = models.CharField(
        max_length=UTM_LENGTH,
        help_text="UTM or tracking code for this value"
    )
    description = models.TextField(
        max_length=DESCRIPTION_LENGTH,
        null=True,
        blank=True,
        help_text="Description of what this value represents"
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        help_text="Date from which this value is valid"
    )
    valid_until = models.DateField(
        null=True,
        blank=True,
        help_text="Date until which this value is valid"
    )

    class Meta:
        verbose_name = "Dimension Value"
        verbose_name_plural = "Dimension Values"
        unique_together = ('dimension', 'value')
        ordering = ['dimension', 'value']

    def __str__(self):
        return f"{self.dimension.name}: {self.value}"

    def get_absolute_url(self):
        return reverse("master_data_DimensionValue_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_DimensionValue_update", args=(self.pk,))
