"""
Middleware for handling multi-tenant workspace context
"""
import logging
import uuid
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
        # Check for stale thread-local data from previous request
        # This should not happen if cleanup works correctly, but detect it just in case
        if hasattr(_thread_locals, 'request_id'):
            logger.warning(
                'Thread-local data not cleaned from previous request!',
                extra={
                    'stale_request_id': _thread_locals.request_id,
                    'current_request_path': request.path,
                    'current_request_method': request.method,
                }
            )
            # Clear stale data immediately
            try:
                _thread_locals.__dict__.clear()
            except Exception as e:
                logger.error(f"Error clearing stale thread-local data: {e}")

        # Generate unique request ID for this request
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        _thread_locals.request_id = request_id

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
        # Verify we're cleaning up the correct request's data
        if hasattr(request, 'request_id'):
            thread_local_request_id = getattr(_thread_locals, 'request_id', None)
            if thread_local_request_id and thread_local_request_id != request.request_id:
                logger.error(
                    'Thread-local request ID mismatch during cleanup!',
                    extra={
                        'request_id': request.request_id,
                        'thread_local_request_id': thread_local_request_id,
                        'request_path': request.path,
                    }
                )

        # Clear ALL thread-local data at once (more robust than individual delattr)
        try:
            _thread_locals.__dict__.clear()
        except Exception as e:
            logger.error(
                f"Error cleaning up thread-local storage: {e}",
                extra={
                    'request_path': getattr(request, 'path', 'unknown'),
                    'request_id': getattr(request, 'request_id', 'unknown'),
                }
            )
            # Try again - ensure cleanup happens even if first attempt failed
            try:
                _thread_locals.__dict__.clear()
            except:
                # Last resort - log critical error
                logger.critical("Failed to clear thread-local storage after retry!")

        return response

    def process_exception(self, request, exception):
        """Clean up thread-local data when exception occurs"""
        # Ensure cleanup happens even when view raises exception
        try:
            _thread_locals.__dict__.clear()
        except Exception as e:
            logger.error(
                f"Error cleaning up thread-local storage in exception handler: {e}",
                extra={
                    'request_path': getattr(request, 'path', 'unknown'),
                    'request_id': getattr(request, 'request_id', 'unknown'),
                    'exception': str(exception),
                }
            )

        # Return None to let the exception propagate
        return None
