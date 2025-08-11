from rest_framework import serializers
from typing import Optional
from .. import models


class DimensionSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    slug = serializers.SlugField(required=False, read_only=True,
                                 help_text='URL-friendly version of the name (auto-generated)')

    class Meta:
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

        extra_kwargs = {
            'type': {'required': True, 'allow_null': False},
            'workspace': {'required': True, 'allow_null': False, "help_text": "ID of the workspace this dimension belongs to"},
            'slug': {'required': False, 'allow_blank': True, 'help_text': 'URL-friendly version of the name (auto-generated)'},
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


class DimensionValueSerializer(serializers.ModelSerializer):
    dimension_name = serializers.SerializerMethodField()
    dimension_parent_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    parent_value = serializers.SerializerMethodField()
    dimension_parent = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()

    class Meta:
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
        if obj.parent:
            return obj.parent.dimension.name  # obj.parent is already a DimensionValue instance
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
        required_fields = ['name', 'type']

        # First pass: collect all dimension names from the batch
        dimension_names_in_batch = {
            dim.get('name') for dim in value if dim.get('name')}

        # Get existing dimensions for parent resolution - map names to instances
        existing_dimensions = {
            dim.name: dim
            for dim in models.Dimension.objects.all()
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
            validated_dim = dimension.copy()

            # Check for parent_name field
            if 'parent_name' in dimension and dimension['parent_name']:
                parent_name = dimension['parent_name'].strip()

                # Look for parent in existing dimensions
                if parent_name in existing_dimensions:
                    # Assign the actual Dimension instance, not the ID
                    validated_dim['parent'] = existing_dimensions[parent_name]
                elif parent_name in dimension_names_in_batch:
                    # Parent is in the same batch - this creates a dependency
                    # We'll handle this in the view by processing parents first
                    # Keep for later resolution
                    validated_dim['_parent_name'] = parent_name
                else:
                    raise serializers.ValidationError(
                        f"Dimension at index {i}: Parent dimension '{parent_name}' not found"
                    )

                # Remove parent_name from the data
                validated_dim.pop('parent_name', None)

            validated_dimensions.append(validated_dim)

        return validated_dimensions


class DimensionValueBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk dimension value creation."""
    dimension_values = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of dimension value objects to create"
    )

    def validate_dimension_values(self, value):
        """Validate each dimension value in the list and resolve references."""
        required_fields = ['value', 'label', 'utm']

        # Get existing dimensions and dimension values for reference resolution - map to instances
        existing_dimensions = {
            dim.name: dim
            for dim in models.Dimension.objects.all()
        }

        existing_values = {}
        for val in models.DimensionValue.objects.select_related('dimension').all():
            key = f"{val.dimension.name}:{val.value}"
            existing_values[key] = val

        validated_values = []

        for i, dim_value in enumerate(value):
            # Check required fields
            for field in required_fields:
                if field not in dim_value:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: '{field}' is required"
                    )

            validated_val = dim_value.copy()

            # Resolve dimension reference
            if 'dimension_name' in dim_value:
                dimension_name = dim_value['dimension_name'].strip()
                if dimension_name in existing_dimensions:
                    # Assign the actual Dimension instance, not the ID
                    validated_val['dimension'] = existing_dimensions[dimension_name]
                    validated_val.pop('dimension_name', None)
                else:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: Dimension '{dimension_name}' not found"
                    )
            elif 'dimension' not in dim_value:
                raise serializers.ValidationError(
                    f"Dimension value at index {i}: Either 'dimension' (ID) or 'dimension_name' is required"
                )

            # Resolve parent value reference
            if 'parent_dimension_name' in dim_value and 'parent_value' in dim_value:
                parent_dim_name = dim_value['parent_dimension_name'].strip()
                parent_value = dim_value['parent_value'].strip()
                parent_key = f"{parent_dim_name}:{parent_value}"

                if parent_key in existing_values:
                    # Assign the actual DimensionValue instance, not the ID
                    validated_val['parent'] = existing_values[parent_key]
                else:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: Parent value '{parent_value}' in dimension '{parent_dim_name}' not found"
                    )

                # Remove parent reference fields
                validated_val.pop('parent_dimension_name', None)
                validated_val.pop('parent_value', None)

            # Validate dimension exists (for ID-based reference)
            if 'dimension' in validated_val and isinstance(validated_val['dimension'], int):
                try:
                    dimension_instance = models.Dimension.objects.get(
                        id=validated_val['dimension'])
                    validated_val['dimension'] = dimension_instance
                except models.Dimension.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: Dimension with id {validated_val['dimension']} does not exist"
                    )

            # Validate parent exists if provided (for ID-based reference)
            if 'parent' in validated_val and validated_val['parent'] and isinstance(validated_val['parent'], int):
                try:
                    parent_instance = models.DimensionValue.objects.get(
                        id=validated_val['parent'])
                    validated_val['parent'] = parent_instance
                except models.DimensionValue.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Dimension value at index {i}: Parent dimension value with id {validated_val['parent']} does not exist"
                    )

            validated_values.append(validated_val)

        return validated_values
