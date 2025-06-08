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
    Middleware to determine workspace from subdomain and set context
    """

    def process_request(self, request):
        # Extract subdomain from host
        host = request.get_host().lower()

        # Remove port if present
        if ':' in host:
            host = host.split(':')[0]

        host_parts = host.split('.')

        workspace = None
        workspace_id = None

        # Check for subdomain
        if len(host_parts) >= 3:  # subdomain.domain.com
            subdomain = host_parts[0]

            # Skip common non-tenant subdomains
            if subdomain not in ['www', 'api', 'admin', 'mail', 'ftp']:
                workspace, workspace_id = self._get_workspace_by_subdomain(
                    subdomain)

        # Set request attributes
        request.workspace = workspace
        request.workspace_id = workspace_id
        request.subdomain = host_parts[0] if len(host_parts) >= 3 else None

        # Set thread-local context for model managers
        set_current_workspace(workspace_id)

        # Set user context for superuser bypass
        if hasattr(request, 'user') and request.user.is_authenticated:
            _thread_locals.is_superuser = request.user.is_superuser

            # Validate user has access to this workspace (unless superuser)
            if workspace_id and not request.user.is_superuser:
                if not request.user.has_workspace_access(workspace_id):
                    logger.warning(
                        f"User {request.user.email} attempted to access "
                        f"workspace {workspace.name} without permission"
                    )
                    raise Http404("Workspace not found or access denied")
        else:
            _thread_locals.is_superuser = False

    def _get_workspace_by_subdomain(self, subdomain):
        """Get workspace by subdomain with caching"""
        from master_data.models import Workspace

        cache_key = f'workspace_subdomain_{subdomain}'
        cached_data = cache.get(cache_key)

        if cached_data:
            workspace_id, workspace_name = cached_data
            try:
                workspace = Workspace.objects.get(id=workspace_id)
                return workspace, workspace_id
            except Workspace.DoesNotExist:
                # Cache is stale, remove it
                cache.delete(cache_key)

        try:
            workspace = Workspace.objects.get(slug=subdomain)
            # Cache for 5 minutes
            cache.set(cache_key, (workspace.id, workspace.name), 300)
            return workspace, workspace.id
        except Workspace.DoesNotExist:
            logger.debug(f"No workspace found for subdomain: {subdomain}")
            return None, None

    def process_response(self, request, response):
        """Clean up thread-local data"""
        # Clean up thread-local storage
        if hasattr(_thread_locals, 'workspace_id'):
            delattr(_thread_locals, 'workspace_id')
        if hasattr(_thread_locals, 'is_superuser'):
            delattr(_thread_locals, 'is_superuser')

        return response
