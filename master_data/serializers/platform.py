from rest_framework import serializers
from .. import models
from typing import Optional, Dict, List, Any


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

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None


class EntitySerializer(serializers.ModelSerializer):
    next_entity_name = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Entity
        fields = [
            "id",
            "platform",
            "platform_name",
            "name",
            "entity_level",
            "next_entity",
            "next_entity_name",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]

    def get_next_entity_name(self, obj) -> Optional[str]:
        if obj.next_entity_id:
            return obj.next_entity.name
        return None

    def get_platform_name(self, obj) -> str:
        return obj.platform.name

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None


class PlatformTemplateSerializer(serializers.ModelSerializer):
    entities = EntitySerializer(many=True)

    class Meta:
        model = models.Platform
        fields = [
            "id",
            "name",
            "slug",
            "entities"
        ]
