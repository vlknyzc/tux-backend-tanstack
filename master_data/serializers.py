from rest_framework import serializers

from . import models


class DimensionSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    dimension_type_label = serializers.CharField(
        source='get_dimension_type_display', required=False)

    class Meta:
        model = models.Dimension
        fields = [
            "id",
            "workspace",
            "definition",
            "dimension_type",
            "dimension_type_label",
            "name",
            "parent",
            "parent_name",
        ]

    def get_parent_name(self, obj):
        if obj.parent_id:
            parent = models.Dimension.objects.get(id=obj.parent_id)
            return parent.name
        else:
            return None


class JunkDimensionSerializer(serializers.ModelSerializer):
    dimension_name = serializers.SerializerMethodField()
    dimension_parent_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    parent_value = serializers.SerializerMethodField()
    # workspace = serializers.SerializerMethodField()
    dimension_parent = serializers.SerializerMethodField()

    class Meta:
        model = models.JunkDimension
        fields = [
            "id",
            "workspace",
            # "dimension_value_code",
            "valid_from",
            "definition",
            "dimension_value",
            "valid_until",
            "dimension_value_label",
            "dimension_value_utm",
            "dimension",
            "dimension_name",
            "dimension_parent_name",
            "dimension_parent",
            "parent",
            "parent_name",
            "parent_value",
        ]

    def get_dimension_parent(self, obj):
        if obj.dimension.parent_id:
            parent = models.Dimension.objects.get(id=obj.dimension.parent_id)
            return parent.id
        else:
            return None

    def get_dimension_name(self, obj):
        return obj.dimension.name

    # def get_workspace(self, obj):
    #     return obj.dimension.workspace.id

    def get_parent_name(self, obj):
        if obj.parent_id:
            parent = models.JunkDimension.objects.get(id=obj.parent_id)
            return parent.dimension_value_label
        else:
            return None

    def get_parent_value(self, obj):
        if obj.parent_id:
            parent = models.JunkDimension.objects.get(id=obj.parent_id)
            return parent.dimension_value
        else:
            return None

    def get_dimension_parent_name(self, obj):
        if obj.parent_id:
            parent = models.JunkDimension.objects.get(id=obj.parent_id)
            return parent.dimension.name
        else:
            return None


class WorkspaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Workspace
        fields = [
            "id",
            "name",
            "logo",
            "created_by",
            "created",
            "last_updated",
        ]
        read_only_fields = ["created", "last_updated"]


class PlatformSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Platform
        fields = [
            "id",
            "platform_type",
            "name",
        ]


class StructureSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField()
    # convention_name = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    # convention = serializers.SerializerMethodField()
    convention_name = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()
    dimension_type = serializers.SerializerMethodField()
    parent_dimension_id = serializers.SerializerMethodField()
    parent_dimension_name = serializers.SerializerMethodField()
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    next_field = serializers.SerializerMethodField()
    in_parent_field = serializers.SerializerMethodField()

    class Meta:
        model = models.Structure
        fields = [
            "id",
            "workspace",
            "convention",
            "convention_name",
            "platform",
            "platform_name",
            "field",
            "field_name",
            "field_level",
            "next_field",
            "dimension",
            "dimension_name",
            "dimension_type",
            "dimension_order",
            "delimeter_after_dimension",
            "delimeter_before_dimension",
            "parent_dimension_name",
            "parent_dimension_id",
            "in_parent_field",
        ]

    def get_workspace(self, obj):
        return obj.dimension.workspace.id

    def get_convention(self, obj):
        return obj.convention.id

    def get_convention_name(self, obj):
        return obj.convention.name

    def get_platform(self, obj):
        return obj.field.platform.id

    def get_platform_name(self, obj):
        return obj.field.platform.name

    def get_dimension_name(self, obj):
        return obj.dimension.name

    def get_dimension_type(self, obj):
        return obj.dimension.dimension_type

    def get_parent_dimension_name(self, obj):
        if obj.dimension.parent_id:
            parent = models.Dimension.objects.get(id=obj.dimension.parent_id)
            return parent.name
        else:
            return None

    def get_parent_dimension_id(self, obj):
        if obj.dimension.parent_id:
            parent = models.Dimension.objects.get(id=obj.dimension.parent_id)
            return parent.id
        else:
            return None

    def get_field_name(self, obj):
        return obj.field.name

    def get_field_level(self, obj):
        return obj.field.field_level

    def get_next_field(self, obj):
        if obj.field.next_field_id:
            next_field = models.Field.objects.get(id=obj.field.next_field_id)
            return next_field.name
        else:
            return None

    def get_in_parent_field(self, obj):
        field_level = obj.field.field_level
        if field_level <= 1:
            return False

        # Check for existence of a parent level structure
        parent_exists = models.Structure.objects.filter(
            convention=obj.convention,
            field__platform=obj.field.platform,
            dimension=obj.dimension,
            field__field_level=field_level - 1
        ).exists()

        return parent_exists


