from django.contrib import admin
from django import forms

from . import models


class DimensionAdminForm(forms.ModelForm):

    class Meta:
        model = models.Dimension
        fields = "__all__"


class DimensionAdmin(admin.ModelAdmin):
    form = DimensionAdminForm
    list_display = [
        "definition",
        "dimension_type",
        "name",
    ]
    # readonly_fields = [
    #     "definition",
    #     "type",
    #     "name",
    # ]


class JunkDimensionAdminForm(forms.ModelForm):

    class Meta:
        model = models.JunkDimension
        fields = "__all__"


class JunkDimensionAdmin(admin.ModelAdmin):
    form = JunkDimensionAdminForm
    list_display = [
        # "dimension_value_code",
        "valid_from",
        "definition",
        "dimension_value",
        "valid_until",
        "dimension_value_label",
        "dimension_value_utm",
    ]
    # readonly_fields = [
    #     "dimension_value_code",
    #     "valid_from",
    #     "definition",
    #     "dimension_value",
    #     "valid_until",
    #     "dimension_value_label",
    #     "dimension_value_utm",
    # ]


class WorkspaceAdminForm(forms.ModelForm):

    class Meta:
        model = models.Workspace
        fields = "__all__"


class WorkspaceAdmin(admin.ModelAdmin):

    form = WorkspaceAdminForm
    list_display = [
        "name",
    ]
    readonly_fields = [
        "name",
    ]


class PlatformAdminForm(forms.ModelForm):

    class Meta:
        model = models.Platform
        fields = "__all__"


class PlatformAdmin(admin.ModelAdmin):
    form = PlatformAdminForm
    list_display = [
        "platform_type",
        "name",

    ]
    # readonly_fields = [
    #     "platform_type",
    #     "name",
    #     "platform_field",
    # ]


class FieldAdminForm(forms.ModelForm):

    class Meta:
        model = models.Field
        fields = "__all__"


class FieldAdmin(admin.ModelAdmin):
    form = FieldAdminForm
    list_display = [
        "name",
        "platform",
    ]
    # readonly_fields = [
    #     "name",
    #     "field_type",
    #     "platform",
    # ]


class ConventionAdminForm(forms.ModelForm):

    class Meta:
        model = models.Convention
        fields = "__all__"


class ConventionAdmin(admin.ModelAdmin):
    form = ConventionAdminForm
    list_display = [
        "name",
        "workspace",
    ]
    # readonly_fields = [
    #     "name",
    #     "workspace",
    # ]


class StructureAdminForm(forms.ModelForm):

    class Meta:
        model = models.Structure
        fields = "__all__"


class StructureAdmin(admin.ModelAdmin):
    form = StructureAdminForm
    list_display = [
        "dimension",
        "delimeter_after_dimension",
        "delimeter_before_dimension",
        "dimension_order",


    ]
    # readonly_fields = [
    #     "delimeter_after_dimension",
    #     "delimeter_before_dimension",
    #     "dimension_order",
    # ]


class StringAdminForm(forms.ModelForm):

    class Meta:
        model = models.String
        fields = "__all__"


class StringAdmin(admin.ModelAdmin):
    form = StringAdminForm
    list_display = [
        "parent",
        "workspace",
        "field",
    ]


admin.site.register(models.Dimension, DimensionAdmin)
admin.site.register(models.JunkDimension, JunkDimensionAdmin)
admin.site.register(models.Workspace, WorkspaceAdmin)
admin.site.register(models.Platform, PlatformAdmin)
admin.site.register(models.Field, FieldAdmin)
admin.site.register(models.Structure, StructureAdmin)
admin.site.register(models.Convention, ConventionAdmin)
admin.site.register(models.String, StringAdmin)
