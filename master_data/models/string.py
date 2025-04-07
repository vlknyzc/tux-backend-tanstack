from django.db import models
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver

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

    name = models.CharField(max_length=30)
    description = models.TextField(max_length=500, null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUSES,
        default=DRAFT,
    )

    def __str__(self):
        return str(self.name)


class String(TimeStampModel):
    # Relationships
    parent = models.ForeignKey("master_data.String", on_delete=models.CASCADE,
                               null=True, blank=True, related_name="strings")
    field = models.ForeignKey(
        "master_data.Field", on_delete=models.CASCADE, related_name="strings")
    # convention = models.ForeignKey(
    #     "master_data.Convention", on_delete=models.CASCADE, related_name="strings")
    submission = models.ForeignKey(
        "master_data.Submission", on_delete=models.CASCADE, related_name="strings")

    # Fields
    value = models.CharField(max_length=400)
    string_uuid = models.UUIDField()
    parent_uuid = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("master_data_String_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_String_update", args=(self.pk,))


class StringDetail(TimeStampModel):
    # Relationships
    string = models.ForeignKey(
        "master_data.String",
        on_delete=models.CASCADE,
        related_name="string_details"
    )

    dimension = models.ForeignKey(
        "master_data.Dimension",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="string_details"
    )

    dimension_value = models.ForeignKey(
        "master_data.DimensionValue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="string_details"
    )
    dimension_value_freetext = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.string}"

    def get_absolute_url(self):
        return reverse("master_data_StringDetail_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_StringDetail_update", args=(self.pk,))


@receiver(post_save, sender=StringDetail)
def update_parent(sender, instance, created, **kwargs):
    if created and instance.parent_uuid:
        try:
            parent_string = String.objects.get(
                string_uuid=instance.parent_uuid)
            instance.parent = parent_string
            instance.save()
        except String.DoesNotExist:
            pass  # Handle the case where parent does not exist
