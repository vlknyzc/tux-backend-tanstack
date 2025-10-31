"""
Management command to create initial superuser non-interactively
Useful for Railway deployment where interactive input is not available
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create initial superuser non-interactively (for deployment)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default=os.environ.get('SUPERUSER_EMAIL', 'admin@example.com'),
            help='Superuser email address'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=os.environ.get('SUPERUSER_PASSWORD', 'changeme123!'),
            help='Superuser password'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default=os.environ.get('SUPERUSER_FIRST_NAME', 'Admin'),
            help='Superuser first name'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default=os.environ.get('SUPERUSER_LAST_NAME', 'User'),
            help='Superuser last name'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip if superuser with this email already exists'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        skip_existing = options['skip_existing']

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            if skip_existing:
                self.stdout.write(
                    self.style.WARNING(
                        f'Superuser with email "{email}" already exists. Skipping.'
                    )
                )
                # Show existing superusers
                self.stdout.write('\nExisting superusers:')
                for user in User.objects.filter(is_superuser=True):
                    self.stdout.write(
                        f'  ✓ {user.email} ({user.get_full_name()})'
                    )
                return
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Superuser with email "{email}" already exists!'
                    )
                )
                return

        try:
            # Create superuser
            superuser = User.objects.create_superuser(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Successfully created superuser!'
                )
            )
            self.stdout.write(f'   Email: {superuser.email}')
            self.stdout.write(f'   Name: {superuser.get_full_name()}')
            self.stdout.write(f'   Password: {"*" * len(password)}')
            
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  IMPORTANT: Change the password immediately after first login!'
                )
            )
            
            self.stdout.write(f'\n🔗 Access admin at: https://your-app.railway.app/admin/')
            self.stdout.write(f'📚 API docs at: https://your-app.railway.app/api/schema/swagger-ui/')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating superuser: {str(e)}')
            )
            raise

