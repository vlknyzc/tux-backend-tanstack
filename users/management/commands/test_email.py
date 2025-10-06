"""
Django management command to test the Resend email service.
Usage: python manage.py test_email your-email@example.com
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from users.services import get_email_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send a test email using the Resend email service'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send the test email to'
        )
        parser.add_argument(
            '--template',
            action='store_true',
            help='Use the HTML template for the test email'
        )

    def handle(self, *args, **options):
        email_address = options['email']

        self.stdout.write(
            self.style.HTTP_INFO(f"Testing Resend email service with {email_address}")
        )

        try:
            # Send test email
            self.stdout.write(f"\n📤 Sending test email to {email_address}...")

            email_service = get_email_service()
            if options['template']:
                # Use template-based email
                context = {
                    'from_email': email_service.from_email,
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                }

                result = email_service.send_template_email(
                    to_emails=[email_address],
                    subject="tuxonomy.com - Resend Template Test Email",
                    template_name='test_email',
                    context=context
                )
            else:
                # Use simple email method
                result = email_service.send_test_email(email_address)

            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {result['message']}")
                )
                self.stdout.write(f"   Message ID: {result['message_id']}")
                self.stdout.write(f"   Recipient: {email_address}")
                self.stdout.write(f"   From: {email_service.from_email}")

                self.stdout.write("\n🎉 Test completed successfully!")
                self.stdout.write("Check your email inbox (and spam folder) for the test message.")

            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ {result['message']}")
                )
                if 'error_code' in result:
                    self.stdout.write(f"   Error Code: {result['error_code']}")
                if 'error_message' in result:
                    self.stdout.write(f"   Error Details: {result['error_message']}")

                # Provide troubleshooting suggestions
                self.stdout.write("\n🔧 Troubleshooting suggestions:")
                self.stdout.write("1. Check that your Resend API key is properly configured")
                self.stdout.write("2. Verify that your sender email domain is verified in Resend")
                self.stdout.write("3. Check your Resend dashboard for any issues")

        except Exception as e:
            logger.exception(f"Unexpected error in test_email command: {str(e)}")
            raise CommandError(f"Failed to test email service: {str(e)}")

        self.stdout.write("\n" + "="*60)
        self.stdout.write("tuxonomy.com Email Service Test Complete")
        self.stdout.write("="*60)
