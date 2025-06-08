"""
Management command to assign users to workspaces
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from master_data.models import Workspace
from users.models import WorkspaceUser

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign a user to a workspace with a specific role'

    def add_arguments(self, parser):
        parser.add_argument('user_email', type=str, help='User email address')
        parser.add_argument('workspace_slug', type=str, help='Workspace slug')
        parser.add_argument(
            '--role',
            type=str,
            choices=['admin', 'user', 'viewer'],
            default='user',
            help='User role in the workspace (default: user)'
        )
        parser.add_argument(
            '--activate',
            action='store_true',
            help='Activate the workspace assignment if it exists but is inactive'
        )

    def handle(self, *args, **options):
        user_email = options['user_email']
        workspace_slug = options['workspace_slug']
        role = options['role']
        activate = options['activate']

        try:
            # Get user
            user = User.objects.get(email=user_email)
            self.stdout.write(
                f'Found user: {user.get_full_name()} ({user.email})')
        except User.DoesNotExist:
            raise CommandError(
                f'User with email "{user_email}" does not exist')

        try:
            # Get workspace
            workspace = Workspace.objects.get(slug=workspace_slug)
            self.stdout.write(f'Found workspace: {workspace.name}')
        except Workspace.DoesNotExist:
            raise CommandError(
                f'Workspace with slug "{workspace_slug}" does not exist')

        # Check if assignment already exists
        try:
            workspace_user = WorkspaceUser.objects.get(
                user=user, workspace=workspace)

            if workspace_user.is_active:
                self.stdout.write(
                    self.style.WARNING(
                        f'User {user.email} is already assigned to workspace {workspace.name} '
                        f'with role "{workspace_user.role}"'
                    )
                )
                return
            elif activate:
                workspace_user.is_active = True
                workspace_user.role = role
                workspace_user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Activated and updated assignment: {user.email} -> {workspace.name} '
                        f'with role "{role}"'
                    )
                )
                return
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'User {user.email} has an inactive assignment to workspace {workspace.name}. '
                        f'Use --activate to reactivate it.'
                    )
                )
                return

        except WorkspaceUser.DoesNotExist:
            # Create new assignment
            workspace_user = WorkspaceUser.objects.create(
                user=user,
                workspace=workspace,
                role=role,
                is_active=True
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully assigned {user.email} to workspace {workspace.name} '
                    f'with role "{role}"'
                )
            )

        # Show user's current workspace assignments
        self.stdout.write('\nUser\'s current workspace assignments:')
        assignments = WorkspaceUser.objects.filter(user=user, is_active=True)
        for assignment in assignments:
            status = "✓ Active" if assignment.is_active else "✗ Inactive"
            self.stdout.write(
                f'  - {assignment.workspace.name} ({assignment.role}) {status}')
