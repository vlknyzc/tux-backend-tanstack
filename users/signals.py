"""
Django signals for the users app.
Handles automatic email sending and other post-save operations.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Invitation

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Invitation)
def send_invitation_email_on_create(sender, instance, created, **kwargs):
    """
    Send invitation email automatically when a new invitation is created.
    
    Args:
        sender: The model class (Invitation)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created and instance.status == 'pending':
        try:
            logger.info(f"Sending invitation email to {instance.email} for invitation {instance.token}")
            
            # Import here to avoid circular imports
            from .services import send_invitation_email
            result = send_invitation_email(instance)
            
            if result['success']:
                logger.info(
                    f"✅ Invitation email sent successfully to {instance.email}. "
                    f"Message ID: {result['message_id']}"
                )
            else:
                logger.error(
                    f"❌ Failed to send invitation email to {instance.email}. "
                    f"Error: {result['message']}"
                )
                
        except Exception as e:
            logger.error(
                f"❌ Unexpected error sending invitation email to {instance.email}: {str(e)}",
                exc_info=True
            )


@receiver(post_save, sender=Invitation)
def log_invitation_status_changes(sender, instance, created, **kwargs):
    """
    Log invitation status changes for audit purposes.
    
    Args:
        sender: The model class (Invitation)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        logger.info(
            f"📨 New invitation created: {instance.email} invited by "
            f"{instance.invitor.email if instance.invitor else 'System'} "
            f"to workspace '{instance.workspace.name if instance.workspace else 'N/A'}' "
            f"with role '{instance.get_role_display()}'. "
            f"Expires: {instance.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
    else:
        # Log status changes for existing invitations
        logger.info(
            f"📝 Invitation {instance.token} for {instance.email} "
            f"updated to status: {instance.status}"
        )
