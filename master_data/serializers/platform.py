from rest_framework import serializers
from .. import models


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Platform
        fields = [
            "id",
            "platform_type",
            "name",
            "icon_name",
        ]


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