class FieldSerializer(serializers.ModelSerializer):

    next_field_name = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Field
        fields = [
            "id",
            "platform",
            "platform_name",
            "name",
            "field_level",
            "next_field",
            "next_field_name",
        ]

    def get_next_field_name(self, obj):
        if obj.next_field_id:
            next_field = models.Field.objects.get(id=obj.next_field_id)
            return next_field.name
        else:
            return None

    def get_platform_name(self, obj):
        return obj.platform.name


class PlatformTemplateSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True)

    class Meta:
        model = models.Platform
        fields = [
            "id",
            "name",
            "fields"
        ]


class ConventionPlatformSerializer(serializers.ModelSerializer):

    platform_name = serializers.SerializerMethodField()

    class Meta:
        model = models.ConventionPlatform
        fields = '__all__'

    def get_platform_name(self, obj):
        return obj.platform.name


class ConventionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Convention
        fields = ['id', 'workspace', 'name', 'description',
                  'status', 'valid_from', 'valid_until']

    def validate(self, data):
        """
        Check that valid_until is after valid_from if provided
        """
        if data.get('valid_until') and data['valid_until'] < data['valid_from']:
            raise serializers.ValidationError({
                "valid_until": "End date must be after start date"
            })
        return data


class StringSerializer(serializers.ModelSerializer):

    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    convention_name = serializers.SerializerMethodField()
    platform_id = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()

    class Meta:
        model = models.String
        fields = [
            "id",
            "last_updated",
            "created",
            "workspace",
            "field",
            "field_name",
            "field_level",
            "convention",
            "convention_name",
            "platform_id",
            "platform_name",
            "string_uuid",
            "string_value",
            "parent",
            "parent_uuid",
        ]

    def get_field_name(self, obj):
        return obj.field.name

    def get_field_level(self, obj):
        return obj.field.field_level

    def get_convention_name(self, obj):
        return obj.convention.name if obj.convention else None

    def get_platform_id(self, obj):
        return obj.field.platform.id if obj.field and obj.field.platform else None

    def get_platform_name(self, obj):
        return obj.field.platform.name if obj.field and obj.field.platform else None


