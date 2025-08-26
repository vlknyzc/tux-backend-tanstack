"""
Django management command to test the SES email service.
Usage: python manage.py test_email vlknyzc@gmail.com
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from users.services import email_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send a test email using the SES email service'

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
        parser.add_argument(
            '--check-quota',
            action='store_true',
            help='Check SES send quota and statistics'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Verify the email address with SES'
        )

    def handle(self, *args, **options):
        email_address = options['email']
        
        self.stdout.write(
            self.style.HTTP_INFO(f"Testing SES email service with {email_address}")
        )
        
        try:
            # Check quota if requested
            if options['check_quota']:
                self.stdout.write("\n📊 Checking SES quota and statistics...")
                quota_result = email_service.get_send_quota()
                if quota_result['success']:
                    self.stdout.write(self.style.SUCCESS("✅ Quota information retrieved:"))
                    self.stdout.write(f"   Max 24-hour send: {quota_result['max_24_hour_send']}")
                    self.stdout.write(f"   Max send rate: {quota_result['max_send_rate']}")
                    self.stdout.write(f"   Sent last 24 hours: {quota_result['sent_last_24_hours']}")
                else:
                    self.stdout.write(
                        self.style.WARNING(f"❌ Failed to get quota: {quota_result['error_message']}")
                    )
            
            # Verify email if requested
            if options['verify']:
                self.stdout.write(f"\n📧 Verifying email address {email_address}...")
                verify_result = email_service.verify_email_address(email_address)
                if verify_result['success']:
                    self.stdout.write(self.style.SUCCESS(f"✅ {verify_result['message']}"))
                else:
                    self.stdout.write(
                        self.style.WARNING(f"❌ {verify_result['message']}")
                    )
            
            # Send test email
            self.stdout.write(f"\n📤 Sending test email to {email_address}...")
            
            if options['template']:
                # Use template-based email
                context = {
                    'region': getattr(email_service.ses_client._client_config, 'region_name', 'us-east-1'),
                    'from_email': email_service.from_email,
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                }
                
                result = email_service.send_template_email(
                    to_emails=[email_address],
                    subject="TUX Backend - SES Template Test Email",
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
                self.stdout.write("1. Check that your AWS credentials are properly configured")
                self.stdout.write("2. Verify that your SES service is active in the correct region")
                self.stdout.write("3. Ensure your sender email is verified in SES")
                self.stdout.write("4. Check if you're in SES sandbox mode (limits recipients)")
                
        except Exception as e:
            logger.exception(f"Unexpected error in test_email command: {str(e)}")
            raise CommandError(f"Failed to test email service: {str(e)}")
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("TUX Backend Email Service Test Complete")
        self.stdout.write("="*60)
