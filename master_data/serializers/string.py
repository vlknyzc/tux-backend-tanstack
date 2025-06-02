from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .. import models
from ..services import StringGenerationService, NamingConventionError


class StringSerializer(serializers.ModelSerializer):
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    platform_id = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    platform_slug = serializers.SerializerMethodField()
    submission_name = serializers.SerializerMethodField()
    rule_id = serializers.SerializerMethodField()
    rule_name = serializers.SerializerMethodField()

    # New fields for enhanced business logic
    dimension_values = serializers.SerializerMethodField()
    hierarchy_path = serializers.SerializerMethodField()
    can_have_children = serializers.SerializerMethodField()
    suggested_child_field = serializers.SerializerMethodField()
    naming_conflicts = serializers.SerializerMethodField()

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
            "platform_slug",
            "string_uuid",
            "value",
            "parent",
            "parent_uuid",
            # New business logic fields
            "is_auto_generated",
            "generation_metadata",
            "dimension_values",
            "hierarchy_path",
            "can_have_children",
            "suggested_child_field",
            "naming_conflicts",
        ]
        read_only_fields = ["string_uuid",
                            "rule_id", "created", "last_updated"]

    def get_field_name(self, obj):
        return obj.field.name

    def get_submission_name(self, obj):
        return obj.submission.name if obj.submission else None

    def get_platform_name(self, obj):
        return obj.field.platform.name if obj.field and obj.field.platform else None

    def get_field_level(self, obj):
        return obj.field.field_level

    def get_platform_id(self, obj):
        return obj.field.platform.id if obj.field and obj.field.platform else None

    def get_platform_slug(self, obj):
        return obj.field.platform.slug if obj.field and obj.field.platform else None

    def get_rule_id(self, obj):
        return obj.submission.rule.id if obj.submission and obj.submission.rule else None

    def get_rule_name(self, obj):
        return obj.submission.rule.name if obj.submission and obj.submission.rule else None

    def get_dimension_values(self, obj):
        """Get dimension values used to generate this string."""
        return obj.get_dimension_values()

    def get_hierarchy_path(self, obj):
        """Get the hierarchy path for this string."""
        path = obj.get_hierarchy_path()
        return [{"id": s.id, "value": s.value, "field_level": s.field.field_level} for s in path]

    def get_can_have_children(self, obj):
        """Check if this string can have child strings."""
        return obj.can_have_children()

    def get_suggested_child_field(self, obj):
        """Get suggested child field for creating child strings."""
        child_field = obj.suggest_child_field()
        if child_field:
            return {"id": child_field.id, "name": child_field.name, "field_level": child_field.field_level}
        return None

    def get_naming_conflicts(self, obj):
        """Get any naming conflicts for this string."""
        return obj.check_naming_conflicts()


class StringDetailSerializer(serializers.ModelSerializer):
    dimension_value_display = serializers.SerializerMethodField()
    dimension_value_label = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()
    dimension_type = serializers.SerializerMethodField()
    submission_name = serializers.SerializerMethodField()
    effective_value = serializers.SerializerMethodField()

    class Meta:
        model = models.StringDetail
        fields = [
            "id",
            "submission_name",
            "string",
            "dimension",
            "dimension_name",
            "dimension_type",
            "dimension_value",
            "dimension_value_display",
            "dimension_value_label",
            "dimension_value_freetext",
            "effective_value",
            "created",
            "last_updated",
        ]
        read_only_fields = ["created", "last_updated"]

    def get_submission_name(self, obj):
        return obj.string.submission.name if obj.string and obj.string.submission else None

    def get_dimension_name(self, obj):
        return obj.dimension.name if obj.dimension else None

    def get_dimension_type(self, obj):
        return obj.dimension.type if obj.dimension else None

    def get_dimension_value_display(self, obj):
        return obj.dimension_value.value if obj.dimension_value else None

    def get_dimension_value_label(self, obj):
        return obj.dimension_value.label if obj.dimension_value else None

    def get_effective_value(self, obj):
        """Get the effective value (either from dimension_value or freetext)."""
        return obj.get_effective_value()


class StringGenerationRequestSerializer(serializers.Serializer):
    """Serializer for string generation requests."""
    submission_id = serializers.IntegerField()
    field_id = serializers.IntegerField()
    dimension_values = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dictionary mapping dimension names to their values"
    )
    parent_string_id = serializers.IntegerField(
        required=False, allow_null=True)

    def validate_submission_id(self, value):
        """Validate that submission exists."""
        try:
            models.Submission.objects.get(id=value)
        except models.Submission.DoesNotExist:
            raise serializers.ValidationError("Submission does not exist")
        return value

    def validate_field_id(self, value):
        """Validate that field exists."""
        try:
            models.Field.objects.get(id=value)
        except models.Field.DoesNotExist:
            raise serializers.ValidationError("Field does not exist")
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        try:
            submission = models.Submission.objects.get(
                id=attrs['submission_id'])
            field = models.Field.objects.get(id=attrs['field_id'])

            # Validate rule and field belong to same platform
            if submission.rule.platform != field.platform:
                raise serializers.ValidationError(
                    "Rule and field must belong to the same platform"
                )

            # Validate dimension values
            validation_errors = StringGenerationService.validate_dimension_values(
                submission.rule, field, attrs['dimension_values']
            )
            if validation_errors:
                raise serializers.ValidationError({
                    "dimension_values": validation_errors
                })

        except models.Submission.DoesNotExist:
            raise serializers.ValidationError("Submission does not exist")
        except models.Field.DoesNotExist:
            raise serializers.ValidationError("Field does not exist")

        return attrs


class StringRegenerationSerializer(serializers.Serializer):
    """Serializer for string regeneration requests."""
    dimension_values = serializers.DictField(
        child=serializers.CharField(),
        help_text="New dimension values to use for regeneration"
    )


class StringConflictCheckSerializer(serializers.Serializer):
    """Serializer for checking naming conflicts."""
    rule_id = serializers.IntegerField()
    field_id = serializers.IntegerField()
    proposed_value = serializers.CharField()
    exclude_string_id = serializers.IntegerField(
        required=False, allow_null=True)


class StringBulkGenerationRequestSerializer(serializers.Serializer):
    """Serializer for bulk string generation."""
    submission_id = serializers.IntegerField()
    generation_requests = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of generation requests with field_id and dimension_values"
    )

    def validate_generation_requests(self, value):
        """Validate each generation request in the list."""
        for request in value:
            if 'field_id' not in request:
                raise serializers.ValidationError(
                    "Each request must have field_id")
            if 'dimension_values' not in request:
                raise serializers.ValidationError(
                    "Each request must have dimension_values")
        return value
