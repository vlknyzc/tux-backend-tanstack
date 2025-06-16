from rest_framework import permissions


class IsAuthenticatedOrDebugReadOnly(permissions.BasePermission):
    """
    Custom permission class that:
    - Allows read-only access in DEBUG mode
    - Requires authentication for all other operations
    """

    def has_permission(self, request, view):
        from django.conf import settings

        # In DEBUG mode, allow read-only access
        if settings.DEBUG and request.method in permissions.SAFE_METHODS:
            return True

        # Otherwise require authentication
        return bool(request.user and request.user.is_authenticated)
