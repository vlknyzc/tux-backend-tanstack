from rest_framework import serializers
from .. import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class StringSerializer(serializers.ModelSerializer):
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    platform_id = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    submission_name = serializers.SerializerMethodField()
    rule_id = serializers.SerializerMethodField()
    rule_name = serializers.SerializerMethodField()

    class Meta:
        model = models.String
        fields = [
            "id",
            "submission",
            "submission_name",
            "rule_id",
            "rule_name",
            "last_updated",
            "created",
            "field",
            "field_name",
            "field_level",
            "platform_id",
            "platform_name",
            "string_uuid",
            "value",
            "parent",
            "parent_uuid",
        ]

    def get_field_name(self, obj):
        return obj.field.name

    def get_submission_name(self, obj):
        return obj.submission.name if obj.submission else None

    def get_platform_name(self, obj):
        return obj.field.platform.name if obj.field and obj.field.platform else None

    def get_field_level(self, obj):
        return obj.field.field_level

    def get_field_level(self, obj):
        return obj.field.field_level

    def get_platform_id(self, obj):
        return obj.field.platform.id if obj.field and obj.field.platform else None

    def get_platform_name(self, obj):
        return obj.field.platform.name if obj.field and obj.field.platform else None

    def get_rule_id(self, obj):
        return obj.submission.rule.id if obj.submission and obj.submission.rule else None

    def get_rule_name(self, obj):
        return obj.submission.rule.name if obj.submission and obj.submission.rule else None


class StringDetailSerializer(serializers.ModelSerializer):
    dimension_value_display = serializers.SerializerMethodField()
    dimension_value_label = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()
    submission_name = serializers.SerializerMethodField()

    class Meta:
        model = models.StringDetail
        fields = [
            "id",
            "submission_name",
            "string",
            "dimension",
            "dimension_name",
            "dimension_value",
            "dimension_value_display",
            "dimension_value_label",
            "dimension_value_freetext",
            "created",
            "last_updated",
        ]
        read_only_fields = ["created", "last_updated"]

    def get_submission_name(self, obj):
        return obj.string.submission.name if obj.string and obj.string.submission else None

    def get_dimension_name(self, obj):
        return obj.dimension.name if obj.dimension else None

    def get_dimension_value_display(self, obj):
        return obj.dimension_value.dimension_value if obj.dimension_value else None

    def get_dimension_value_label(self, obj):
        return obj.dimension_value.dimension_value_label if obj.dimension_value else None
