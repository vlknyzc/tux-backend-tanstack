from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

import uuid
# from django.contrib.auth.models import User

# TODO - link models with workspace to filter out responses


def default_workspace_logo():
    return "workspaces/default/default-workspace-logo.png"


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
    logo = models.ImageField(
        upload_to='workspaces/logos/',
        default=default_workspace_logo,
        null=True,
        blank=True
    )

    class Meta:
        pass

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("master_data_Workspace_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Workspace_update", args=(self.pk,))


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


class Convention(TimeStampModel):
    workspace = models.ForeignKey(
        "master_data.Workspace", on_delete=models.CASCADE, related_name="conventions")

    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(max_length=500, null=True, blank=True)
    status = models.BooleanField(default=True)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.name)


class ConventionPlatform(models.Model):

    # Relationships
    convention = models.ForeignKey(
        "master_data.Convention", on_delete=models.CASCADE, related_name="convention_platforms")
    platform = models.ForeignKey(
        "master_data.Platform", on_delete=models.CASCADE, related_name="convention_platforms")

    # Fields
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("master_data_ConventionPlatform_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_ConventionPlatform_update", args=(self.pk,))


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


class String(TimeStampModel):

    # Relationships
    parent = models.ForeignKey("master_data.String", on_delete=models.CASCADE,
                               null=True, blank=True, related_name="strings")
    workspace = models.ForeignKey(
        "master_data.Workspace", on_delete=models.CASCADE)
    field = models.ForeignKey(
        "master_data.Field", on_delete=models.CASCADE, related_name="strings")
    convention = models.ForeignKey(
        "master_data.Convention", on_delete=models.CASCADE, related_name="strings")

    # Fields
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    string_value = models.CharField(max_length=400)
    string_uuid = models.UUIDField()
    parent_uuid = models.UUIDField(null=True, blank=True)

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("master_data_String_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_String_update", args=(self.pk,))


class StringItem(TimeStampModel):
    # Relationships
    string = models.ForeignKey(
        "master_data.String",
        on_delete=models.CASCADE,
        related_name="string_items"
    )
    structure = models.ForeignKey(
        "master_data.Structure",
        on_delete=models.CASCADE,
        related_name="string_items"
    )
    dimension_value = models.ForeignKey(
        "master_data.JunkDimension",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="string_items"
    )
    dimension_value_freetext = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    class Meta:
        pass

    def __str__(self):
        return f"{self.string} - {self.structure}"

    def get_absolute_url(self):
        return reverse("master_data_StringItem_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_StringItem_update", args=(self.pk,))


@receiver(post_save, sender=String)
def update_parent(sender, instance, created, **kwargs):
    if created and instance.parent_uuid:
        try:
            parent_string = String.objects.get(
                string_uuid=instance.parent_uuid)
            instance.parent = parent_string
            instance.save()
        except String.DoesNotExist:
            pass  # Handle the case where parent does not exist
