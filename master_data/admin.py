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
# admin.site.register(models.Submission, SubmissionAdmin)  # DEPRECATED: Use Projects instead
admin.site.register(models.DimensionConstraint, DimensionConstraintAdmin)


# External String Admin (String Registry Validated Strings)
class ExternalStringAdmin(admin.ModelAdmin):
    list_display = [
        "external_platform_id",
        "value",
        "platform",
        "entity",
        "validation_status",
        "get_status_icon",
        "imported_status",
        "version",
        "created",
        "created_by",
    ]
    list_filter = [
        "validation_status",
        "platform",
        "entity",
        "batch__operation_type",
        "imported_at",
        "created",
    ]
    search_fields = [
        "external_platform_id",
        "value",
        "batch__file_name",
        "created_by__email",
    ]
    readonly_fields = [
        "workspace",
        "platform",
        "rule",
        "entity",
        "batch",
        "value",
        "external_platform_id",
        "external_parent_id",
        "validation_status",
        "validation_metadata",
        "imported_to_project_string",
        "imported_at",
        "created_by",
        "version",
        "superseded_by",
        "created",
        "last_updated",
    ]
    ordering = ["-created"]
    date_hierarchy = "created"

    def get_status_icon(self, obj):
        icons = {
            'valid': '✓ Valid',
            'invalid': '✗ Invalid',
            'warning': '⚠ Warning',
            'skipped': '⊘ Skipped'
        }
        return icons.get(obj.validation_status, '?')
    get_status_icon.short_description = 'Status'

    def imported_status(self, obj):
        if obj.imported_at:
            return '✓ Imported'
        elif obj.is_importable():
            return '⏳ Ready'
        else:
            return '✗ Cannot import'
    imported_status.short_description = 'Import Status'

    def has_add_permission(self, request):
        """Prevent manual creation."""
        return False


# External String Batch Admin (String Registry CSV Uploads)
class ExternalStringBatchAdmin(admin.ModelAdmin):
    list_display = [
        "file_name",
        "operation_type",
        "get_operation_icon",
        "uploaded_by",
        "workspace",
        "platform",
        "project",
        "status",
        "created",
        "uploaded_rows",
        "valid_count",
        "failed_count",
        "get_success_rate",
        "processing_time_seconds",
    ]
    list_filter = [
        "operation_type",
        "status",
        "workspace",
        "platform",
        "project",
        "uploaded_by",
        "created",
    ]
    search_fields = [
        "file_name",
        "uploaded_by__email",
        "uploaded_by__first_name",
        "uploaded_by__last_name",
        "project__name",
    ]
    readonly_fields = [
        "workspace",
        "uploaded_by",
        "file_name",
        "file_size_bytes",
        "operation_type",
        "platform",
        "rule",
        "project",
        "created",
        "last_updated",
        "total_rows",
        "uploaded_rows",
        "processed_rows",
        "skipped_rows",
        "created_count",
        "updated_count",
        "valid_count",
        "warnings_count",
        "failed_count",
        "linked_parents_count",
        "parent_conflicts_count",
        "parent_not_found_count",
        "processing_time_seconds",
        "status",
        "error_message",
        "get_success_rate",
        "get_failure_rate",
        "view_strings_link",
    ]
    ordering = ["-created"]
    date_hierarchy = "created"

    def get_operation_icon(self, obj):
        icons = {
            'validation': '🔍 Validation',
            'import': '📥 Import'
        }
        return icons.get(obj.operation_type, obj.operation_type)
    get_operation_icon.short_description = 'Operation'

    def get_success_rate(self, obj):
        """Display success rate as percentage."""
        return f"{obj.success_rate}%"
    get_success_rate.short_description = "Success Rate"

    def get_failure_rate(self, obj):
        """Display failure rate as percentage."""
        return f"{obj.failure_rate}%"
    get_failure_rate.short_description = "Failure Rate"

    def view_strings_link(self, obj):
        from django.utils.html import format_html
        url = f"/admin/master_data/externalstring/?batch__id__exact={obj.id}"
        return format_html('<a href="{}">View {} strings</a>', url, obj.uploaded_rows)
    view_strings_link.short_description = "Strings"

    def has_add_permission(self, request):
        """Prevent manual creation of batches."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup."""
        return True


admin.site.register(models.ExternalString, ExternalStringAdmin)
admin.site.register(models.ExternalStringBatch, ExternalStringBatchAdmin)


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


class StringAdmin(admin.ModelAdmin):
    list_display = [
        "project", "platform", "entity", "value", "string_uuid",
        "created_by", "created", "last_updated",
    ]
    list_filter = ["platform", "entity__entity_level", "created"]
    search_fields = ["value", "string_uuid", "project__name"]
    readonly_fields = ["string_uuid", "created", "last_updated"]


class StringDetailAdmin(admin.ModelAdmin):
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
admin.site.register(models.String, StringAdmin)
admin.site.register(models.StringDetail, StringDetailAdmin)
