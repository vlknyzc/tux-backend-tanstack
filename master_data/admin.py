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
        "dimension_value_code",
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
        "platform_field",
    ]
    # readonly_fields = [
    #     "platform_type",
    #     "name",
    #     "platform_field",
    # ]


class RuleAdminForm(forms.ModelForm):

    class Meta:
        model = models.Rule
        fields = "__all__"


class RuleAdmin(admin.ModelAdmin):
    form = RuleAdminForm
    list_display = [
        "valid_from",
        "valid_until",
        "name",
        "workspace",

    ]
    # readonly_fields = [
    #     "valid_from",
    #     "valid_until",
    #     "name",
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
        "rule"
    ]
    # readonly_fields = [
    #     "delimeter_after_dimension",
    #     "delimeter_before_dimension",
    #     "dimension_order",
    # ]


admin.site.register(models.Dimension, DimensionAdmin)
admin.site.register(models.JunkDimension, JunkDimensionAdmin)
admin.site.register(models.Workspace, WorkspaceAdmin)
admin.site.register(models.Platform, PlatformAdmin)
admin.site.register(models.Rule, RuleAdmin)
admin.site.register(models.Structure, StructureAdmin)
