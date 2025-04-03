# from django.db import models
# from django.urls import reverse

# from .base import TimeStampModel


# class Convention(TimeStampModel):
#     ACTIVE = "active"
#     INACTIVE = "inactive"
#     STATUSES = [
#         (ACTIVE, 'Active'),
#         (INACTIVE, 'Inactive'),
#     ]

#     name = models.CharField(max_length=30, unique=True)
#     description = models.TextField(max_length=500, null=True, blank=True)
#     status = models.CharField(
#         max_length=30,
#         choices=STATUSES,
#         default=ACTIVE,
#     )
#     valid_from = models.DateField()
#     valid_until = models.DateField(null=True, blank=True)

#     def __str__(self):
#         return str(self.name)


# class ConventionPlatform(models.Model):
#     # Relationships
#     convention = models.ForeignKey(
#         "master_data.Convention", on_delete=models.CASCADE, related_name="convention_platforms")
#     platform = models.ForeignKey(
#         "master_data.Platform", on_delete=models.CASCADE, related_name="convention_platforms")

#     # Fields
#     last_updated = models.DateTimeField(auto_now=True, editable=False)
#     created = models.DateTimeField(auto_now_add=True, editable=False)

#     def __str__(self):
#         return str(self.name)

#     def get_absolute_url(self):
#         return reverse("master_data_ConventionPlatform_detail", args=(self.pk,))

#     def get_update_url(self):
#         return reverse("master_data_ConventionPlatform_update", args=(self.pk,))
