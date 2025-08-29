"""
Management command to create workspaces
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from master_data.models import Workspace
from users.models import WorkspaceUser

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a new workspace'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Workspace name')
        parser.add_argument(
            '--slug',
            type=str,
            help='Workspace slug (auto-generated from name if not provided)'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            help='Email of user to assign as workspace admin'
        )
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Create admin user if they don\'t exist (requires --admin-email)'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip creation if workspace already exists (for deployment scripts)'
        )

    def handle(self, *args, **options):
        name = options['name']
        slug = options.get('slug')
        admin_email = options.get('admin_email')
        create_admin = options['create_admin']
        skip_existing = options['skip_existing']

        # Validate inputs
        if create_admin and not admin_email:
            raise CommandError(
                '--admin-email is required when using --create-admin')

        try:
            # Check if workspace already exists
            if slug:
                existing = Workspace.objects.filter(slug=slug).first()
                if existing:
                    if skip_existing:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Workspace with slug "{slug}" already exists. Skipping creation.'
                            )
                        )
                        return
                    else:
                        raise CommandError(
                            f'Workspace with slug "{slug}" already exists')

            existing = Workspace.objects.filter(name=name).first()
            if existing:
                if skip_existing:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Workspace with name "{name}" already exists. Skipping creation.'
                        )
                    )
                    return
                else:
                    raise CommandError(
                        f'Workspace with name "{name}" already exists')

            # Create workspace
            workspace_data = {'name': name}
            if slug:
                workspace_data['slug'] = slug

            workspace = Workspace.objects.create(**workspace_data)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created workspace: {workspace.name} (slug: {workspace.slug})'
                )
            )

            # Handle admin user assignment
            if admin_email:
                admin_user = None

                try:
                    admin_user = User.objects.get(email=admin_email)
                    self.stdout.write(
                        f'Found existing admin user: {admin_user.get_full_name()}')
                except User.DoesNotExist:
                    if create_admin:
                        # Create admin user
                        admin_user = User.objects.create_user(
                            email=admin_email,
                            first_name='Admin',
                            last_name='User',
                            password='changeme123!'  # Temporary password
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created admin user: {admin_user.email} (password: changeme123!)'
                            )
                        )
                        self.stdout.write(
                            self.style.WARNING(
                                'Please change the admin password immediately!'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Admin user {admin_email} does not exist. '
                                f'Use --create-admin to create them.'
                            )
                        )

                if admin_user:
                    # Assign admin to workspace
                    WorkspaceUser.objects.create(
                        user=admin_user,
                        workspace=workspace,
                        role='admin',
                        is_active=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Assigned {admin_user.email} as admin of workspace {workspace.name}'
                        )
                    )

            # Show workspace details
            self.stdout.write('\nWorkspace Details:')
            self.stdout.write(f'  Name: {workspace.name}')
            self.stdout.write(f'  Slug: {workspace.slug}')
            self.stdout.write(f'  Status: {workspace.status}')
            self.stdout.write(f'  Created: {workspace.created}')

            if admin_email:
                self.stdout.write(f'\nAccess URLs:')
                self.stdout.write(
                    f'  Subdomain: {workspace.slug}.yourdomain.com')
                self.stdout.write(f'  Admin: {admin_email}')

        except Exception as e:
            raise CommandError(f'Failed to create workspace: {str(e)}')
