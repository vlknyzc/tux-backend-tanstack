from rest_framework import serializers
from .. import models


class DimensionSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Dimension
        fields = [
            "id",
            "description",
            "type",
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
            return parent.label
        else:
            return None

    def get_parent_value(self, obj):
        if obj.parent_id:
            parent = models.DimensionValue.objects.get(id=obj.parent_id)
            return parent.value
        else:
            return None

    def get_dimension_parent_name(self, obj):
        if obj.parent_id:
            parent = models.DimensionValue.objects.get(id=obj.parent_id)
            return parent.dimension.name
        else:
            return None
