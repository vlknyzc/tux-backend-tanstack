"""
Middleware for handling multi-tenant workspace context
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import Http404
from master_data.models.base import set_current_workspace, _thread_locals

logger = logging.getLogger(__name__)


class WorkspaceMiddleware(MiddlewareMixin):
    """
    Middleware to set workspace context for multi-tenancy
    """

    def process_request(self, request):
        # For development and simplified workspace handling,
        # workspace will be determined by the views/serializers
        workspace = None
        workspace_id = None

        # Set request attributes
        request.workspace = workspace
        request.workspace_id = workspace_id

        # Set thread-local context for model managers
        set_current_workspace(workspace_id)

        # Set user context for superuser bypass
        try:
            if hasattr(request, 'user') and request.user.is_authenticated:
                _thread_locals.is_superuser = request.user.is_superuser
            else:
                _thread_locals.is_superuser = False
        except Exception as e:
            logger.warning(f"Error setting superuser context: {e}")
            _thread_locals.is_superuser = False

    def process_response(self, request, response):
        """Clean up thread-local data"""
        # Clean up thread-local storage - handle each cleanup separately
        # to ensure one failure doesn't prevent the other from being cleaned up
        
        # Clean up workspace_id
        try:
            if hasattr(_thread_locals, 'workspace_id'):
                delattr(_thread_locals, 'workspace_id')
        except Exception as e:
            logger.warning(f"Error cleaning up workspace_id: {e}")
        
        # Clean up is_superuser
        try:
            if hasattr(_thread_locals, 'is_superuser'):
                delattr(_thread_locals, 'is_superuser')
        except Exception as e:
            logger.warning(f"Error cleaning up is_superuser: {e}")

        return response