class StringItemSerializer(serializers.ModelSerializer):
    structure_field_name = serializers.SerializerMethodField()
    dimension_value_id = serializers.SerializerMethodField()
    dimension_value = serializers.SerializerMethodField()
    dimension_value_label = serializers.SerializerMethodField()
    dimension_id = serializers.SerializerMethodField()

    class Meta:
        model = models.StringItem
        fields = [
            "id",
            "string",
            "structure",
            "structure_field_name",
            "dimension_value_id",
            "dimension_value",
            "dimension_value_label",
            "dimension_value_freetext",
            "dimension_id",
            "created",
            "last_updated",
        ]
        read_only_fields = ["created", "last_updated"]

    def validate(self, data):
        """
        Validate based on dimension type
        """
        structure = data.get('structure')
        if not structure:
            raise serializers.ValidationError({
                "structure": "Structure is required"
            })

        dimension_type = structure.dimension.dimension_type
        dimension_value_id = self.initial_data.get('dimension_value_id')
        dimension_value = self.initial_data.get('dimension_value')
        dimension_value_label = self.initial_data.get('dimension_value_label')
        dimension_value_freetext = self.initial_data.get(
            'dimension_value_freetext')

        # For free text dimensions
        if dimension_type in [models.Dimension.FREE_TEXT, models.Dimension.FREE_TEXT_WITH_VALIDATIONS]:
            if dimension_value_id or dimension_value_label:
                raise serializers.ValidationError({
                    "dimension_value_id": "Cannot set dimension_value_id for free text dimensions",
                    "dimension_value_label": "Cannot set dimension_value_label for free text dimensions"
                })
            # Remove the requirement for dimension_value_freetext
            data['dimension_value'] = None
            return data

        # For mastered dimensions
        if dimension_type == models.Dimension.MASTERED:
            if dimension_value_freetext:
                raise serializers.ValidationError({
                    "dimension_value_freetext": "Cannot set free text for mastered dimensions"
                })
            if not dimension_value_id:
                raise serializers.ValidationError({
                    "dimension_value_id": "Dimension value ID is required for mastered dimensions"
                })

            try:
                junk_dimension = models.JunkDimension.objects.get(
                    id=dimension_value_id)

                # If other fields are provided, validate they match
                if dimension_value and junk_dimension.dimension_value != dimension_value:
                    raise serializers.ValidationError({
                        "dimension_value": f"Value '{dimension_value}' does not match JunkDimension with id {dimension_value_id}"
                    })

                if dimension_value_label and junk_dimension.dimension_value_label != dimension_value_label:
                    raise serializers.ValidationError({
                        "dimension_value_label": f"Label '{dimension_value_label}' does not match JunkDimension with id {dimension_value_id}"
                    })

                data['dimension_value'] = junk_dimension

            except models.JunkDimension.DoesNotExist:
                raise serializers.ValidationError({
                    "dimension_value_id": f"JunkDimension with id {dimension_value_id} does not exist"
                })

        return data

    def create(self, validated_data):
        # Remove only the extra fields that aren't in the model
        validated_data.pop('dimension_value_id', None)
        validated_data.pop('dimension_value_label', None)

        # Note: Don't pop 'dimension_value' as it contains the JunkDimension instance
        # that was set in the validate method

        # Create the StringItem instance
        string_item = models.StringItem.objects.create(**validated_data)
        return string_item

    def get_structure_field_name(self, obj):
        return obj.structure.field.name if obj.structure else None

    def get_dimension_id(self, obj):
        return obj.structure.dimension.id if obj.structure and obj.structure.dimension else None

    def get_dimension_value_id(self, obj):
        return obj.dimension_value.id if obj.dimension_value else None

    def get_dimension_value(self, obj):
        return obj.dimension_value.dimension_value if obj.dimension_value else None

    def get_dimension_value_label(self, obj):
        return obj.dimension_value.dimension_value_label if obj.dimension_value else None


class ConventionPlatformDetailSerializer(serializers.ModelSerializer):
    platform_name = serializers.SerializerMethodField()
    platform_fields = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    workspace = serializers.SerializerMethodField()
    convention_name = serializers.SerializerMethodField()

    class Meta:
        model = models.ConventionPlatform
        fields = [
            'id',
            'workspace',
            'workspace_name',
            'convention',
            'convention_name',
            'platform',
            'platform_name',
            'platform_fields',
            'created',
            'last_updated'
        ]

    def get_platform_name(self, obj):
        return obj.platform.name

    def get_platform_fields(self, obj):
        fields = models.Field.objects.filter(
            platform=obj.platform).order_by('field_level')
        return FieldSerializer(fields, many=True).data

    def get_workspace_name(self, obj):
        return obj.convention.workspace.name

    def get_workspace(self, obj):
        return obj.convention.workspace.id

    def get_convention_name(self, obj):
        return obj.convention.name
