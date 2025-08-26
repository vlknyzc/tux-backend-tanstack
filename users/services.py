"""
Email services for the TUX backend application.
Uses Amazon SES via boto3 for sending emails.
"""

import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)


class SESEmailService:
    """
    Service class for sending emails using Amazon SES with boto3.
    Provides both HTML and plain text email support with template rendering.
    """
    
    def __init__(self):
        """Initialize the SES client with configuration from Django settings."""
        try:
            self.ses_client = boto3.client(
                'ses',
                region_name=getattr(settings, 'AWS_SES_REGION_NAME', 'us-east-1'),
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            )
            self.from_email = getattr(settings, 'AWS_SES_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
            logger.info("SES Email Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SES client: {str(e)}")
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
        Send an email using Amazon SES.
        
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
            
            # Build the destination
            destination = {'ToAddresses': to_emails}
            if cc_emails:
                destination['CcAddresses'] = cc_emails
            if bcc_emails:
                destination['BccAddresses'] = bcc_emails
            
            # Build the message
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'}
            }
            
            # Add body content
            body = {}
            if html_content:
                body['Html'] = {'Data': html_content, 'Charset': 'UTF-8'}
            if text_content:
                body['Text'] = {'Data': text_content, 'Charset': 'UTF-8'}
            elif html_content:
                # Generate plain text from HTML if no text content provided
                body['Text'] = {'Data': strip_tags(html_content), 'Charset': 'UTF-8'}
            
            if not body:
                raise ValueError("Either html_content or text_content must be provided")
            
            message['Body'] = body
            
            # Send the email
            send_kwargs = {
                'Source': sender,
                'Destination': destination,
                'Message': message
            }
            
            if reply_to_emails:
                send_kwargs['ReplyToAddresses'] = reply_to_emails
            
            response = self.ses_client.send_email(**send_kwargs)
            
            logger.info(f"Email sent successfully. MessageId: {response['MessageId']}")
            return {
                'success': True,
                'message_id': response['MessageId'],
                'message': 'Email sent successfully'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"SES ClientError: {error_code} - {error_message}")
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message,
                'message': f'Failed to send email: {error_message}'
            }
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return {
                'success': False,
                'error_code': 'NoCredentials',
                'error_message': 'AWS credentials not found',
                'message': 'Failed to send email: AWS credentials not configured'
            }
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return {
                'success': False,
                'error_code': 'UnknownError',
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
    
    def verify_email_address(self, email_address: str) -> Dict[str, Any]:
        """
        Verify an email address with Amazon SES.
        
        Args:
            email_address: Email address to verify
            
        Returns:
            Dict containing verification status
        """
        try:
            response = self.ses_client.verify_email_identity(EmailAddress=email_address)
            logger.info(f"Verification email sent to {email_address}")
            return {
                'success': True,
                'message': f'Verification email sent to {email_address}'
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to verify email {email_address}: {error_code} - {error_message}")
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message,
                'message': f'Failed to verify email: {error_message}'
            }
    
    def get_send_quota(self) -> Dict[str, Any]:
        """
        Get the current SES send quota and statistics.
        
        Returns:
            Dict containing quota information
        """
        try:
            quota_response = self.ses_client.get_send_quota()
            stats_response = self.ses_client.get_send_statistics()
            
            return {
                'success': True,
                'max_24_hour_send': quota_response.get('Max24HourSend', 0),
                'max_send_rate': quota_response.get('MaxSendRate', 0),
                'sent_last_24_hours': quota_response.get('SentLast24Hours', 0),
                'send_data_points': stats_response.get('SendDataPoints', [])
            }
        except ClientError as e:
            logger.error(f"Failed to get send quota: {e}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def send_test_email(self, to_email: str) -> Dict[str, Any]:
        """
        Send a test email to verify SES configuration.
        
        Args:
            to_email: Email address to send test email to
            
        Returns:
            Dict containing success status and details
        """
        subject = "TUX Backend - SES Test Email"
        html_content = """
        <html>
        <head></head>
        <body>
            <h2>TUX Backend SES Test Email</h2>
            <p>This is a test email sent from the TUX Backend application using Amazon SES.</p>
            <p><strong>Configuration Details:</strong></p>
            <ul>
                <li>Service: Amazon SES</li>
                <li>Client: boto3</li>
                <li>Region: {region}</li>
                <li>From Email: {from_email}</li>
            </ul>
            <p>If you received this email, your SES configuration is working correctly!</p>
            <hr>
            <p><small>Sent from TUX Backend Email Service</small></p>
        </body>
        </html>
        """.format(
            region=getattr(settings, 'AWS_SES_REGION_NAME', 'us-east-1'),
            from_email=self.from_email
        )
        
        text_content = """
        TUX Backend - SES Test Email
        
        This is a test email sent from the TUX Backend application using Amazon SES.
        
        Configuration Details:
        - Service: Amazon SES
        - Client: boto3
        - Region: {region}
        - From Email: {from_email}
        
        If you received this email, your SES configuration is working correctly!
        
        ---
        Sent from TUX Backend Email Service
        """.format(
            region=getattr(settings, 'AWS_SES_REGION_NAME', 'us-east-1'),
            from_email=self.from_email
        )
        
        return self.send_email(
            to_emails=[to_email],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )


# Global instance for easy access
email_service = SESEmailService()


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
            subject = "You're invited to join TUX Backend"
        
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
    return email_service.send_test_email(to_email)
