from django.db import models
from django.urls import reverse

from .base import TimeStampModel


class Rule(TimeStampModel):
    ACTIVE = "active"
    INACTIVE = "inactive"
    STATUSES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]

    # Relationships
    # convention = models.ForeignKey(
    #     "master_data.Convention", on_delete=models.CASCADE, related_name="rules")
    platform = models.ForeignKey(
        "master_data.Platform", on_delete=models.CASCADE, related_name="rules")

    # Fields
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUSES,
        default=ACTIVE,
    )

    def __str__(self):
        return str(self.name + " - " + self.platform.name)

    def get_absolute_url(self):
        return reverse("master_data_Rule_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Rule_update", args=(self.pk,))


class RuleDetail(TimeStampModel):
    # Relationships
    rule = models.ForeignKey(
        "master_data.Rule", on_delete=models.CASCADE, related_name="rule_details")
    field = models.ForeignKey(
        "master_data.Field", on_delete=models.CASCADE, related_name="rule_details")
    dimension = models.ForeignKey(
        "master_data.Dimension", on_delete=models.CASCADE, related_name="rule_details")

    # Fields
    prefix = models.CharField(
        max_length=20, null=True, blank=True)
    suffix = models.CharField(
        max_length=20, null=True, blank=True)
    delimiter = models.CharField(
        max_length=1, null=True, blank=True)
    dimension_order = models.SmallIntegerField()

    class Meta:
        unique_together = ("rule", "field",  'dimension_order')

    def __str__(self):
        return str(self.rule.name + " - " + self.field.name + " - " + self.dimension.name)

    def get_absolute_url(self):
        return reverse("master_data_RuleDetail_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_RuleDetail_update", args=(self.pk,))
