from django.db import models
from django.urls import reverse
from django.conf import settings
# from django.contrib.auth.models import User

# TODO - link models with workspace to filter out responses


class TimeStampModel(models.Model):

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class Workspace(TimeStampModel):

    # Relationships
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspace")

    # Fields
    name = models.CharField(max_length=30, unique=True)

    class Meta:
        pass

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("master_data_Workspace_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Workspace_update", args=(self.pk,))


class Convention(TimeStampModel):
    workspace = models.ForeignKey(
        "master_data.Workspace", on_delete=models.CASCADE, related_name="conventions")

    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(max_length=500, null=True, blank=True)

    def __str__(self):
        return str(self.name)


class Platform(TimeStampModel):

    # Fields
    platform_type = models.CharField(max_length=30)
    name = models.CharField(max_length=30)

    def __str__(self):
        return str(self.name)

    # def get_absolute_url(self):
    #     return reverse("master_data_Platform_detail", args=(self.pk,))

    # def get_update_url(self):
    #     return reverse("master_data_Platform_update", args=(self.pk,))


class Field(TimeStampModel):
    platform = models.ForeignKey(
        "master_data.Platform", on_delete=models.CASCADE, related_name="fields")

    # Fields
    field_name = models.CharField(max_length=30)
    field_level = models.SmallIntegerField(null=False, blank=False)
    next_field = models.ForeignKey("master_data.Field", on_delete=models.CASCADE,
                                   null=True, blank=True, related_name="fields")

    class Meta:
        unique_together = ('platform', 'field_name', 'field_level')

    def __str__(self):
        return str(self.platform.name + " - " + self.field_name)

    def get_absolute_url(self):
        return reverse("master_data_Field_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Field_update", args=(self.pk,))


class Dimension(TimeStampModel):
    MASTERED = "mastered"
    FREE_TEXT = "free-text"
    FREE_TEXT_WITH_VALIDATIONS = "free-text-with-validations"
    RULE = "rule"
    TYPES = [
        (MASTERED, 'Mastered'),
        (FREE_TEXT, 'Free Text'),
        (RULE, 'Rule'),
        (FREE_TEXT_WITH_VALIDATIONS, 'Free Text With Validations')
    ]

    # Relationships
    parent = models.ForeignKey("master_data.Dimension", on_delete=models.CASCADE,
                               null=True, blank=True, related_name="dimensions")

    workspace = models.ForeignKey(
        "master_data.Workspace", on_delete=models.CASCADE, related_name="dimensions")

    # Fields
    definition = models.TextField(max_length=500, null=True, blank=True)
    dimension_type = models.CharField(
        max_length=30,
        choices=TYPES,
        default=MASTERED,
    )
    name = models.CharField(max_length=30)

    class Meta:
        unique_together = ('name', 'workspace')

    def __str__(self):
        return str(f'{self.workspace.name} - {self.name}')

    def get_absolute_url(self):
        return reverse("master_data_Dimension_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Dimension_update", args=(self.pk,))


class JunkDimension(TimeStampModel):

    # Relationships
    dimension = models.ForeignKey(
        "master_data.Dimension", on_delete=models.CASCADE, related_name="junk_dimension")
    parent = models.ForeignKey("master_data.JunkDimension",
                               on_delete=models.CASCADE, related_name="junk_dimension", null=True, blank=True)

    # Fields
    # dimension_value_code = models.CharField(max_length=30)
    valid_from = models.DateField(null=True, blank=True)
    definition = models.TextField(max_length=500, null=True, blank=True)
    dimension_value = models.CharField(max_length=30)
    valid_until = models.DateField(null=True, blank=True)
    dimension_value_label = models.CharField(max_length=50)
    dimension_value_utm = models.CharField(max_length=30)

    @property
    def workspace(self):
        return self.dimension.workspace.id if self.dimension else None

    class Meta:
        unique_together = ('dimension', 'dimension_value')

    def __str__(self):
        return str(self.dimension_value)

    def get_absolute_url(self):
        return reverse("master_data_JunkDimension_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_JunkDimension_update", args=(self.pk,))


class Structure(TimeStampModel):

    # Relationships
    convention = models.ForeignKey(
        "master_data.Convention", on_delete=models.CASCADE, related_name="structures")

    dimension = models.ForeignKey(
        "master_data.Dimension", on_delete=models.CASCADE, related_name="structures")
    field = models.ForeignKey(
        "master_data.Field", on_delete=models.CASCADE, related_name="structures")

    # Fields

    delimeter_after_dimension = models.CharField(
        max_length=20, null=True, blank=True)
    delimeter_before_dimension = models.CharField(
        max_length=20, null=True, blank=True)
    dimension_order = models.SmallIntegerField()

    class Meta:
        unique_together = ("convention", 'field', 'dimension_order')

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("master_data_Structure_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Structure_update", args=(self.pk,))
