"""
Base serializers for master_data app.

Provides common functionality and security patterns for all serializers.
"""

from rest_framework import serializers


class WorkspaceOwnedSerializer(serializers.ModelSerializer):
    """
    Base serializer for models that belong to a workspace.

    Implements security best practices:
    - Prevents mass assignment to workspace field
    - Prevents mass assignment to created_by field
    - Prevents modification of timestamps

    Models using WorkspaceMixin should inherit from this serializer
    to prevent authorization bypass vulnerabilities.

    Usage:
        class MyModelSerializer(WorkspaceOwnedSerializer):
            class Meta(WorkspaceOwnedSerializer.Meta):
                model = MyModel
                fields = ['id', 'name', 'workspace', 'created_by', ...]

    Note: Views must set workspace and created_by in perform_create():
        def perform_create(self, serializer):
            serializer.save(
                workspace=self.get_workspace(),
                created_by=self.request.user
            )
    """

    class Meta:
        # These fields should be read-only across all workspace-owned models
        read_only_fields = [
            'id',
            'workspace',      # Set by view from URL path
            'created_by',     # Set by view from request.user
            'created',        # Auto-managed timestamp
            'last_updated',   # Auto-managed timestamp
        ]
