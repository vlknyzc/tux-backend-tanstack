from django.db import models
from django.urls import reverse

# TODO - link models with workspace to filter out responses


class TimeStampModel(models.Model):

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


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
        pass

    def __str__(self):
        return str(self.name)

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
    dimension_value_code = models.CharField(max_length=30)
    valid_from = models.DateField(null=True, blank=True)
    definition = models.TextField(max_length=500, null=True, blank=True)
    dimension_value = models.CharField(max_length=30)
    valid_until = models.DateField(null=True, blank=True)
    dimension_value_label = models.CharField(max_length=50)
    dimension_value_utm = models.CharField(max_length=30)

    class Meta:
        unique_together = ('dimension', 'dimension_value')

    def __str__(self):
        return str(self.dimension_value)

    def get_absolute_url(self):
        return reverse("master_data_JunkDimension_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_JunkDimension_update", args=(self.pk,))


class Workspace(TimeStampModel):

    # Relationships
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="workspace")

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


class Platform(TimeStampModel):

    # Relationships
    workspace = models.ForeignKey(
        "master_data.Workspace", on_delete=models.CASCADE, related_name="platforms")

    # Fields
    platform_type = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    platform_field = models.CharField(max_length=30)
    field_level = models.SmallIntegerField()

    class Meta:
        unique_together = ('name', 'platform_field', 'field_level')

    def __str__(self):
        return str(self.name + " - " + self.platform_field)

    def get_absolute_url(self):
        return reverse("master_data_Platform_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Platform_update", args=(self.pk,))


class Rule(TimeStampModel):

    # Relationships
    workspace = models.ForeignKey(
        "master_data.Workspace", on_delete=models.CASCADE, related_name="rules")

    # Fields
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=30)

    class Meta:
        unique_together = ('workspace', 'name')

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("master_data_Rule_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Rule_update", args=(self.pk,))


class Structure(TimeStampModel):

    # Relationships
    rule = models.ForeignKey(
        "master_data.Rule", on_delete=models.CASCADE, related_name="structures")
    dimension = models.ForeignKey(
        "master_data.Dimension", on_delete=models.CASCADE, related_name="structures")
    platform = models.ForeignKey(
        "master_data.Platform", on_delete=models.CASCADE, related_name="structures")

    # Fields
    delimeter_after_dimension = models.CharField(
        max_length=1, null=True, blank=True)
    delimeter_before_dimension = models.CharField(
        max_length=1, null=True, blank=True)
    dimension_order = models.SmallIntegerField()

    class Meta:
        unique_together = ('rule', 'platform', 'dimension_order')

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("master_data_Structure_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Structure_update", args=(self.pk,))
