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

        "name",
        "description",
        "type",
    ]


class DimensionValueAdminForm(forms.ModelForm):

    class Meta:
        model = models.DimensionValue
        fields = "__all__"


class DimensionValueAdmin(admin.ModelAdmin):
    form = DimensionValueAdminForm
    list_display = [
        # "dimension_value_code",
        "valid_from",
        "description",
        "value",
        "valid_until",
        "label",
        "utm",
    ]


class WorkspaceAdminForm(forms.ModelForm):

    class Meta:
        model = models.Workspace
        fields = "__all__"


class WorkspaceAdmin(admin.ModelAdmin):

    form = WorkspaceAdminForm
    list_display = [
        "name", "status", "slug", "created", "last_updated",
    ]
    search_fields = [
        "name", "slug",
    ]
    list_filter = [
        "status", "created",
    ]
    readonly_fields = [
        "slug", "created", "last_updated", "created_by",
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


class EntityAdminForm(forms.ModelForm):

    class Meta:
        model = models.Entity
        fields = "__all__"


class EntityAdmin(admin.ModelAdmin):
    form = EntityAdminForm
    list_display = [
        "name",
        "platform",
    ]


class RuleAdminForm(forms.ModelForm):

    class Meta:
        model = models.Rule
        fields = "__all__"


class RuleAdmin(admin.ModelAdmin):
    form = RuleAdminForm
    list_display = [
        "name",


    ]


class RuleDetailAdminForm(forms.ModelForm):

    class Meta:
        model = models.RuleDetail
        fields = "__all__"


class RuleDetailAdmin(admin.ModelAdmin):
    form = RuleDetailAdminForm
    list_display = [
        "rule",
        # "platform",
        "entity",
        "dimension",
    ]


class StringAdminForm(forms.ModelForm):

    class Meta:
        model = models.String
        fields = "__all__"


class StringAdmin(admin.ModelAdmin):
    form = StringAdminForm
    list_display = [
        "parent",
        # "workspace",

    ]


class StringDetailAdminForm(forms.ModelForm):

    class Meta:
        model = models.StringDetail
        fields = "__all__"


class StringDetailAdmin(admin.ModelAdmin):
    form = StringDetailAdminForm
    list_display = [
        "string",
        "dimension",
        "dimension_value",
        "dimension_value_freetext",
        # "rule",
    ]


class DimensionConstraintAdminForm(forms.ModelForm):

    class Meta:
        model = models.DimensionConstraint
        fields = "__all__"


class DimensionConstraintAdmin(admin.ModelAdmin):
    form = DimensionConstraintAdminForm
    list_display = [
        "dimension",
        "constraint_type",
        "value",
        "order",
        "is_active",
    ]
    list_filter = [
        "constraint_type",
        "is_active",
    ]
    search_fields = [
        "dimension__name",
        "error_message",
    ]
    ordering = ["dimension", "order"]


admin.site.register(models.Dimension, DimensionAdmin)
admin.site.register(models.DimensionValue, DimensionValueAdmin)
admin.site.register(models.Workspace, WorkspaceAdmin)
admin.site.register(models.Platform, PlatformAdmin)
admin.site.register(models.Entity, EntityAdmin)
admin.site.register(models.Rule, RuleAdmin)
admin.site.register(models.RuleDetail, RuleDetailAdmin)
admin.site.register(models.String, StringAdmin)
admin.site.register(models.StringDetail, StringDetailAdmin)
# admin.site.register(models.Submission, SubmissionAdmin)  # DEPRECATED: Use Projects instead
admin.site.register(models.DimensionConstraint, DimensionConstraintAdmin)


# Project models
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name", "slug", "workspace", "status", "approval_status",
        "owner", "created", "last_updated",
    ]
    list_filter = ["status", "approval_status", "created"]
    search_fields = ["name", "slug", "description"]
    readonly_fields = ["slug", "created", "last_updated"]
    filter_horizontal = []


class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ["project", "user", "role", "created"]
    list_filter = ["role", "created"]
    search_fields = ["project__name", "user__email", "user__first_name", "user__last_name"]


class ProjectActivityAdmin(admin.ModelAdmin):
    list_display = ["project", "type", "user", "created"]
    list_filter = ["type", "created"]
    search_fields = ["project__name", "description"]
    readonly_fields = ["created"]


class ApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = ["project", "action", "user", "timestamp"]
    list_filter = ["action", "timestamp"]
    search_fields = ["comment"]
    readonly_fields = ["timestamp"]


class ProjectStringAdmin(admin.ModelAdmin):
    list_display = [
        "project", "platform", "entity", "value", "string_uuid",
        "created_by", "created", "last_updated",
    ]
    list_filter = ["platform", "entity__entity_level", "created"]
    search_fields = ["value", "string_uuid", "project__name"]
    readonly_fields = ["string_uuid", "created", "last_updated"]


class ProjectStringDetailAdmin(admin.ModelAdmin):
    list_display = [
        "string", "dimension", "dimension_value", "dimension_value_freetext",
        "is_inherited",
    ]
    list_filter = ["is_inherited", "dimension"]
    search_fields = ["dimension__name", "dimension_value_freetext"]


admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.ProjectMember, ProjectMemberAdmin)
admin.site.register(models.ProjectActivity, ProjectActivityAdmin)
admin.site.register(models.ApprovalHistory, ApprovalHistoryAdmin)
admin.site.register(models.ProjectString, ProjectStringAdmin)
admin.site.register(models.ProjectStringDetail, ProjectStringDetailAdmin)
