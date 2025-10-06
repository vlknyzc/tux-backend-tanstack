"""
Email services for the TUX backend application.
Uses Resend for sending emails.
"""

import logging
import resend
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ResendEmailService:
    """
    Service class for sending emails using Resend.
    Provides both HTML and plain text email support with template rendering.
    """

    def __init__(self):
        """Initialize the Resend client with configuration from Django settings."""
        try:
            api_key = getattr(settings, 'RESEND_API_KEY', None)
            if api_key:
                resend.api_key = api_key
            self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@tuxonomy.com')
            logger.info("Resend Email Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Resend client: {str(e)}")
            raise

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str = None,
        text_content: str = None,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        reply_to_emails: List[str] = None,
        from_email: str = None
    ) -> Dict[str, Any]:
        """
        Send an email using Resend.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            html_content: HTML content of the email
            text_content: Plain text content of the email
            cc_emails: List of CC email addresses (optional)
            bcc_emails: List of BCC email addresses (optional)
            reply_to_emails: List of reply-to email addresses (optional)
            from_email: Sender email address (optional, uses default if not provided)

        Returns:
            Dict containing success status and message ID or error details
        """
        try:
            # Use provided from_email or default
            sender = from_email or self.from_email

            if not sender:
                raise ValueError("No sender email address provided and no default configured")

            if not resend.api_key:
                raise ValueError("Resend API key not configured")

            # Build the email parameters
            params = {
                "from": sender,
                "to": to_emails,
                "subject": subject,
            }

            # Add HTML content
            if html_content:
                params["html"] = html_content

            # Add text content or generate from HTML
            if text_content:
                params["text"] = text_content
            elif html_content:
                params["text"] = strip_tags(html_content)
            else:
                raise ValueError("Either html_content or text_content must be provided")

            # Add optional fields
            if cc_emails:
                params["cc"] = cc_emails
            if bcc_emails:
                params["bcc"] = bcc_emails
            if reply_to_emails:
                params["reply_to"] = reply_to_emails

            # Send the email
            response = resend.Emails.send(params)

            # Resend returns a dict with 'id' on success
            if isinstance(response, dict) and 'id' in response:
                logger.info(f"Email sent successfully. Message ID: {response['id']}")
                return {
                    'success': True,
                    'message_id': response['id'],
                    'message': 'Email sent successfully'
                }
            else:
                logger.error(f"Unexpected response from Resend: {response}")
                return {
                    'success': False,
                    'error_code': 'UnexpectedResponse',
                    'error_message': str(response),
                    'message': f'Unexpected response from Resend: {response}'
                }

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                'success': False,
                'error_code': 'SendError',
                'error_message': str(e),
                'message': f'Failed to send email: {str(e)}'
            }

    def send_template_email(
        self,
        to_emails: List[str],
        subject: str,
        template_name: str,
        context: Dict[str, Any] = None,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        reply_to_emails: List[str] = None,
        from_email: str = None
    ) -> Dict[str, Any]:
        """
        Send an email using Django templates.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            template_name: Name of the template file (without .html extension)
            context: Template context variables
            cc_emails: List of CC email addresses (optional)
            bcc_emails: List of BCC email addresses (optional)
            reply_to_emails: List of reply-to email addresses (optional)
            from_email: Sender email address (optional)

        Returns:
            Dict containing success status and message ID or error details
        """
        try:
            context = context or {}

            # Render HTML template
            html_template_path = f'emails/{template_name}.html'
            html_content = render_to_string(html_template_path, context)

            # Try to render text template (optional)
            text_content = None
            try:
                text_template_path = f'emails/{template_name}.txt'
                text_content = render_to_string(text_template_path, context)
            except Exception:
                # Text template is optional, we'll generate from HTML
                pass

            return self.send_email(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                reply_to_emails=reply_to_emails,
                from_email=from_email
            )

        except Exception as e:
            logger.error(f"Error rendering email template '{template_name}': {str(e)}")
            return {
                'success': False,
                'error_code': 'TemplateError',
                'error_message': str(e),
                'message': f'Failed to render email template: {str(e)}'
            }

    def send_test_email(self, to_email: str) -> Dict[str, Any]:
        """
        Send a test email to verify Resend configuration.

        Args:
            to_email: Email address to send test email to

        Returns:
            Dict containing success status and details
        """
        subject = "TUX Backend - Resend Test Email"
        html_content = """
        <html>
        <head></head>
        <body>
            <h2>TUX Backend Resend Test Email</h2>
            <p>This is a test email sent from the TUX Backend application using Resend.</p>
            <p><strong>Configuration Details:</strong></p>
            <ul>
                <li>Service: Resend</li>
                <li>From Email: {from_email}</li>
            </ul>
            <p>If you received this email, your Resend configuration is working correctly!</p>
            <hr>
            <p><small>Sent from TUX Backend Email Service</small></p>
        </body>
        </html>
        """.format(from_email=self.from_email)

        text_content = """
        TUX Backend - Resend Test Email

        This is a test email sent from the TUX Backend application using Resend.

        Configuration Details:
        - Service: Resend
        - From Email: {from_email}

        If you received this email, your Resend configuration is working correctly!

        ---
        Sent from TUX Backend Email Service
        """.format(from_email=self.from_email)

        return self.send_email(
            to_emails=[to_email],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )


def get_email_service():
    """Get a singleton instance of the email service."""
    if not hasattr(get_email_service, '_instance'):
        get_email_service._instance = ResendEmailService()
    return get_email_service._instance


def send_invitation_email(invitation) -> Dict[str, Any]:
    """
    Send an invitation email for user registration.

    Args:
        invitation: Invitation model instance

    Returns:
        Dict containing success status and details
    """
    try:
        # Get frontend URL from settings or use a default
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        invitation_url = f"{frontend_url}/accept-invitation/{invitation.token}"

        context = {
            'invitation': invitation,
            'invitation_url': invitation_url,
        }

        # Create a dynamic subject based on workspace
        if invitation.workspace:
            subject = f"You're invited to join {invitation.workspace.name}"
        else:
            subject = "You're invited to join tuxonomy.com"
        # Use the getter function instead of global instance
        email_service = get_email_service()
        result = email_service.send_template_email(
            to_emails=[invitation.email],
            subject=subject,
            template_name='invitation',
            context=context
        )

        # Log the attempt
        if result['success']:
            logger.info(f"Invitation email sent to {invitation.email} for invitation {invitation.token}")
        else:
            logger.error(f"Failed to send invitation email to {invitation.email}: {result['message']}")

        return result

    except Exception as e:
        logger.error(f"Error sending invitation email: {str(e)}")
        return {
            'success': False,
            'error_message': str(e),
            'message': f'Failed to send invitation email: {str(e)}'
        }


def send_test_email(to_email: str) -> Dict[str, Any]:
    """
    Convenience function to send a test email.

    Args:
        to_email: Email address to send test email to

    Returns:
        Dict containing success status and details
    """
    # Use the getter function instead of global instance
    email_service = get_email_service()
    return email_service.send_test_email(to_email)
