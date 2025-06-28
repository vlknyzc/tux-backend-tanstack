from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import UserAccount, WorkspaceUser


class WorkspaceUserInline(admin.TabularInline):
    """Inline admin for workspace assignments within user admin"""
    model = WorkspaceUser
    extra = 0
    fields = ('workspace', 'role', 'is_active', 'created', 'updated')
    readonly_fields = ('created', 'updated')
    autocomplete_fields = ['workspace']


@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    """Admin configuration for UserAccount model"""

    # Display settings
    list_display = [
        'email', 'full_name', 'is_active', 'is_staff', 'is_superuser',
        'workspace_count', 'last_login'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser',
        'workspaceuser__role', 'workspaceuser__workspace'
    ]
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']

    # Form settings
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login',),
            'classes': ('collapse',)
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    # Readonly fields
    readonly_fields = ['last_login']

    # Inlines
    inlines = [WorkspaceUserInline]

    # Custom methods for list display
    def full_name(self, obj):
        """Display user's full name"""
        return obj.get_full_name()
    full_name.short_description = 'Full Name'

    def workspace_count(self, obj):
        """Display number of workspaces user has access to"""
        if obj.is_superuser:
            return format_html('<span style="color: green;">All (Superuser)</span>')
        count = obj.workspaces.filter(workspaceuser__is_active=True).count()
        return f"{count} workspace{'s' if count != 1 else ''}"
    workspace_count.short_description = 'Workspaces'

    # Actions
    actions = ['activate_users', 'deactivate_users',
               'make_staff', 'remove_staff']

    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated.')
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.')
    deactivate_users.short_description = "Deactivate selected users"

    def make_staff(self, request, queryset):
        """Make selected users staff"""
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'{updated} user(s) made staff.')
    make_staff.short_description = "Make selected users staff"

    def remove_staff(self, request, queryset):
        """Remove staff status from selected users"""
        updated = queryset.update(is_staff=False)
        self.message_user(request, f'{updated} user(s) removed from staff.')
    remove_staff.short_description = "Remove staff status from selected users"


@admin.register(WorkspaceUser)
class WorkspaceUserAdmin(admin.ModelAdmin):
    """Admin configuration for WorkspaceUser model"""

    # Display settings
    list_display = [
        'user_email', 'user_name', 'workspace_name', 'role',
        'is_active', 'created', 'updated'
    ]
    list_filter = [
        'role', 'is_active', 'created', 'workspace',
        'user__is_active', 'user__is_staff'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'workspace__name'
    ]
    ordering = ['-created']

    # Form settings
    fields = ('user', 'workspace', 'role', 'is_active')
    autocomplete_fields = ['user', 'workspace']

    # Custom methods for list display
    def user_email(self, obj):
        """Display user's email with link to user admin"""
        return format_html(
            '<a href="/admin/users/useraccount/{}/change/">{}</a>',
            obj.user.id, obj.user.email
        )
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def user_name(self, obj):
        """Display user's full name"""
        return obj.user.get_full_name()
    user_name.short_description = 'User Name'
    user_name.admin_order_field = 'user__first_name'

    def workspace_name(self, obj):
        """Display workspace name with link to workspace admin"""
        return format_html(
            '<a href="/admin/master_data/workspace/{}/change/">{}</a>',
            obj.workspace.id, obj.workspace.name
        )
    workspace_name.short_description = 'Workspace'
    workspace_name.admin_order_field = 'workspace__name'

    # Actions
    actions = ['activate_assignments', 'deactivate_assignments',
               'promote_to_admin', 'demote_to_user']

    def activate_assignments(self, request, queryset):
        """Activate selected workspace assignments"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, f'{updated} workspace assignment(s) activated.')
    activate_assignments.short_description = "Activate selected assignments"

    def deactivate_assignments(self, request, queryset):
        """Deactivate selected workspace assignments"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f'{updated} workspace assignment(s) deactivated.')
    deactivate_assignments.short_description = "Deactivate selected assignments"

    def promote_to_admin(self, request, queryset):
        """Promote selected users to admin role"""
        updated = queryset.update(role='admin')
        self.message_user(request, f'{updated} user(s) promoted to admin.')
    promote_to_admin.short_description = "Promote to admin role"

    def demote_to_user(self, request, queryset):
        """Demote selected users to user role"""
        updated = queryset.update(role='user')
        self.message_user(request, f'{updated} user(s) set to user role.')
    demote_to_user.short_description = "Set to user role"

    # Custom queryset for performance
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'workspace')


# Register models with admin site
admin.site.site_header = "TUX Backend Administration"
admin.site.site_title = "TUX Admin"
admin.site.index_title = "Welcome to TUX Backend Administration"
