from rest_framework import serializers
from .. import models


class DimensionSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    dimension_type_label = serializers.CharField(
        source='get_dimension_type_display', required=False)

    class Meta:
        model = models.Dimension
        fields = [
            "id",
            "definition",
            "dimension_type",
            "dimension_type_label",
            "name",
            "parent",
            "parent_name",
            "status",
        ]

    def get_parent_name(self, obj):
        if obj.parent_id:
            parent = models.Dimension.objects.get(id=obj.parent_id)
            return parent.name
        else:
            return None


class DimensionValueSerializer(serializers.ModelSerializer):
    dimension_name = serializers.SerializerMethodField()
    dimension_parent_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    parent_value = serializers.SerializerMethodField()
    dimension_parent = serializers.SerializerMethodField()

    class Meta:
        model = models.DimensionValue
        fields = [
            "id",
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

    def get_parent_name(self, obj):
        if obj.parent_id:
            parent = models.DimensionValue.objects.get(id=obj.parent_id)
            return parent.dimension_value_label
        else:
            return None

    def get_parent_value(self, obj):
        if obj.parent_id:
            parent = models.DimensionValue.objects.get(id=obj.parent_id)
            return parent.dimension_value
        else:
            return None

    def get_dimension_parent_name(self, obj):
        if obj.parent_id:
            parent = models.DimensionValue.objects.get(id=obj.parent_id)
            return parent.dimension.name
        else:
            return None
