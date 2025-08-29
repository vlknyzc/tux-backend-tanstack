"""
Email-related API views for the TUX backend application.
Provides endpoints for testing and managing email functionality.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
import logging
from typing import Dict, Any

from .services import get_email_service

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def send_test_email(request):
    """
    Send a test email using the SES service.
    Only admin users can send test emails.
    
    POST /api/v1/email/test/
    {
        "email": "test@example.com",
        "use_template": true
    }
    """
    try:
        email_address = request.data.get('email')
        use_template = request.data.get('use_template', False)
        
        if not email_address:
            return Response(
                {'error': 'Email address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send test email
        if use_template:
            context = {
                'region': getattr(get_email_service().ses_client._client_config, 'region_name', 'us-east-1'),
                'from_email': get_email_service().from_email,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            result = get_email_service().send_template_email(
                to_emails=[email_address],
                subject="TUX Backend - API Test Email",
                template_name='test_email',
                context=context
            )
        else:
            result = get_email_service().send_test_email(email_address)
        
        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'message_id': result['message_id'],
                'recipient': email_address,
                'from_email': get_email_service().from_email,
                'template_used': use_template
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result['message'],
                'error_code': result.get('error_code'),
                'error_details': result.get('error_message')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in send_test_email API: {str(e)}")
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_email_quota(request):
    """
    Get SES quota and statistics.
    Only admin users can access quota information.
    
    GET /api/v1/email/quota/
    """
    try:
        quota_result = get_email_service().get_send_quota()
        
        if quota_result['success']:
            return Response({
                'success': True,
                'quota': {
                    'max_24_hour_send': quota_result['max_24_hour_send'],
                    'max_send_rate': quota_result['max_send_rate'],
                    'sent_last_24_hours': quota_result['sent_last_24_hours'],
                    'send_data_points': quota_result['send_data_points']
                },
                'region': getattr(get_email_service().ses_client._client_config, 'region_name', 'us-east-1'),
                'from_email': get_email_service().from_email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': quota_result['error_message']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in get_email_quota API: {str(e)}")
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def verify_email(request):
    """
    Verify an email address with SES.
    Only admin users can verify email addresses.
    
    POST /api/v1/email/verify/
    {
        "email": "test@example.com"
    }
    """
    try:
        email_address = request.data.get('email')
        
        if not email_address:
            return Response(
                {'error': 'Email address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = get_email_service().verify_email_address(email_address)
        
        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'email': email_address
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result['message'],
                'error_code': result.get('error_code'),
                'error_details': result.get('error_message')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in verify_email API: {str(e)}")
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_custom_email(request):
    """
    Send a custom email (for admin users only).
    Regular users cannot send arbitrary emails.
    
    POST /api/v1/email/send/
    {
        "to_emails": ["user@example.com"],
        "subject": "Custom Subject",
        "html_content": "<h1>HTML Content</h1>",
        "text_content": "Plain text content",
        "cc_emails": ["cc@example.com"],  // optional
        "bcc_emails": ["bcc@example.com"]  // optional
    }
    """
    # Only allow admin users to send custom emails
    if not request.user.is_staff:
        return Response(
            {'error': 'Only admin users can send custom emails'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        to_emails = request.data.get('to_emails', [])
        subject = request.data.get('subject')
        html_content = request.data.get('html_content')
        text_content = request.data.get('text_content')
        cc_emails = request.data.get('cc_emails', [])
        bcc_emails = request.data.get('bcc_emails', [])
        
        if not to_emails:
            return Response(
                {'error': 'At least one recipient email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not subject:
            return Response(
                {'error': 'Subject is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not html_content and not text_content:
            return Response(
                {'error': 'Either HTML content or text content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = get_email_service().send_email(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            cc_emails=cc_emails if cc_emails else None,
            bcc_emails=bcc_emails if bcc_emails else None
        )
        
        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'message_id': result['message_id'],
                'recipients': to_emails,
                'cc_recipients': cc_emails,
                'bcc_recipients': bcc_emails,
                'from_email': get_email_service().from_email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result['message'],
                'error_code': result.get('error_code'),
                'error_details': result.get('error_message')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in send_custom_email API: {str(e)}")
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
