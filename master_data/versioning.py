import re
from rest_framework.versioning import BaseVersioning
from rest_framework import exceptions


class CustomURLPathVersioning(BaseVersioning):
    """
    Custom URL path versioning that extracts version from paths like /api/v1/ or /api/v2/
    """
    invalid_version_message = 'Invalid version in URL path. Expected "v1" or "v2".'
    default_version = 'v1'
    allowed_versions = ['v1', 'v2']

    def determine_version(self, request, *args, **kwargs):
        """
        Extract version from URL path like /api/v1/ or /api/v2/
        """
        path = request.path_info or request.path

        # Use regex to extract version from path
        version_pattern = r'/api/v(\d+)/'
        match = re.search(version_pattern, path)

        if match:
            version_number = match.group(1)
            version = f'v{version_number}'

            # Validate version is allowed
            if hasattr(self, 'allowed_versions') and self.allowed_versions:
                if version not in self.allowed_versions:
                    raise exceptions.NotFound(self.invalid_version_message)

            return version

        # If no version found in path, check if it's a legacy path (/api/)
        if '/api/' in path and '/api/v' not in path:
            # Legacy path, return default version
            return getattr(self, 'default_version', 'v1')

        # No version found and not a legacy path
        return getattr(self, 'default_version', 'v1')

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        """
        Return a versioned URL for the given view name.
        """
        if request.version:
            return f'/api/{request.version}/'
        return '/api/'
