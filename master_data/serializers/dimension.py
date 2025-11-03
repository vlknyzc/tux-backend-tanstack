from rest_framework import serializers
from typing import Optional
from .. import models
from .base import WorkspaceOwnedSerializer


class DimensionSerializer(WorkspaceOwnedSerializer):
    parent_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    slug = serializers.SlugField(required=False, read_only=True,
                                 help_text='URL-friendly version of the name (auto-generated)')

    class Meta(WorkspaceOwnedSerializer.Meta):
        model = models.Dimension
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "type",
            "parent",
            "parent_name",
            "status",
            "workspace",
            "workspace_name",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

        # Extend parent read_only_fields with slug (auto-generated)
        read_only_fields = WorkspaceOwnedSerializer.Meta.read_only_fields + ['slug']

        extra_kwargs = {
            'type': {'required': True, 'allow_null': False},
        }

    def get_parent_name(self, obj) -> Optional[str]:
        if obj.parent:
            return obj.parent.name  # obj.parent is already a Dimension instance
        else:
            return None

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_workspace_name(self, obj) -> Optional[str]:
        if obj.workspace:
            return obj.workspace.name
        return None

    def validate(self, data):
        """Validate dimension data including parent relationships."""
        # Get workspace - it can come from data or context
        workspace = data.get('workspace') or self.context.get('workspace')

        if not workspace:
            raise serializers.ValidationError(
                "Workspace is required for dimension validation"
            )

        # Validate parent dimension if provided
        parent = data.get('parent')
        if parent:
            self._validate_parent_dimension(parent, workspace)

        return data

    def _validate_parent_dimension(self, parent, workspace):
        """
        Validate parent dimension.

        Checks:
        1. Parent exists in the same workspace
        2. No circular reference would be created
        """
        # Check workspace match
        if parent.workspace != workspace:
            raise serializers.ValidationError({
                'parent': 'Parent dimension must be in the same workspace'
            })

        # Check circular reference (only when updating existing dimension)
        if self.instance:
            if self._would_create_circular_reference(self.instance, parent):
                raise serializers.ValidationError({
                    'parent': 'This would create a circular reference in the dimension hierarchy'
                })

    def _would_create_circular_reference(self, dimension, new_parent):
        """
        Check if setting new_parent would create a circular reference.

        Traverses up the parent chain to see if we encounter the dimension
        we're trying to update.

        Args:
            dimension: The dimension being updated
            new_parent: The proposed new parent

        Returns:
            True if circular reference would be created, False otherwise
        """
        current = new_parent
        visited = set()

        while current:
            # If we've seen this dimension before, we have a cycle
            if current.id in visited:
                # This is a cycle but not involving our dimension
                return False

            # If we encounter the dimension we're updating, that's a circular reference
            if current.id == dimension.id:
                return True

            visited.add(current.id)
            current = current.parent

        return False


class DimensionValueSerializer(WorkspaceOwnedSerializer):
    dimension_name = serializers.SerializerMethodField()
    dimension_parent_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    parent_value = serializers.SerializerMethodField()
    dimension_parent = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()

    class Meta(WorkspaceOwnedSerializer.Meta):
        model = models.DimensionValue
        fields = [
            "id",
            "valid_from",
            "description",
            "value",
            "valid_until",
            "label",
            "utm",
            "dimension",
            "dimension_name",
            "dimension_parent_name",
            "dimension_parent",
            "parent",
            "parent_name",
            "parent_value",
            "workspace",
            "workspace_name",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]
        # Inherit read_only_fields from WorkspaceOwnedSerializer
        read_only_fields = WorkspaceOwnedSerializer.Meta.read_only_fields

    def validate_dimension(self, value):
        if value is not None:
            try:
                models.Dimension.objects.get(id=value.id)
            except models.Dimension.DoesNotExist:
                raise serializers.ValidationError(
                    f"Dimension with id {value.id} does not exist")
        return value

    def get_dimension_parent(self, obj) -> Optional[int]:
        if obj.dimension.parent:
            # obj.dimension.parent is already a Dimension instance
            return obj.dimension.parent.id
        else:
            return None

    def get_dimension_name(self, obj) -> str:
        return obj.dimension.name

    def get_parent_name(self, obj) -> Optional[str]:
        if obj.parent:
            return obj.parent.label  # obj.parent is already a DimensionValue instance
        else:
            return None

    def get_parent_value(self, obj) -> Optional[str]:
        if obj.parent:
            return obj.parent.value  # obj.parent is already a DimensionValue instance
        else:
            return None

    def get_dimension_parent_name(self, obj) -> Optional[str]:
        if obj.dimension.parent:
            return obj.dimension.parent.name  # obj.dimension.parent is the parent Dimension
        else:
            return None

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_workspace_name(self, obj) -> Optional[str]:
        if obj.workspace:
            return obj.workspace.name
        return None


class DimensionBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk dimension creation."""
    dimensions = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of dimension objects to create"
    )

    def validate_dimensions(self, value):
        """Validate each dimension in the list and resolve parent references."""
        # Require workspace context for validation
        workspace = self.context.get('workspace')
        if not workspace:
            raise serializers.ValidationError(
                "Workspace context is required for dimension validation"
            )

        required_fields = ['name', 'type']

        # First pass: collect all dimension names from the batch
        dimension_names_in_batch = {
            dimension_data.get('name')
            for dimension_data in value
            if dimension_data.get('name')
        }

        # Get existing dimensions for parent resolution - map names to instances
        # SECURITY: Filter by workspace to prevent cross-workspace information disclosure
        existing_dimensions = {
            dimension.name: dimension
            for dimension in models.Dimension.objects.filter(workspace=workspace)
        }

        validated_dimensions = []

        for i, dimension in enumerate(value):
            # Check required fields
            for field in required_fields:
                if field not in dimension:
                    raise serializers.ValidationError(
                        f"Dimension at index {i}: '{field}' is required"
                    )

            # Validate choices
            if 'type' in dimension:
                from ..constants import DimensionTypeChoices
                valid_types = [choice[0]
                               for choice in DimensionTypeChoices.choices]
                if dimension['type'] not in valid_types:
                    raise serializers.ValidationError(
                        f"Dimension at index {i}: Invalid type '{dimension['type']}'. "
                        f"Valid options: {valid_types}"
                    )

            if 'status' in dimension:
                from ..constants import StatusChoices
                valid_statuses = [choice[0]
                                  for choice in StatusChoices.choices]
                if dimension['status'] not in valid_statuses:
                    raise serializers.ValidationError(
                        f"Dimension at index {i}: Invalid status '{dimension['status']}'. "
                        f"Valid options: {valid_statuses}"
                    )

            # Handle parent resolution
            validated_dimension_data = dimension.copy()

            # Check for parent_name field
            if 'parent_name' in dimension and dimension['parent_name']:
                parent_name = dimension['parent_name'].strip()

                # Look for parent in existing dimensions
                if parent_name in existing_dimensions:
                    # Assign the actual Dimension instance, not the ID
                    validated_dimension_data['parent'] = existing_dimensions[parent_name]
                elif parent_name in dimension_names_in_batch:
                    # Parent is in the same batch - this creates a dependency
                    # We'll handle this in the view by processing parents first
                    # Keep for later resolution
                    validated_dimension_data['_parent_name'] = parent_name
                else:
                    raise serializers.ValidationError(
                        f"Dimension at index {i}: Parent dimension '{parent_name}' not found"
                    )

                # Remove parent_name from the data
                validated_dimension_data.pop('parent_name', None)

            validated_dimensions.append(validated_dimension_data)

        return validated_dimensions


class DimensionValueBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk dimension value creation."""
    dimension_values = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of dimension value objects to create"
    )

    def validate_dimension_values(self, value):
        """Validate each dimension value in the list and resolve references."""
        # Require workspace context for validation
        workspace = self.context.get('workspace')
        if not workspace:
            raise serializers.ValidationError(
                "Workspace context is required for dimension value validation"
            )

        required_fields = ['value', 'label', 'utm']

        # Get existing dimensions and dimension values for reference resolution - map to instances
        # SECURITY: Filter by workspace to prevent cross-workspace information disclosure
        existing_dimensions = {
            dimension.name: dimension
            for dimension in models.Dimension.objects.filter(workspace=workspace)
        }

        existing_values = {}
        for dimension_value in models.DimensionValue.objects.filter(workspace=workspace).select_related('dimension'):
            key = f"{dimension_value.dimension.name}:{dimension_value.value}"
            existing_values[key] = dimension_value

        validated_values = []

        for i, dimension_value_data in enumerate(value):
            # Check required fields
            for field in required_fields:
                if field not in dimension_value_data:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: '{field}' is required"
                    )

            validated_value_data = dimension_value_data.copy()

            # Resolve dimension reference
            if 'dimension_name' in dimension_value_data:
                dimension_name = dimension_value_data['dimension_name'].strip()
                if dimension_name in existing_dimensions:
                    # Assign the actual Dimension instance, not the ID
                    validated_value_data['dimension'] = existing_dimensions[dimension_name]
                    validated_value_data.pop('dimension_name', None)
                else:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: Dimension '{dimension_name}' not found"
                    )
            elif 'dimension' not in dimension_value_data:
                raise serializers.ValidationError(
                    f"Dimension value at index {i}: Either 'dimension' (ID) or 'dimension_name' is required"
                )

            # Resolve parent value reference
            if 'parent_dimension_name' in dimension_value_data and 'parent_value' in dimension_value_data:
                parent_dimension_name = dimension_value_data['parent_dimension_name'].strip()
                parent_value = dimension_value_data['parent_value'].strip()
                parent_key = f"{parent_dimension_name}:{parent_value}"

                if parent_key in existing_values:
                    # Assign the actual DimensionValue instance, not the ID
                    validated_value_data['parent'] = existing_values[parent_key]
                else:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: Parent value '{parent_value}' in dimension '{parent_dimension_name}' not found"
                    )

                # Remove parent reference fields
                validated_value_data.pop('parent_dimension_name', None)
                validated_value_data.pop('parent_value', None)

            # Validate dimension exists (for ID-based reference)
            if 'dimension' in validated_value_data and isinstance(validated_value_data['dimension'], int):
                try:
                    dimension_instance = models.Dimension.objects.get(
                        id=validated_value_data['dimension'])
                    validated_value_data['dimension'] = dimension_instance
                except models.Dimension.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: Dimension with id {validated_value_data['dimension']} does not exist"
                    )

            # Validate parent exists if provided (for ID-based reference)
            if 'parent' in validated_value_data and validated_value_data['parent'] and isinstance(validated_value_data['parent'], int):
                try:
                    parent_instance = models.DimensionValue.objects.get(
                        id=validated_value_data['parent'])
                    validated_value_data['parent'] = parent_instance
                except models.DimensionValue.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: Parent dimension value with id {validated_value_data['parent']} does not exist"
                    )

            validated_values.append(validated_value_data)

        return validated_values
