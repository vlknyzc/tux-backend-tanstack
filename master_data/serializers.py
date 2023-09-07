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
    parent_dimension_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    parent_value = serializers.SerializerMethodField()
    # workspace = serializers.SerializerMethodField()

    class Meta:
        model = models.JunkDimension
        fields = [
            "id",
            "workspace",
            "dimension_value_code",
            "valid_from",
            "definition",
            "dimension_value",
            "valid_until",
            "dimension_value_label",
            "dimension_value_utm",
            "dimension",
            "dimension_name",
            "parent_dimension_name",
            "parent",
            "parent_name",
            "parent_value",

        ]

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

    def get_parent_dimension_name(self, obj):
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
            "created_by",
        ]


class PlatformSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Platform
        fields = [
            "id",
            "platform_type",
            "name",
            "platform_field",
            "field_level",
            "workspace",
        ]


class RuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Rule
        fields = [
            "id",
            "workspace",
            "name",
            "valid_from",
            "valid_until",

        ]


class StructureSerializer(serializers.ModelSerializer):
    dimension_name = serializers.SerializerMethodField()
    parent_dimension_name = serializers.SerializerMethodField()
    platform_field = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Structure
        fields = [
            "id",
            "platform",
            "platform_name",
            "platform_field",
            "field_level",
            "delimeter_after_dimension",
            "delimeter_before_dimension",
            "dimension_order",
            "rule",
            "dimension",
            "dimension_name",
            "parent_dimension_name",
        ]

    def get_dimension_name(self, obj):
        return obj.dimension.name

    def get_parent_dimension_name(self, obj):
        if obj.dimension.parent_id:
            parent = models.Dimension.objects.get(id=obj.dimension.parent_id)
            return parent.name
        else:
            return None

    def get_platform_field(self, obj):
        return obj.platform.platform_field

    def get_platform_name(self, obj):
        return obj.platform.name

    def get_field_level(self, obj):
        return obj.platform.field_level
