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
            "string_uuid",
            "string_value",
            "parent",
            "parent_uuid",
        ]

    def get_field_name(self, obj):
        return obj.field.name

    def get_field_level(self, obj):
        return obj.field.field_level
