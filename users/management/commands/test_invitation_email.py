"""
Django management command to test the invitation email flow.
Usage: python manage.py test_invitation_email vlknyzc@gmail.com --workspace-name "Test Workspace"
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import uuid

from users.models import Invitation, WorkspaceUser
from users.services import send_invitation_email
from master_data.models import Workspace

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the invitation email flow by creating a test invitation and sending the email'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send the invitation to'
        )
        parser.add_argument(
            '--workspace-name',
            type=str,
            default='Test Workspace',
            help='Name of the workspace for the test invitation'
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['admin', 'user', 'viewer'],
            default='user',
            help='Role to assign in the invitation'
        )
        parser.add_argument(
            '--create-workspace',
            action='store_true',
            help='Create a test workspace if it doesn\'t exist'
        )
        parser.add_argument(
            '--invitor-email',
            type=str,
            help='Email of the user sending the invitation (will create if doesn\'t exist)'
        )
        parser.add_argument(
            '--no-send',
            action='store_true',
            help='Create the invitation but don\'t send the email (for testing template only)'
        )

    def handle(self, *args, **options):
        email_address = options['email']
        workspace_name = options['workspace_name']
        role = options['role']
        create_workspace = options['create_workspace']
        invitor_email = options['invitor_email']
        no_send = options['no_send']
        
        self.stdout.write(
            self.style.HTTP_INFO(f"🧪 Testing invitation email flow for {email_address}")
        )
        
        try:
            # Create or get invitor user
            if invitor_email:
                invitor, created = User.objects.get_or_create(
                    email=invitor_email,
                    defaults={
                        'is_active': True,
                        'is_staff': False,
                        'first_name': 'Test',
                        'last_name': 'Invitor'
                    }
                )
                if created:
                    invitor.set_password('testpassword123')
                    invitor.save()
                    self.stdout.write(f"✅ Created test invitor user: {invitor_email}")
                else:
                    self.stdout.write(f"ℹ️  Using existing invitor user: {invitor_email}")
            else:
                # Use superuser or create a test user
                invitor = User.objects.filter(is_superuser=True).first()
                if not invitor:
                    invitor = User.objects.create_user(
                        email='test.admin@example.com',
                        password='testpassword123',
                        first_name='Test',
                        last_name='Admin',
                        is_staff=True,
                        is_superuser=True
                    )
                    self.stdout.write("✅ Created test admin user")
                else:
                    self.stdout.write(f"ℹ️  Using existing admin user: {invitor.email}")
            
            # Create or get workspace
            workspace = None
            if workspace_name != 'None':
                if create_workspace:
                    workspace, created = Workspace.objects.get_or_create(
                        name=workspace_name,
                        defaults={
                            'slug': workspace_name.lower().replace(' ', '-'),
                            'status': 'active'
                        }
                    )
                    if created:
                        self.stdout.write(f"✅ Created test workspace: {workspace_name}")
                    else:
                        self.stdout.write(f"ℹ️  Using existing workspace: {workspace_name}")
                else:
                    workspace = Workspace.objects.filter(name=workspace_name).first()
                    if not workspace:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Workspace '{workspace_name}' not found. Use --create-workspace to create it.")
                        )
                        workspace = None
            
            # Check if invitation already exists
            existing_invitation = Invitation.objects.filter(
                email=email_address,
                workspace=workspace,
                status='pending'
            ).first()
            
            if existing_invitation and existing_invitation.is_valid:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Valid invitation already exists for {email_address}")
                )
                invitation = existing_invitation
            else:
                # Create test invitation
                invitation = Invitation.objects.create(
                    email=email_address,
                    invitor=invitor,
                    workspace=workspace,
                    role=role,
                    expires_at=timezone.now() + timedelta(days=7)
                )
                
                self.stdout.write(f"✅ Created test invitation:")
                self.stdout.write(f"   Token: {invitation.token}")
                self.stdout.write(f"   Email: {invitation.email}")
                self.stdout.write(f"   Invitor: {invitation.invitor.email}")
                self.stdout.write(f"   Workspace: {invitation.workspace.name if invitation.workspace else 'None'}")
                self.stdout.write(f"   Role: {invitation.get_role_display()}")
                self.stdout.write(f"   Expires: {invitation.expires_at}")
            
            if no_send:
                self.stdout.write(
                    self.style.SUCCESS("✅ Invitation created successfully (email not sent due to --no-send flag)")
                )
                return
            
            # Send invitation email
            self.stdout.write(f"\n📤 Sending invitation email...")
            
            result = send_invitation_email(invitation)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {result['message']}")
                )
                self.stdout.write(f"   Message ID: {result['message_id']}")
                self.stdout.write(f"   Recipient: {invitation.email}")
                self.stdout.write(f"   Subject: You're invited to join {invitation.workspace.name if invitation.workspace else 'tuxonomy.com'}")
                
                # Show invitation URL for testing
                frontend_url = 'http://localhost:3000'  # Default frontend URL
                invitation_url = f"{frontend_url}/register?token={invitation.token}"
                self.stdout.write(f"\n🔗 Invitation URL (for testing):")
                self.stdout.write(f"   {invitation_url}")
                
                self.stdout.write("\n🎉 Test completed successfully!")
                self.stdout.write("Check your email inbox (and spam folder) for the invitation message.")
                
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ {result['message']}")
                )
                if 'error_code' in result:
                    self.stdout.write(f"   Error Code: {result['error_code']}")
                if 'error_message' in result:
                    self.stdout.write(f"   Error Details: {result['error_message']}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Unexpected error: {str(e)}")
            )
            raise CommandError(f"Failed to test invitation email: {str(e)}")
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("tuxonomy.com Invitation Email Test Complete")
        self.stdout.write("="*70)
