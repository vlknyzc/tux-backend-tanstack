from rest_framework import serializers
from .. import models


class PlatformSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Platform
        fields = [
            "id",
            "platform_type",
            "name",
            "slug",
            "icon_name",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None


class FieldSerializer(serializers.ModelSerializer):
    next_field_name = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

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
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_next_field_name(self, obj):
        if obj.next_field_id:
            next_field = models.Field.objects.get(id=obj.next_field_id)
            return next_field.name
        else:
            return None

    def get_platform_name(self, obj):
        return obj.platform.name

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None


class PlatformTemplateSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True)

    class Meta:
        model = models.Platform
        fields = [
            "id",
            "name",
            "slug",
            "fields"
        ]
