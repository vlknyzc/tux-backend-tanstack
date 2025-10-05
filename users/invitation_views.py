from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from datetime import timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view
import logging

from .models import Invitation, UserAccount
from .serializers import (
    InvitationCreateSerializer,
    InvitationSerializer,
    InvitationListSerializer,
    InvitationValidationSerializer,
    RegisterViaInvitationSerializer,
    InvitationResendSerializer,
    UserSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List invitations",
        description="Get list of invitations. Admins can see all, users see only their sent invitations.",
        tags=["Invitations"]
    ),
    create=extend_schema(
        summary="Create invitation",
        description="Create a new invitation for a user to join a workspace.",
        tags=["Invitations"]
    ),
    retrieve=extend_schema(
        summary="Get invitation details",
        description="Get detailed information about a specific invitation.",
        tags=["Invitations"]
    ),
    destroy=extend_schema(
        summary="Revoke invitation",
        description="Revoke an invitation (mark as revoked).",
        tags=["Invitations"]
    ),
)
class InvitationViewSet(ModelViewSet):
    """
    ViewSet for managing invitations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return InvitationCreateSerializer
        elif self.action == 'list':
            return InvitationListSerializer
        elif self.action == 'resend':
            return InvitationResendSerializer
        return InvitationSerializer
    
    def get_queryset(self):
        """Filter invitations based on user permissions"""
        user = self.request.user
        
        if user.is_superuser:
            # Superusers can see all invitations
            queryset = Invitation.objects.all()
        else:
            # Regular users can only see invitations they sent
            queryset = Invitation.objects.filter(invitor=user)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by workspace if provided
        workspace_filter = self.request.query_params.get('workspace')
        if workspace_filter:
            queryset = queryset.filter(workspace_id=workspace_filter)
        
        return queryset.select_related('invitor', 'workspace', 'used_by')
    
    def perform_create(self, serializer):
        """Create invitation with current user as invitor"""
        invitation = serializer.save(invitor=self.request.user)

        # Send invitation email
        self._send_invitation_email(invitation)
    
    def destroy(self, request, *args, **kwargs):
        """Revoke invitation instead of deleting"""
        invitation = self.get_object()
        
        # Check if user can revoke this invitation
        if not (request.user.is_superuser or invitation.invitor == request.user):
            return Response(
                {"error": "You don't have permission to revoke this invitation"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if invitation.status != 'pending':
            return Response(
                {"error": f"Cannot revoke invitation with status '{invitation.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.mark_as_revoked()
        
        return Response(
            {"message": "Invitation revoked successfully"},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="Resend invitation",
        description="Resend an invitation by extending its expiration date.",
        tags=["Invitations"]
    )
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend invitation by extending expiration"""
        invitation = self.get_object()
        
        # Check permissions
        if not (request.user.is_superuser or invitation.invitor == request.user):
            return Response(
                {"error": "You don't have permission to resend this invitation"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if invitation.status not in ['pending', 'expired']:
            return Response(
                {"error": f"Cannot resend invitation with status '{invitation.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extend expiration by 7 days from now
        invitation.expires_at = timezone.now() + timedelta(days=7)
        invitation.status = 'pending'
        invitation.save(update_fields=['expires_at', 'status', 'updated_at'])

        # Resend invitation email
        self._send_invitation_email(invitation)

        serializer = self.get_serializer({
            'message': 'Invitation resent successfully',
            'new_expires_at': invitation.expires_at
        })

        return Response(serializer.data, status=status.HTTP_200_OK)

    def _send_invitation_email(self, invitation):
        """Send invitation email to the invitee"""
        logger = logging.getLogger(__name__)

        try:
            # Construct invitation URL (you may need to adjust this based on your frontend URL)
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            invitation_url = f"{frontend_url}/register?token={invitation.token}"

            # Email subject
            subject = f"You're invited to join {invitation.workspace.name if invitation.workspace else 'Tuxonomy'}"

            # Email content
            message = f"""
Hi,

{invitation.invitor.get_full_name()} has invited you to join {invitation.workspace.name if invitation.workspace else 'Tuxonomy'}.

Click the link below to accept the invitation and create your account:
{invitation_url}

This invitation will expire on {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p UTC')}.

Best regards,
The Tuxonomy Team
"""

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                fail_silently=False,
            )

            logger.info(f"Invitation email sent successfully to {invitation.email}")

        except Exception as e:
            logger.error(f"Failed to send invitation email to {invitation.email}: {str(e)}")
            # You may want to handle this differently in production
            # For now, we'll log the error but not fail the invitation creation


@extend_schema(
    summary="Validate invitation token",
    description="Check if an invitation token is valid without consuming it.",
    tags=["Invitations"]
)
class InvitationValidateView(APIView):
    """
    View for validating invitation tokens
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token, version=None):
        """Validate invitation token"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Validating invitation token: {token} from {request.META.get('HTTP_ORIGIN', 'unknown origin')}")
        
        try:
            invitation = Invitation.objects.select_related('invitor', 'workspace').get(token=token)
        except Invitation.DoesNotExist:
            return Response(
                {
                    "valid": False,
                    "status": "not_found",
                    "message": "Invitation not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if invitation is expired and update status if needed
        if invitation.is_expired and invitation.status == 'pending':
            invitation.mark_as_expired()
        
        # Prepare response data
        response_data = {
            "valid": invitation.is_valid,
            "status": invitation.status,
            "email": invitation.email,
            "invitor_name": invitation.invitor.get_full_name(),
            "workspace_name": invitation.workspace.name if invitation.workspace else None,
            "role": invitation.role,
            "expires_at": invitation.expires_at,
        }
        
        # Add appropriate message
        if invitation.is_valid:
            response_data["message"] = "Invitation is valid"
        elif invitation.status == 'used':
            response_data["message"] = "Invitation has already been used"
        elif invitation.status == 'expired' or invitation.is_expired:
            response_data["message"] = "Invitation has expired"
        elif invitation.status == 'revoked':
            response_data["message"] = "Invitation has been revoked"
        else:
            response_data["message"] = "Invitation is not valid"
        
        serializer = InvitationValidationSerializer(response_data)
        
        return Response(
            serializer.data,
            status=status.HTTP_200_OK if invitation.is_valid else status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    summary="Register user via invitation",
    description="Create a new user account using a valid invitation token.",
    tags=["Invitations", "Authentication"]
)
class RegisterViaInvitationView(APIView):
    """
    View for user registration via invitation
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, version=None):
        """Register user via invitation token"""
        serializer = RegisterViaInvitationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()
                    
                    # Return user data
                    user_serializer = UserSerializer(user)
                    return Response(
                        {
                            "message": "User registered successfully",
                            "user": user_serializer.data
                        },
                        status=status.HTTP_201_CREATED
                    )
            except Exception as e:
                return Response(
                    {"error": f"Registration failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Get invitation statistics",
    description="Get statistics about invitations (admin only).",
    tags=["Invitations"]
)
class InvitationStatsView(APIView):
    """
    View for invitation statistics (admin only)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, version=None):
        """Get invitation statistics"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate statistics
        total_invitations = Invitation.objects.count()
        pending_invitations = Invitation.objects.filter(status='pending').count()
        used_invitations = Invitation.objects.filter(status='used').count()
        expired_invitations = Invitation.objects.filter(status='expired').count()
        revoked_invitations = Invitation.objects.filter(status='revoked').count()
        
        # Get expired but not marked invitations
        expired_pending = Invitation.objects.filter(
            status='pending',
            expires_at__lt=timezone.now()
        ).count()
        
        stats = {
            "total_invitations": total_invitations,
            "pending_invitations": pending_invitations,
            "used_invitations": used_invitations,
            "expired_invitations": expired_invitations,
            "revoked_invitations": revoked_invitations,
            "expired_but_pending": expired_pending,
            "success_rate": round((used_invitations / total_invitations * 100) if total_invitations > 0 else 0, 2)
        }
        
        return Response(stats, status=status.HTTP_200_OK)
